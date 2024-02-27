import click
import cv2
import numpy as np
import os
from datetime import datetime


import logging

# Create a custom formatter with your desired time format
time_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt=time_format)
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@click.command()
@click.option('--input_batch', prompt='input_batch', help='The scan containing a batch of photos')
@click.option('--output_dir', prompt='output_dir', help='Where to write the parsed photos', default='/tmp')
@click.option('--batch_num', prompt='batch_num', help='Batch of scanned photos')
@click.option('--num_photos', prompt='num_photos', help='How many photos to expect in a batch file', default=20)
def main(input_batch, output_dir, batch_num, num_photos):
    # write output to a certain path with a processing timestamp
    output_dir_with_runtime_info = f"{output_dir}/instax_parsing/{batch_num}/{epoch_now()}"
    os.makedirs(output_dir_with_runtime_info, exist_ok=True)
    logger.info(f'writing all files to: {output_dir_with_runtime_info}')
    input_path_as_img = normalize(input_batch)
    detect_polaroids(input_path_as_img, output_dir_with_runtime_info, batch_num, num_photos)


def epoch_now():
    current_utc_datetime = datetime.utcnow()
    formatted_utc_time = current_utc_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted_utc_time


# take an input batch and convert the file type to JPG
# TODO support more file types
def normalize(input_batch):
    input_batch_str = str(input_batch)

    if input_batch_str.endswith('.jpg') or input_batch_str.endswith('.png'):
        return input_batch_str

    raise Exception(f'file type of {input_batch_str}')


# main logic to detect photos
def detect_polaroids(image_path, output_dir, batch_num, num_photos):
    img = cv2.imread(image_path)

    # copy your scan to output dir so you know what you are parsing from
    output_base_file = os.path.join(output_dir, f"batch{batch_num}_base.jpg")
    logger.info(f'write base scan to {output_base_file}')
    cv2.imwrite(output_base_file, img)

    logger.info('Converting img to gray scale')
    # grayscale helps CV2 process image
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    logger.info('Blur the image for better edge detection')
    img_gray_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)

    logger.info('Apply thresholding to isolate white regions')
    thresh = cv2.adaptiveThreshold(img_gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

    # I picked these params after trial and error, there isn't much thought behind them
    t1, t2 = 300, 350
    logger.info('Apply canny edge detection')
    edges = cv2.Canny(image=thresh, threshold1=t1, threshold2=t2)

    logger.info('Finding contours')
    # cv2.RETR_EXTERNAL really helps find the outer edges of the photo to include white border
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # large filter here helps remove small, noisy scans
    min_contour_area = 50000
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    logger.info(f'Filtered out {len(contours) - len(filtered_contours)} contours with size less than {min_contour_area}, leaving {len(filtered_contours)} remaining')

    def calculate_centroid(contour):
        M = cv2.moments(contour)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        return np.array([cx, cy])

    def are_contours_similar(contour1, contour2, threshold_distance=500):
        centroid1 = calculate_centroid(contour1)
        centroid2 = calculate_centroid(contour2)
        distance = np.linalg.norm(centroid1 - centroid2)
        return distance < threshold_distance

    logger.info('Sort contours by area in descending order')
    filtered_contours.sort(key=cv2.contourArea, reverse=True)

    logger.info('Deduplicate contours based on similarity of centroids')
    deduplicated_contours = []
    for contour in filtered_contours:
        if not any(are_contours_similar(contour, existing_contour) for existing_contour in deduplicated_contours):
            deduplicated_contours.append(contour)

    # Take the largest N contours
    top_contours = deduplicated_contours[:num_photos]

    # Save each contour as a separate image
    for photo_num, contour in enumerate(top_contours):
        # Find the bounding box of the contour
        # bounding rect creates a perfectly square image. If your scan is rotated at all, it may produce a weird scan
        x, y, w, h = cv2.boundingRect(contour)

        # Extract the region from the original image
        contour_image = img[y:y + h, x:x + w]

        # Save the contour image to a file
        output_file = os.path.join(output_dir, f'batch{batch_num}_photo{photo_num}.jpg')
        cv2.imwrite(output_file, contour_image)

        logger.info(f'photo number:{photo_num}, batch number:{batch_num}, output file:{output_file}, img size:{contour_image.size}')

    logger.info(f'Done processing batch {batch_num}')


if __name__ == "__main__":
    main()

