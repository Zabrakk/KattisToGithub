from typing import List
from argparse import ArgumentParser


def parse_arguments(args: List[str]):
    """
    Reads Kattis login details and target directory from command line input.

    Parameters:
    - args: sys.argv[1:]

    Returns:
    - List[str]: [user, password, directory]
    """
    parser = ArgumentParser()
    parser.add_argument('-u', '--user', type=str, required=True, help='Kattis username or email')
    parser.add_argument('-p', '--password', type=str, required=True, help='Kattis password')
    parser.add_argument('-d', '--directory', type=str, required=True, help='Directory to which Kattis solution are downloaded to')
    return parser.parse_args(args)
