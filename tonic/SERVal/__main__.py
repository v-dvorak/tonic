from argparse import ArgumentParser
from pathlib import Path

from prettytable import PrettyTable, MARKDOWN
from tqdm.contrib import tzip
from .utils import compute_LMX_metrics
from ..Linearization import LMXWrapper


def main():
    parser = ArgumentParser()

    parser.add_argument("predicted", type=Path, help="Predicted MusicXML file or directory")
    parser.add_argument("ground_truth", type=Path, help="Ground truth MusicXML file or directory")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Store detailed results to a CSV file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Make script verbose")
    parser.add_argument("--raise_err", action="store_true", help="Raise exception if errors occur")
    parser.add_argument("--index_id", action="store_true", help="Outputs data IDs indexes instead of file names")

    args = parser.parse_args()

    if args.predicted.is_dir():
        predicted = sorted(list(args.predicted.glob("*.musicxml")))
    else:
        predicted = [args.predicted]
    if args.ground_truth.is_dir():
        ground_truth = sorted(list(args.ground_truth.glob("*.musicxml")))
    else:
        ground_truth = [args.ground_truth]

    if len(predicted) != len(ground_truth):
        raise ValueError("Number of predicted and ground truth files must match")

    # SETUP TABLE
    table = PrettyTable(["ID", "standardized", "reduced", "melody", "contour"])
    table.set_style(MARKDOWN)
    table.align = "r"

    total_processed = 0
    scores = [0 for _ in range(4)]

    for image_index, (pr_file, gt_file) in enumerate(tzip(predicted, ground_truth, disable=args.verbose)):
        if args.verbose:
            print(f"{image_index}) Validating ground truth: {gt_file.name}")
            print(f"vs predicted: {pr_file.name}")

        if args.index_id:
            image_id = image_index
        else:
            image_id = gt_file.stem
        try:
            p_lmx = LMXWrapper.from_musicxml_file(pr_file)
            gt_lmx = LMXWrapper.from_complex_musicxml_file(gt_file)

            stand, red, mel, cont = compute_LMX_metrics(p_lmx, gt_lmx)

            table.add_row([
                image_id,
                f"{stand:.4f}",
                f"{red:.4f}",
                f"{mel:.4f}",
                f"{cont:.4f}",
            ])

            for i, value in enumerate([stand, red, mel, cont]):
                scores[i] += value

            total_processed += 1
        except Exception as e:
            if args.raise_err:
                raise e

            table.add_row([image_id, "err", "err", "err", "err"])
            if args.verbose:
                print(e)

        if args.verbose:
            print()

    if total_processed > 0:
        table.add_row(["avg", *[f"{value / total_processed :.4f}" for value in scores]])
    else:
        table.add_row(["avg", "err", "err", "err", "err"])

    if args.output:
        args.output.parents[0].mkdir(exist_ok=True, parents=True)
        with open(args.output, "w") as file:
            file.write(table.get_csv_string())

    if args.verbose:
        print(table)


if __name__ == "__main__":
    main()
