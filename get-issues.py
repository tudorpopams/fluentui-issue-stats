import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import requests
import json

load_dotenv()


def fetch_issues(repo, token):
    issues = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{repo}/issues?state=all&page={page}&per_page=100&labels=Fluent UI react-components (v9)"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Error fetching issues: {response.status_code}")

        page_issues = response.json()

        if not page_issues:
            break

        print(f"Fetched page {page}")

        issues.extend(page_issues)
        page += 1

    return issues


def main():
    repo = "microsoft/fluentui"
    token = os.environ["GITHUB_TOKEN"]
    data_folder = f"data/{sys.argv[1]}"
    Path(data_folder).mkdir(parents=True, exist_ok=True)

    issues = fetch_issues(repo, token)

    with open(f"{data_folder}/issues.json", "w") as f:
        json.dump(issues, f, indent=4)


if __name__ == "__main__":
    main()
