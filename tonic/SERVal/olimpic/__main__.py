import random
from argparse import ArgumentParser
from pathlib import Path
from timeit import default_timer as timer

from prettytable import PrettyTable, MARKDOWN
from tqdm import tqdm

from datasetup.olimpic import OLIMPIC_ENTRY_POINT, download_olimpic
from odtools.Download import (get_path_to_latest_version, update_models, OLA_TAG, NOTA_TAG)
from odtools.Inference.ModelWrappers import YOLODetectionModelWrapper
from .pipeline import process_single_olimpic_image
from ..utils import compute_LMX_metrics
from ...Linearization import LMXWrapper


def main():
    parser = ArgumentParser()
    parser.add_argument("-c", "--count", type=int, default=100, help="Number of images to process")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed for data shuffling")
    parser.add_argument("-v", "--verbose", action="store_true", help="Make script verbose")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Store detailed results to a CSV file")
    parser.add_argument("--raise_err", action="store_true", help="Raise exception if errors occur")
    parser.add_argument("--safe_box_off", action="store_true", help="Turns of the safe box in assembly algorithm")

    args = parser.parse_args()

    # setup models
    update_models()
    notehead_detector = YOLODetectionModelWrapper(get_path_to_latest_version(NOTA_TAG))
    staff_detector = YOLODetectionModelWrapper(get_path_to_latest_version(OLA_TAG))

    # setup dataset
    if not OLIMPIC_ENTRY_POINT.exists():
        download_olimpic()

    # load images
    images = sorted(list(OLIMPIC_ENTRY_POINT.rglob("*.png")))
    mxlms = sorted(list(OLIMPIC_ENTRY_POINT.rglob("*.musicxml")))

    if len(images) != len(mxlms):
        raise ValueError("Numbers of annotations and images do not match.")

    if args.count > len(mxlms):
        print("Warning: Number of data specified is greater than the number of data available")
        args.count = len(mxlms)

    # retrieve specified number of images
    data = list(zip(images, mxlms))
    random.Random(args.seed).shuffle(data)
    data = data[:args.count]

    # setup logs
    total_processed = 0
    total_score = [0 for _ in range(4)]
    error_log = ""
    error_count = 0
    table = PrettyTable(["ID", "standardized", "reduced", "melody", "contour"])
    table.set_style(MARKDOWN)

    start = timer()
    for image_path, mxml_path in tqdm(data, desc="Processing", disable=args.verbose):
        if args.verbose:
            print(f">>> {mxml_path}")
        try:
            gt_lmx = LMXWrapper.from_complex_musicxml_file(mxml_path)

            p_lmx = process_single_olimpic_image(
                image_path,
                staff_detector,
                notehead_detector,
                vertical_offset_factor=0 if args.safe_box_off else None,
                verbose=False,
                visualize=False
            )
            p_lmx.canonicalize()

            stand, red, mel, cont = compute_LMX_metrics(p_lmx, gt_lmx)

            table.add_row([
                image_path.stem,
                f"{stand:.4f}",
                f"{red:.4f}",
                f"{mel:.4f}",
                f"{cont:.4f}",
            ])
            if args.verbose:
                print(f"Score: {stand}")

            total_processed += 1
            total_score[0] += stand
            total_score[1] += red
            total_score[2] += mel
            total_score[3] += cont

        except Exception as e:
            if args.raise_err:
                raise e

            error_log += f"{mxml_path}: {e}\n"
            error_count += 1
            print(f"{mxml_path}: {e}")

        if args.verbose:
            print()

    time_elapsed = timer() - start

    if args.output:
        args.output.mkdir(exist_ok=True, parents=True)
        with open(args.output) as file:
            file.write(table.to_csv(index=False))

    print(f"Error log:\n{error_log}")
    print()
    print(f"Processed: {total_processed}")
    print(f"Errors: {error_count}")
    print()
    print(f"Scores:")
    print(f">>> Standardized: {total_score[0] / total_processed:.4f}")
    print(f">>> Reduced: {total_score[1] / total_processed:.4f}")
    print(f">>> Melody: {total_score[2] / total_processed:.4f}")
    print(f">>> Contour: {total_score[3] / total_processed:.4f}")
    print()
    print("Time elapsed:", time_elapsed)


if __name__ == "__main__":
    main()
