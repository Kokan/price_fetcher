from argparse import ArgumentParser
from pathlib import Path

from beancount import loader


def validate_prices(prices_dir: Path) -> int:
    main_files = sorted(prices_dir.glob("*/main.beancount"))
    if not main_files:
        print(f"No yearly main.beancount files found under {prices_dir}")
        return 0

    error_count = 0
    for main_file in main_files:
        _entries, errors, _options_map = loader.load_file(str(main_file))
        if errors:
            error_count += len(errors)
            print(f"{main_file} has {len(errors)} Beancount validation error(s):")
            for error in errors:
                print(error)
        else:
            print(f"{main_file} is valid")

    return error_count


def main() -> None:
    parser = ArgumentParser(description="Validate generated Beancount price files.")
    parser.add_argument(
        "prices_dir",
        nargs="?",
        default=Path("prices"),
        type=Path,
        help="Directory containing <year>/main.beancount files",
    )
    args = parser.parse_args()

    error_count = validate_prices(args.prices_dir)
    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
