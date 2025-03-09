from argparse import ArgumentParser
from pathlib import Path

from prettytable import PrettyTable, MARKDOWN

from ..Linearization import LMXWrapper, complex_musicxml_file_to_lmx


def main():
    parser = ArgumentParser()

    parser.add_argument("predicted", type=Path, help="Predicted file or directory")
    parser.add_argument("ground_truth", type=Path, help="Ground truth file or directory")

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
    table = PrettyTable(["ID", "SER"])
    table.set_style(MARKDOWN)
    table.align = "r"

    for i, (pr, gt) in enumerate(zip(predicted, ground_truth)):
        print(f"Validating ground truth: {gt.name}")
        print(f"vs predicted: {pr.name}")
        try:
            p_lmx = LMXWrapper.from_musicxml_file(pr)
            gt_lmx = complex_musicxml_file_to_lmx(gt)
            ser = LMXWrapper.normalized_levenstein_distance(p_lmx, gt_lmx)
            print(ser)
            table.add_row([i, f"{ser:.4f}"])
        except Exception as e:
            table.add_row([i, "err"])
            print(e)
        print()

    print(table)


if __name__ == "__main__":
    main()
