from typing import List
from argparse import ArgumentParser


def parse_arguments(args: List[str]):
    """
    Reads Kattis login details from command line input.

    Parameters:
    - args: sys.argv[1:]

    Returns:
    - List[str]: [user, password]
    """
    parser = ArgumentParser()
    parser.add_argument('-u', '--user', type=str, help='Kattis username or email')
    parser.add_argument('-p', '--password', type=str, help='Kattis password')
    return parser.parse_args(args)
