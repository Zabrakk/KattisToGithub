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
    parser.add_argument('--no-git', required=False, default=False, action='store_true', help='If this argument is given, Git add and commit will not be used on any files')
    parser.add_argument('--py-main-only', required=False, default=False, action='store_true', help='If this argument is given, KTG only downloads Python 3 files that include the substring "def main()"')
    return parser.parse_args(args)
