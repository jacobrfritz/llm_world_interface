# src/llm_world_interface/cli.py
import argparse
import sys

from .main import run


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Llm World Interface CLI")
    return parser.parse_args(args)


def main() -> None:
    _ = parse_args(sys.argv[1:])
    run()


if __name__ == "__main__":
    main()
