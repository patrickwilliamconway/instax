# Image Metadata Editor

This Python script allows you to modify metadata in JPEG images. You can update GPS coordinates, date and time information, and add annotations to your photos.

## Features

### Update GPS coordinates based on location input

You can specify a file `scripts/photo/script_secret.json` and add a field `common_locations` like this
```json
{
    "common_locations": {
        "0": "123 Main St New York, NY",
        "1": "1600 Pennsylvania Ave",
        "2": "Statue of Liberty, NY"
    }
}
```
so that when you are prompted for locations, you have frequent ones available. 

`GeoPy` is great - it is very flexible with what inputs it accepts. For example:
```shell
2024-02-26 21:55:09 - INFO - Based on input: the white house, found: White House, 1600, Pennsylvania Avenue 
Northwest, Ward 2, Washington, District of Columbia, 20500, United States
```

### Modify date and time metadata
You'll input: Day, Month, Year, Time of Day (morning, afternoon, evening). 

### Add custom annotations to photos
This doesn't work as well as I had hoped. It saves the annotation as part of the file, but applications like Apple 
Photos and Google Photos don't use them as the "description" fields. Oh well.


## Usage
Run the script with the following command:

```shell
python process_photo.py --input_dir <input_dir> --start_offset <start_offset>
```
   
   - `<input_dir>`: Path to the directory containing the JPEG files you want to process.
   - `<start_offset>`: Optional. Specifies the index of the photo to start processing from. Default is 0.
   - `<photo_regex>`: Optional. Specifies the index of the photo to start processing from. Default is matches scan10_photo1

Follow the prompts to update metadata for each photo.

### Example
I've included a demo photo that you can use to test out the program. Run it with:

```shell
cd scripts/photo;
python process_photo.py --input_dir demo/
```

![Example Usage of the Script](example_process_photo.png "Example Usage")

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Click](https://click.palletsprojects.com/en/8.0.x/): Command line interface creation kit.
- [piexif](https://piexif.readthedocs.io/en/latest/): Python library to simplify working with EXIF data in JPEG files.
- [Pillow](https://python-pillow.org/): Python Imaging Library fork.
- [geopy](https://geopy.readthedocs.io/en/stable/): Geocoding library for Python.