import json
import os
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv
from alive_progress import alive_bar

load_dotenv()

label_v9 = "Fluent UI react-components (v9)"
label_epic = "Type: Epic"
label_feature = "Type: Feature"
label_bug = "Type: Bug :bug:"
label_needs_backlog_grooming = "Needs: Backlog review"
label_a11y = "Area: Accessibility"
label_soft_close = "Resolution: Soft Close"
label_parter_ask = "Partner Ask"
label_needs_triage = "Needs: Triage :mag:"

token = os.environ["GITHUB_TOKEN"]
repo = "microsoft/fluentui"


def run_query(query):
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': f'bearer {token}'}
    response = requests.post(url, json={'query': query}, headers=headers)
    response.raise_for_status()

    return response.json()


def generate_graphql_query(repo, date_interval, after_query):
    return f"""
    {{
      search(query: "repo:{repo} is:issue created:{date_interval} updated:{date_interval} label:\\"{label_v9}\\"", type: ISSUE, first: 100, {after_query}) {{
        pageInfo {{
          endCursor
          hasNextPage
        }}
        edges {{
          node {{
            ... on Issue {{
              title
              number
              createdAt
              closedAt
              state
              labels(first: 100) {{
                nodes {{
                  name
                }}
              }}
              timelineItems(first: 100, itemTypes: [LABELED_EVENT, UNLABELED_EVENT]) {{
                nodes {{
                  __typename
                  ... on LabeledEvent {{
                    createdAt
                    label {{
                      name
                    }}
                  }}
                  ... on UnlabeledEvent {{
                    createdAt
                    label {{
                      name
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """


def fetch_all_issues():
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=365)

    current_date_fmt = current_date.strftime('%Y-%m')
    one_year_ago_fmt = one_year_ago.strftime('%Y-%m')

    date_interval = f"{one_year_ago_fmt}..{current_date_fmt}"

    issues = []
    has_next_page = True
    end_cursor = None

    after_query = ''

    with alive_bar(0, title="Fetching issues", unit=" pages") as bar:
        while has_next_page:
            query = generate_graphql_query(repo, date_interval, after_query)
            result = run_query(query)

            issues.extend([edge['node']
                          for edge in result['data']['search']['edges']])

            page_info = result['data']['search']['pageInfo']

            has_next_page = page_info['hasNextPage']

            if has_next_page:
                end_cursor = f'"{page_info["endCursor"]}"'
                after_query = 'after: ' + end_cursor

            bar()

    return issues


def get_issues(from_file=False):
    issues = []

    if from_file:
        data_folder = "data/issues.json"

        with open(data_folder, "r") as json_file:
            issues = json.load(json_file)
    else:
        issues = fetch_all_issues()
        data_folder = "data/issues.json"

        with open(data_folder, "w") as json_file:
            json.dump(issues, json_file, indent=2)

    return issues


def normalize_issues(issues):
    normalized_issues = []

    for issue in issues:
        labels = set([label['name'] for label in issue['labels']['nodes']])
        timeline_items = []

        if 'timelineItems' in issue:
            for timeline_item in issue['timelineItems']['nodes']:
                formatted_item = {
                    "type": timeline_item["__typename"],
                    "createdAt": datetime.strptime(timeline_item["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
                }

                if 'label' in timeline_item:
                    formatted_item["label"] = timeline_item["label"]["name"]

                timeline_items.append(formatted_item)

        normalized_issue = {
            'title': issue['title'],
            'number': issue['number'],
            'createdAt': issue['createdAt'],
            'closedAt': issue['closedAt'],
            'state': issue['state'],
            'labels': labels,
            'timelineItems': timeline_items
        }

        normalized_issues.append(normalized_issue)

    return normalized_issues


if __name__ == "__main__":
    issues = get_issues(True)
    normalized_issues = normalize_issues(issues)

    print(normalized_issues[-1])
