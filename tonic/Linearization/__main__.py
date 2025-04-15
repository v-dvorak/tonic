from argparse import ArgumentParser
from pathlib import Path

from . import LMXWrapper


def main():
    parser = ArgumentParser()

    subparsers = parser.add_subparsers(dest="command", help="Jobs")

    simp_parser = subparsers.add_parser("simplify")
    simp_parser.add_argument("input", help="Path to input file")
    simp_parser.add_argument("-o", "--output", help="Path to output file")

    prev_parser = subparsers.add_parser("preview")
    prev_parser.add_argument("input", help="Path to input file")

    args = parser.parse_args()

    if args.command == "simplify":
        input_file = Path(args.input)
        if args.output is None:
            output_file = input_file.parent / (input_file.stem + "_simple" + input_file.suffix)
        else:
            output_file = Path(args.output)

        LMXWrapper.simplify_musicxml_file(input_file, output_file)
        print(f"Saved at: {output_file.absolute()}")
        return 0

    elif args.command == "preview":
        with open(args.input, "r") as f:
            read_lmx = LMXWrapper(f.read().split())

        print(read_lmx.to_human_readable())
        print()
        print(read_lmx.to_melody())
        print()
        print(read_lmx.to_contour())
        return 0
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
