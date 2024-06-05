import click
import piexif
import os
from PIL import Image
from geopy.geocoders import Nominatim
import json
from datetime import datetime
import re
import logging

# Create a custom formatter with your desired time format
time_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt=time_format)
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DEFAULT_PHOTO_REGEX = 'batch[0-9]+.*_photo[0-9]+.*'


@click.command()
@click.option(
    '--input_dir',
    prompt='location of input files',
    help='where to read .jpg files from'
)
@click.option(
    '--start_offset',
    default=0,
    help='which number photo should to start processing from'
)
@click.option(
    '--photo_regex',
    default=DEFAULT_PHOTO_REGEX,
    help='regex to match files against. If you are using process_scan.py, use default.'
)
def main(input_dir, start_offset, photo_regex):
    photos = get_photos(input_dir, photo_regex)
    for photo_index in range(start_offset, len(photos)):
        file_name = photos[photo_index]
        parse_photo(file_name, input_dir)


def get_from_config_file(field=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = 'script_secrets.json'
    config_path = os.path.join(script_dir, config_file)
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            if field:
                return data[field]
            else:
                return data
    except FileNotFoundError:
        logger.warning('no script_secrets.json config file found, loading empty map')
        return {}


common_locations = get_from_config_file("common_locations")


# Given an input directory, find all files that match a regex (batchX_photoY) and return them in ascending order
# relative to Y.
def get_photos(input_dir, photo_regex):
    photos_locations = [f for f in os.listdir(input_dir) if re.match(fr'{photo_regex}', f)]

    # turns 'batch1_photo17.jpeg` into 17
    def file_to_number(f):
        jpg = '.jpg'
        jpeg = '.jpeg'
        to_remove = len(jpg) if f.endswith(jpg) else len(jpeg)
        return int(f.split('_')[1][5:][:-to_remove])

    if photo_regex == DEFAULT_PHOTO_REGEX:
        return sorted(photos_locations, key=file_to_number)
    else:
        return sorted(photos_locations)


# main logic of program
def parse_photo(file, input_dir):
    file_full_path_in = f'{input_dir}/{file}'
    logger.info(f'processing: {file_full_path_in}')

    logger.info('load image data')
    # open photo with default OS's photo viewer (ex: Preview on MacOS)
    img = Image.open(file_full_path_in)
    # title doesn't seem to actually work...
    img.show(title=file)

    current_exif_data = piexif.load(file_full_path_in)
    should_update = True
    if current_exif_data['GPS']:
        # give option to skip if you already have GPS data
        should_update = y_n(f'found GPS data, still want to update metadata for {file}?')

    if not should_update:
        logger.info(f'skipping {file}')
    else:
        # manually enter data
        location_data = location(file)
        date_data = date(file)
        caption_data = annotation(file)

        new_metadata = {
            'GPS': location_data,
            'Exif': date_data,
            '0th': caption_data,
        }

        update_exif_metadata(file_full_path_in, new_metadata)

    img.close()


def y_n(caption, default='y'):
    return click.prompt(
        text=caption,
        default=default,
        type=click.Choice(['y', 'n']),
        show_choices=False,
        show_default=True,
        value_proc=lambda ans: ans == 'y',
    )


# Update metadata on existing file. Will OVERWRITE the existing GPS, Exif, 0th fields but leave all others the same.
def update_exif_metadata(file_path, new_metadata):
    file = os.path.basename(file_path)
    logger.info(f'Reading the existing metadata from the image {file}')
    try:
        exif_data = piexif.load(file_path)
    except Exception as e:
        logger.error(f"Error loading exif data for {file}: {e}")
        return False

    logger.info(f'Modify the existing metadata of {file} with new values {new_metadata}')
    exif_data.update(new_metadata)

    try:
        exif_bytes = piexif.dump(new_metadata)
        piexif.insert(exif_bytes, file_path)
        logger.info(f"Metadata updated successfully for {file}")
    except Exception as e:
        logger.error(f"Error updating metadata for {file}: {e}")


# add a description of the photo
def annotation(file):
    logger.info(f"\n{color('CAPTION SECTION', GREEN)} for {file}")
    while True:
        caption = click.prompt(text='Copy caption')
        data = {
            piexif.ImageIFD.ImageDescription: caption
        }

        input_ok = y_n(f"Confirm Annotation: {color(caption, BLUE)}")

        if input_ok:
            return data


times_of_day = {
    "m": 9,   # morning
    "a": 13,  # afternoon
    "e": 20,  # evening
}

date_cache = {}


# add date metadata to JPGs
def date(file):
    logger.info(f"\n{color('DATE SECTION', GREEN)} for {file}")
    while True:
        sorted_cache = json.dumps(dict(sorted(date_cache.items(), key=lambda item: item[1])), indent=1)
        existing_date = click.prompt(
            text=f'use existing date? {sorted_cache}',
            value_proc=lambda s: date_cache.get(s, False),
            default='n',
        )
        if not existing_date:
            month_input = click.prompt(
                text='month',
                value_proc=lambda s: int(s),
                type=click.Choice(range(1, 13)),
                show_choices=False,
            )
            # this won't catch invalid inputs like Feb 30
            day_input = click.prompt(
                text='day',
                value_proc=lambda s: int(s),
                type=click.Choice(range(1, 32)),
                show_choices=False,
            )
            # assuming all photos are from 2000s
            year_input = click.prompt(
                text='year',
                value_proc=lambda s: 2000 + int(s),
                show_choices=False,
            )
            time_of_day = click.prompt(
                text=f'time of day: {json.dumps(times_of_day, indent=1)}',
                type=click.Choice(list(times_of_day.keys())),
                show_choices=False,
                default='e',
                value_proc=lambda s: times_of_day[s],
            )
            input_date = datetime(year_input, month_input, day_input, time_of_day, 0, 0)
            date_string = input_date.strftime("%Y:%m:%d %H:%M:%S")
        else:
            date_string = existing_date

        data = {
            piexif.ExifIFD.DateTimeOriginal: date_string,
            piexif.ExifIFD.DateTimeDigitized: date_string,
        }

        input_ok = y_n(f'Confirm Date - {color(date_string, BLUE)}: ')

        if input_ok:
            if date_string not in date_cache.values():
                # save date entries in cache for faster repeat inputs
                new_idx = str(len(date_cache))
                date_cache[new_idx] = date_string
            return data


geo_cache = {}


# Determine if input was a cache entry (indexed by number) or new location
def process_input_location(prompt_input):
    str_input = str(prompt_input)
    if str_input.isdigit() and str_input in common_locations:
        return common_locations[str_input]
    else:
        return str_input


# Query GeoPy for location
# Program maintains an in memory cache of previous locations.
# (GeoPy can take a bit to respond with NYC addresses for some reason?)
def geo_query(prompt_input):
    if prompt_input in geo_cache:
        logger.info(f'cache hit for {prompt_input}')
        return geo_cache[prompt_input]
    else:
        try:
            geolocator = Nominatim(user_agent="pwc")
            logger.info(f'querying geolocator for {prompt_input}')
            geo = geolocator.geocode(query=prompt_input, timeout=10)
            if geo is None:
                raise Exception(f'Location returned None from geolocator')
            # store previous prompt and data in cache
            geo_cache[prompt_input] = geo
            return geo
        except Exception as e:
            logger.error(f"Error trying to get location data for {prompt_input}: {e}")


# this was taken directly from ChatGPT
def geotagging_to_exif(lat, long):
    lat_ref = 'N' if lat >= 0 else 'S'
    lon_ref = 'E' if long >= 0 else 'W'
    latitude = abs(lat)
    longitude = abs(long)
    lat_deg = int(latitude)
    lat_min = int((latitude - lat_deg) * 60)
    lat_sec = int((latitude - lat_deg - lat_min / 60) * 3600 * 1000)
    lon_deg = int(longitude)
    lon_min = int((longitude - lon_deg) * 60)
    lon_sec = int((longitude - lon_deg - lon_min / 60) * 3600 * 1000)

    data = {
        piexif.GPSIFD.GPSLatitudeRef: lat_ref,
        piexif.GPSIFD.GPSLatitude: ((lat_deg, 1), (lat_min, 1), (lat_sec, 1000)),
        piexif.GPSIFD.GPSLongitudeRef: lon_ref,
        piexif.GPSIFD.GPSLongitude: ((lon_deg, 1), (lon_min, 1), (lon_sec, 1000)),
    }

    return data


# given a prompt input, return EXIF data
def input_to_location(prompt_input):
    geolocation = geo_query(prompt_input)
    logger.info(f'Based on input: {color(prompt_input, CYAN)}, found: {color(geolocation, BLUE)}')
    if geolocation:
        return geotagging_to_exif(geolocation.latitude, geolocation.longitude)


# wraps all logic to process the location of the photo
def location(file):
    logger.info(f"\n{color('LOCATION SECTION', GREEN)} for {file}")

    while True:
        loc_str = [f'{idx}: {loc}' for idx, loc in common_locations.items()]
        location_prompt = f'Choose index from common_locations: {json.dumps(loc_str, indent=1)}. Or, input a location'
        prompt_input = click.prompt(
            text=location_prompt,
            type=click.Choice(list(common_locations.keys())),
            show_choices=False,
            value_proc=process_input_location
        )

        data = input_to_location(prompt_input)

        input_ok = y_n('Confirm location')

        if input_ok:
            if prompt_input not in common_locations.values():
                new_loc_idx = str(len(common_locations))
                common_locations[new_loc_idx] = prompt_input

            return data


RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"


# return text to STDOUT in a color
def color(text, c):
    return f"{c}{text}{RESET}"


if __name__ == '__main__':
    main()
