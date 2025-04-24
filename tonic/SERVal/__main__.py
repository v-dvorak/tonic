from argparse import ArgumentParser
from pathlib import Path

from prettytable import PrettyTable, MARKDOWN

from .utils import compute_LMX_metrics
from ..Linearization import LMXWrapper


def main():
    parser = ArgumentParser()

    parser.add_argument("predicted", type=Path, help="Predicted MusicXML file or directory")
    parser.add_argument("ground_truth", type=Path, help="Ground truth MusicXML file or directory")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Store detailed results to a CSV file")
    parser.add_argument("--raise_err", action="store_true", help="Raise exception if errors occur")

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

    for i, (pr, gt) in enumerate(zip(predicted, ground_truth)):
        print(f"{i}) Validating ground truth: {gt.name}")
        print(f"vs predicted: {pr.name}")
        try:
            p_lmx = LMXWrapper.from_musicxml_file(pr)
            gt_lmx = LMXWrapper.from_complex_musicxml_file(gt)

            stand, red, mel, cont = compute_LMX_metrics(p_lmx, gt_lmx)

            table.add_row([
                i,
                f"{stand:.4f}",
                f"{red:.4f}",
                f"{mel:.4f}",
                f"{cont:.4f}",
            ])
        except Exception as e:
            if args.raise_err:
                raise e

            table.add_row([i, "err", "err", "err", "err"])
            print(e)
        print()

    if args.output:
        args.output.mkdir(exist_ok=True, parents=True)
        with open(args.output) as file:
            file.write(table.to_csv(index=False))

    print(table)


if __name__ == "__main__":
    main()
