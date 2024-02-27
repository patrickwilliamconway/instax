# Instax Photo Parsing Tool

This Python script is designed to parse scanned Instax photos from a batch scan, detect individual Polaroid-like images, and save them separately.

Below is a breakdown of its functionality and usage.

## Features

- **Batch Processing**: Parses a batch of scanned photos in one go.
- **Instant-Film Photo Detection**: Detects individual Polaroid-like images within the batch scan.
- **Contour Deduplication**: Removes duplicate contours based on the similarity of centroids.
- **Output Organization**: Saves each detected photo as a separate image file.

## Requirements

To run the script, you need:

- Python 3.x
- OpenCV (`cv2`)
- NumPy
- Click

## Usage
Run the script with the following command:

```shell
python process_scan.py --input_batch <input_batch> --output_dir <output_dir> --batch_num <batch_num> --num_photos <num_photos>
```

- `<input_batch>`: Provide the input batch scan path using the `--input_batch` option.
- `<output_dir>`: Specify the output directory where parsed photos will be saved using the `--output_dir` option. Default is `/tmp`.
- `<batch_num>`: Specify the batch number (`--batch_num`) and the expected number of photos in the batch.
- `<num_photos>`: The program will select (`--num_photos`) contours from the scan. Default is `20`.

### Example
I've included a demo scan. You can test the program out with the following:

```shell
cd scripts/scan;
python process_scan.py --input_batch demo/demo_scan.jpg --output_dir scripts/scan/demo --batch_num 0 --num_photos 20
```

### Additional Notes

- Ensure the scanned images are of sufficient quality for accurate detection
- This performs best when there are large, dark gaps between the photos
- Adjust threshold values and contour area criteria as needed for different scans
