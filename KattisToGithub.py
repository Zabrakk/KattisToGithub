import os
import sys
import csv
import requests
import subprocess
from pathlib import Path
from functools import cached_property
from typing import List, Dict, Generator
from bs4 import BeautifulSoup as Soup
from src.constants import *
from src.argument_parser import parse_arguments
from src.solved_problem import SolvedProblem, ProblemStatus


class KattisToGithub:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.base_url = BASE_URL
        self.login_url = LOGIN_URL
        self.solved_problems: List[SolvedProblem] = []

    def get_run_details_from_sys_argv(self) -> None:
        """
        Uses src/argument_parser to extract the Kattis login details from command line input.
        Stores these values to self.user and self.password respectively.
        """
        parser = parse_arguments(sys.argv[1:])
        self.user = parser.user
        self.password = parser.password
        self.directory = Path(__file__).parent / parser.directory

    def create_folders_for_solutions(self) -> None:
        """
        Creates a folder called Solutions. The code's of solved problems will be stored there
        """
        if not os.path.exists(self.directory / 'Solutions'):
            print(f'#: Creating folder for problem solutions')
            os.mkdir(self.directory / 'Solutions')

    def load_solved_problem_status_csv(self) -> None:
        if os.path.exists(self.directory / 'status.csv'):
            with open(self.directory / 'status.csv', 'r') as csv_file:
                try:
                    reader = csv.DictReader(csv_file, fieldnames=CSV_FIELD_NAMES)
                    reader.__next__()
                    for row in reader:
                        self.solved_problems += [self._load_solved_problem_from_csv_row(row)]
                except StopIteration:
                    print(f'#: Status.csv was empty')

    def _load_solved_problem_from_csv_row(self, row: Dict) -> SolvedProblem:
        filename_language_dict = {}
        if len(row['Solutions']) > 0:
            for entry in row['Solutions'].split('#'):
                language, filename = entry.split('|')
                filename_language_dict[filename] = language
        return SolvedProblem(
            name=row['Name'],
            difficulty=row['Difficulty'],
            status=ProblemStatus(int(row['Status'])),
            problem_link=row['ProblemLink'],
            submissions_link=row['SubmissionsLink'],
            filename_language_dict=filename_language_dict
        )

    @property
    def login_payload(self) -> Dict:
        return {
            'csrf_token': self._get_CSRF_token(),
            'user': self.user,
            'password': self.password
        }

    @cached_property
    def _solved_problems_url(self) -> str:
        return f'{self.base_url}/users/{self.user}'

    @cached_property
    def _solved_problem_submission_url(self) -> str:
        return f'{self._solved_problems_url}?tab=submissions&problem='

    @cached_property
    def _solved_problem_links(self) -> str:
        return [problem.submissions_link for problem in self.solved_problems]

    def _get_CSRF_token(self) -> str:
        """
        Obtains the sessions CSRF token from the login page.

        Returns:
        - str: CSRF token
        """
        response = self.session.get(self.login_url)
        if response.status_code != 200:
            print('#: GETin the login page failed')
            return
        soup = Soup(response.text, 'html.parser')
        return soup.find('input', {'name': 'csrf_token'}).get('value')

    def login(self) -> bool:
        """
        Logs into Kattis with the given credentials.

        Returns:
        - bool: True if successfully logged in; False otherwise
        """
        print('#: Attempting to login')
        response = self.session.post(self.login_url, data=self.login_payload, timeout=30)
        if response.status_code != 200:
            print('#: Something went wrong during login')
            return False
        if response.url == self.login_url:
            print(f'#: Login failed')
            return False
        else:
            print('#: Logged in to Kattis')
            return True

    def _get_html(self, url: str) -> Soup:
        response = self.session.get(url)
        return Soup(response.text, 'html.parser')

    def get_solved_problems(self) -> None:
        html = self._get_html(self._solved_problems_url)
        pages = ['']
        for page in pages:
            print(f'#: Collecting solved problems from {self._solved_problems_url + page}')
            html = self._get_html(self._solved_problems_url + page)
            for tr in html.find('div', attrs={'id': 'problems-tab'}).find('tbody').find_all('tr'):
                sp = self._parse_solved_problem(tr)
                if sp.submissions_link not in self._solved_problem_links:
                    self.solved_problems += [sp]
            self._get_links_to_next_pages(html, pages)
        print(f'#: Found a total of {len(self.solved_problems)} solved problems')

    def _get_links_to_next_pages(self, html: Soup, pages: List[str]) -> None:
        """
        Looks for the numbered next page buttons and obtains the query strings from them.

        Parameters:
        - html: BeautifulSoup object created from a HTTP request response.
        - pages: List of query params leading to further pages. The lists contents is updated inside this function.
        """
        next_pages = [href.attrs['href'] for href in html.find_all('a', href=True, attrs={'role': 'button'}) if '?page=' in href.attrs['href']]
        for next_page in next_pages:
            if next_page not in pages and next_page != '?page=1':
                pages += [next_page]

    def _parse_solved_problem(self, html) -> SolvedProblem:
        """
        Creates a SolvedProblem object based on given data

        Parameters:
        - html: BeautifulSoup object created from a HTTP request response.

        Returns:
        - SolvedProblem
        """
        problem_link = html.contents[0].find('a')['href']
        return SolvedProblem(
            problem_link=BASE_URL + problem_link,
            submissions_link = self._solved_problem_submission_url + problem_link.replace('/problems/', ''),
            name = html.contents[0].text,
            points = html.contents[4].find('span').text,
            difficulty = html.contents[4].find('span').attrs['class'][-1].split('_')[1].capitalize()
        )

    def get_codes_for_solved_problems(self) -> None:
        print('#: Starting to fetch codes for solved problems')
        i = 0
        for solved_problem in self.solved_problems:
            if not self._should_look_for_code(solved_problem):
                continue
            solved_problem_html = self._get_html(solved_problem.submissions_link)
            for link, language in self._get_submission_link_and_language(solved_problem_html):
                if language not in solved_problem.filename_language_dict.values():
                    submission_html = self._get_html(link)
                    self._parse_submission(solved_problem, submission_html, language)
                else:
                    print(f'{language} solution already found for {solved_problem.name}')
            #for submission_html in self._get_submission_html(solved_problem_html):
            #    self._parse_submission(solved_problem, submission_html)
            i += 1
            if i > 10:
                break

    def _should_look_for_code(self, solved_problem: SolvedProblem) -> bool:
        return solved_problem.status != 1

    def _get_submission_link_and_language(self, html: Soup) -> Generator[Soup, str, None]:
        for tr in html.find('div', attrs={'id': 'submissions-tab'}).find('tbody').find_all('tr'):
            if tr.find('div', {'class': 'status is-status-accepted'}):
                submission_link = self.base_url + tr.contents[-1].find('a', href=True).attrs['href']
                programming_language = tr.find('td', attrs={'data-type': 'lang'}).text
                yield submission_link, programming_language

    def _get_used_programming_languages(self, solved_problem_html):
        return [td.text for td in solved_problem_html.find_all('td', attrs={'data-type': 'lang'})]

    def _get_submission_html(self, html: Soup) -> Generator[Soup, None, None]:
        for tr in html.find('div', attrs={'id': 'submissions-tab'}).find('tbody').find_all('tr'):
            if tr.find('div', {'class': 'status is-status-accepted'}):
                submission_link = self.base_url + tr.contents[-1].find('a', href=True).attrs['href']
                yield self._get_html(submission_link)

    def _parse_submission(self, solved_problem: SolvedProblem, html: Soup, language: str) -> None:
        filename = html.find('span', attrs={'class': 'mt-2'}).code.text
        if filename in solved_problem.filename_code_dict:
            print(f'#: Not getting older solution for {filename}')
            return
        code = html.find(name='div', attrs={'class': 'source-highlight w-full'}).text
        if language == 'Python 3' and 'def main():' in code:
            print(f'#: Getting code for {solved_problem.name}')
            solved_problem.filename_code_dict[filename] = code
            solved_problem.filename_language_dict[filename] = language
            solved_problem.status = ProblemStatus.CODE_FOUND
            solved_problem.write_to_file(self.directory)
        else:
            solved_problem.status = ProblemStatus.CODE_NOT_FOUND

    def git_commit_solutions(self) -> None:
        solutions_to_commit = [solved_problem for solved_problem in self.solved_problems if len(solved_problem.filename_code_dict) > 0]
        if len(solutions_to_commit) > 5:
            for solved_problem in solutions_to_commit:
                for filename in solved_problem.filename_code_dict:
                    print(['git', 'add', f'{filename}'])
            print(['git', 'commit', f'-m Added new solutions'])
        else:
            for solved_problem in solutions_to_commit:
                for filename in solved_problem.filename_code_dict:
                    print(['git', 'add', f'{filename}'])
                    print(['git', 'commit', f'-m Solution for {solved_problem.name}'])
                    #subprocess.Popen(['git', 'add', f'{filename}'], cwd=d, stdout=subprocess.DEVNULL).wait()
                    #subprocess.Popen(['git', 'commit', f'-m Solution for {solved_problem.name}'], cwd=d, stdout=subprocess.DEVNULL).wait()

    def create_markdown_table(self):
        if os.path.exists(self.directory / 'README.md'):
            with open(self.directory / 'README.md', 'r') as md:
                original_md_content = md.readlines()
            try:
                new_md_content = original_md_content[:original_md_content.index('## Solved Problems\n')]
            except ValueError:
                new_md_content = original_md_content + ['\n']

        new_md_content += ['## Solved Problems\n']
        new_md_content += ['<sub><i>Created with [KattisToGithub](https://github.com/Zabrakk/KattisToGithub)</i></sub>\n']
        new_md_content += ['|Problem|Difficulty|Solutions|\n']
        new_md_content += ['|:-|:-|:-|\n']

        for solved_problem in sorted(self.solved_problems, key=lambda x: ['Hard', 'Medium', 'Easy'].index(x.difficulty)):
            if solved_problem.status != ProblemStatus.CODE_NOT_FOUND:
                solutions = ' '.join([
                    f'[{language}](Solutions/{filename})' for filename, language in solved_problem.filename_language_dict.items()
                ])
                new_md_content += [f'|[{solved_problem.name}]({solved_problem.problem_link})|{solved_problem.difficulty}|{solutions}|\n']

        with open(self.directory / 'README.md', 'w') as md:
            md.writelines(new_md_content)

        if new_md_content != original_md_content:
            print('#: Commiting new version of README.md')
            print(['git', 'add', f'README.md'])
            print(['git', 'commit', f'-m Updated README.md'])

    def update_status_to_csv(self) -> None:
        with open(self.directory / 'status.csv', 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELD_NAMES)
            writer.writeheader()
            for solved_problem in self.solved_problems:
                writer.writerow(solved_problem.to_dict())


if __name__ == '__main__':
    KTG = KattisToGithub()
    KTG.get_run_details_from_sys_argv()
    KTG.create_folders_for_solutions()
    KTG.load_solved_problem_status_csv()
    if KTG.login():
        KTG.get_solved_problems()
        KTG.get_codes_for_solved_problems()
        KTG.git_commit_solutions()
        KTG.create_markdown_table()
        KTG.update_status_to_csv()
