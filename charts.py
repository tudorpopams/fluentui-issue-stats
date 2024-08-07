import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import sys
import requests

from pathlib import Path
from dotenv import load_dotenv
from alive_progress import alive_bar

from collections import Counter

from spreadsheets import component_stats, monthly_stats, overall_issue_stats

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


def fetch_issues(repo, token):
    issues = []
    page = 1

    with alive_bar(0, title="Fetching issues", unit=" pages") as bar:
        while True:
            url = f"https://api.github.com/repos/{repo}/issues?state=all&page={
                page}&per_page=100&labels=Fluent UI react-components (v9)"
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"Error fetching issues: {
                                response.status_code}")

            page_issues = response.json()

            if not page_issues:
                break

            issues.extend(page_issues)
            page += 1
            bar()

    return issues


def get_charts_data(issues):
    all_issues = [
        issue for issue in issues if "pull_request" not in issue
    ]

    issues_minimal = []

    for issue in all_issues:
        labels_set = set([label["name"] for label in issue["labels"]])

        issues_minimal.append(
            {
                "id": issue["id"],
                "title": issue["title"],
                "labels": labels_set,
                "created_at": issue["created_at"],
                "state": issue["state"].lower(),
            }
        )

    df_issues_all = pd.DataFrame(issues_minimal)
    df_issues_all["created_at"] = pd.to_datetime(
        df_issues_all["created_at"], yearfirst=True
    )

    df_issues = pd.DataFrame(
        [issue for issue in issues_minimal if issue["state"] == "open"]
    )
    df_issues["created_at"] = pd.to_datetime(
        df_issues["created_at"], yearfirst=True)

    df_issues_closed = pd.DataFrame(
        [issue for issue in issues_minimal if issue["state"] == "closed"]
    )
    df_issues_closed["created_at"] = pd.to_datetime(
        df_issues_closed["created_at"], yearfirst=True
    )

    issue_labels = [
        issue["labels"] for issue in issues_minimal if issue["state"] == "open"
    ]

    all_labels = set()

    for labels in issue_labels:
        all_labels = all_labels.union(labels)

    component_names = set([label.replace("Component: ", "") for label in all_labels if label.startswith("Component:")])

    return all_issues, issues_minimal, df_issues, df_issues_closed, issue_labels, component_names


def plot_labels_pie(issue_labels):
    labels_counter = Counter()
    no_go_labels = set([label_v9])

    for labels in issue_labels:
        for label in labels:
            if label in no_go_labels:
                continue

            labels_counter.update([label])

    most_common_nr = 10

    labels = [
        f"{label} - {v}"
        for (label, v) in labels_counter.most_common(most_common_nr)
    ]
    values = [value for (_, value)
              in labels_counter.most_common(most_common_nr)]

    _, ax = plt.subplots(figsize=(16, 16))
    ax.set_title(
        f"Top {most_common_nr} labels out of {
            len(issue_labels)} open v9 issues in microsoft/fluentui"
    )

    plt.pie(values, labels=labels, autopct="%1.0f%%")

    return plt


def plot_components_issue_bar(issue_labels):
    labels_counter = Counter()

    for labels in issue_labels:
        for label in labels:
            labels_counter.update([label])

    components_counters = {
        k: v for k, v in labels_counter.items() if k.startswith("Component:")
    }
    sorted_components_counters = dict(
        sorted(components_counters.items(), key=lambda item: item[0])
    )
    labels = [
        key.replace("Component: ", "")
        for key in list(sorted_components_counters.keys())
    ]
    values = list(sorted_components_counters.values())

    _, ax = plt.subplots(figsize=(16, 20))

    ax.barh(labels, values)

    # Show top values
    ax.invert_yaxis()

    # Add annotation to bars
    for i in ax.patches:
        plt.text(
            i.get_width() + 0.2,
            i.get_y() + 0.5,
            str(round((i.get_width()), 2)),
            fontsize=10,
            fontweight="bold",
            color="grey",
        )

    # Add Plot Title
    ax.set_title("v9 Component issues")

    return plt


def plot_issues_in_the_past_12_months_line(df_issues, df_issues_closed, label=None):
    data_source = df_issues if label is None else df_issues[
        df_issues["labels"].apply(lambda x: label in x)
    ]

    data_source_closed = df_issues_closed if label is None else df_issues_closed[
        df_issues_closed["labels"].apply(lambda x: label in x)
    ]

    data = (
        data_source.groupby(
            [data_source["created_at"].dt.year,
                data_source["created_at"].dt.month_name()],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_closed = (
        data_source_closed.groupby(
            [
                data_source_closed["created_at"].dt.year,
                data_source_closed["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    values = list(data.values)
    labels = [f"{k[0]} {k[1]}" for k in list(data.index)]

    closed_values = list(data_closed.values)
    closed_labels = [f"{k[0]} {k[1]}" for k in list(data_closed.index)]

    _, ax = plt.subplots(figsize=(26, 9))
    ax.set_title("Issues opened in the past 12 months")
    ax.invert_xaxis()

    plt.plot(labels, values, label="Opened issues", linestyle="-", marker="o")
    plt.plot(
        closed_labels, closed_values, label="Closed issues", linestyle="--",
        marker="o"
    )

    plt.legend()

    return plt


def plot_backlog_grooming_line(df_issues, df_issues_closed):
    backlog_grooming_df = df_issues[
        df_issues["labels"].apply(lambda x: label_needs_backlog_grooming in x)
    ].sort_values(by="created_at", ascending=False)
    backlog_grooming_closed_df = df_issues_closed[
        df_issues_closed["labels"].apply(
            lambda x: label_needs_backlog_grooming in x)
    ].sort_values(by="created_at", ascending=False)

    data = (
        backlog_grooming_df.groupby(
            [
                backlog_grooming_df["created_at"].dt.year,
                backlog_grooming_df["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_closed = (
        backlog_grooming_closed_df.groupby(
            [
                backlog_grooming_closed_df["created_at"].dt.year,
                backlog_grooming_closed_df["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    values = list(data.values)
    labels = [f"{k[0]} {k[1]}" for k in list(data.index)]

    closed_values = list(data_closed.values)
    closed_labels = [f"{k[0]} {k[1]}" for k in list(data_closed.index)]

    _, ax = plt.subplots(figsize=(26, 9))
    ax.set_title("Issues that required backlog grooming in the past 12 months")
    ax.invert_xaxis()

    plt.plot(labels, values, label="Opened issues", linestyle="-", marker="o")
    plt.plot(
        closed_labels, closed_values, label="Closed issues", linestyle="--",
        marker="o"
    )

    plt.legend()

    return plt


def plot_closed_epics_line(df_issues, df_issues_closed, label_v9, label_epic):
    released_components_df = df_issues_closed[
        df_issues_closed["labels"].apply(
            lambda x: label_v9 in x and label_epic in x)
    ].sort_values(by="created_at", ascending=False)

    open_components_df = df_issues[
        df_issues["labels"].apply(
            lambda x: label_v9 in x and label_epic in x)
    ].sort_values(by="created_at", ascending=False)

    data = (
        released_components_df.groupby(
            [
                released_components_df["created_at"].dt.year,
                released_components_df["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_open = (
        open_components_df.groupby(
            [
                open_components_df["created_at"].dt.year,
                open_components_df["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    values = list(data.values)
    labels = [f"{k[0]} {k[1]}" for k in list(data.index)]

    open_values = list(data_open.values)
    open_labels = [f"{k[0]} {k[1]}" for k in list(data_open.index)]

    _, ax = plt.subplots(figsize=(26, 9))
    ax.set_title("Closed epics (components / large items)")
    ax.invert_xaxis()

    plt.plot(labels, values, linestyle="-", marker="o")
    plt.plot(open_labels, open_values, linestyle="--", marker="o")

    return plt


def plot_triage_issues_line(df_issues):
    created_issues = df_issues.sort_values(by="created_at", ascending=False)
    created_issues["created_at"] = pd.to_datetime(
        created_issues["created_at"] - pd.to_timedelta(1, unit="w"))

    triage_df = df_issues[
        df_issues["labels"].apply(lambda x: label_needs_triage in x)
    ].sort_values(by="created_at", ascending=False)

    triage_df["created_at"] = pd.to_datetime(
        triage_df["created_at"] - pd.to_timedelta(1, unit="w"))

    data_created = (
        created_issues.groupby(
            [
                created_issues["created_at"].dt.year,
                created_issues["created_at"].dt.month_name(),
                pd.Grouper(key="created_at", freq="W-MON"),
            ],
        )["labels"]
        .count()
        .sort_index(ascending=False)
        .head(12)
    )

    data = (
        triage_df.groupby(
            [
                triage_df["created_at"].dt.year,
                triage_df["created_at"].dt.month_name(),
                pd.Grouper(key="created_at", freq="W-MON"),
            ],
        )["labels"]
        .count()
        .sort_index(ascending=False)
    )

    created_values = list(data_created.values)
    created_labels = [k[2].strftime("%Y-%m-%d")
                      for k in list(data_created.index)]

    values = list(data.values)
    labels = [k[2].strftime("%Y-%m-%d") for k in list(data.index)]

    _, ax = plt.subplots(figsize=(26, 9))
    ax.set_title("Issues were created and issues that need triage")
    ax.invert_xaxis()

    for i, txt in enumerate(values):
        ax.annotate(
            txt,
            (labels[i], values[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    for i, txt in enumerate(created_values):
        ax.annotate(
            txt,
            (created_labels[i], created_values[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    plt.plot(labels, values, label="Issues needing triage",
             linestyle="-", marker="o")
    plt.plot(created_labels, created_values,
             label="Created issues", linestyle="--", marker="o")

    plt.xticks(rotation=45)
    plt.legend()

    return plt


def _generate_and_save_plots(issues):
    _, issues_minimal, df_issues, df_issues_closed, issue_labels, component_names = get_charts_data(
        issues)

    with alive_bar(7, title="Generating and saving charts", unit=" charts") as bar:
        plt = plot_labels_pie(issue_labels)
        plt.tight_layout()
        plt.savefig("images/stats-01.png")

        bar()

        plt = plot_components_issue_bar(issue_labels)
        plt.tight_layout()
        plt.savefig("images/stats-02.png")

        bar()

        plt = plot_issues_in_the_past_12_months_line(
            df_issues, df_issues_closed)
        plt.tight_layout()
        plt.savefig("images/stats-03.png")

        bar()

        plt = plot_backlog_grooming_line(df_issues, df_issues_closed)
        plt.tight_layout()
        plt.savefig("images/stats-04.png")

        bar()

        plt = plot_closed_epics_line(df_issues, df_issues_closed, label_v9, label_epic)
        plt.tight_layout()
        plt.savefig("images/stats-05.png")

        bar()

        plt = plot_triage_issues_line(df_issues)
        plt.tight_layout()
        plt.savefig("images/stats-06.png")
        bar()

        plt = plot_issues_in_the_past_12_months_line(
            df_issues, df_issues_closed, label_a11y)
        plt.tight_layout()
        plt.savefig("images/stats-07.png")

        bar()

def _generate_and_save_sheets(issues):
    _, _issues_minimal, df_issues, df_issues_closed, _issue_labels, component_names = get_charts_data(
        issues)

    with alive_bar(3, title="Generating and saving spreadsheets", unit=" sheets") as bar:
        overall_issue_stats(df_issues, label_bug, label_feature, label_epic)
        bar()

        monthly_stats(df_issues, df_issues_closed)
        bar()

        component_stats(component_names, df_issues, label_bug, label_feature, label_epic)
        bar()

def main():
    repo = "microsoft/fluentui"
    token = os.environ["GITHUB_TOKEN"]
    data_folder = f"data/{sys.argv[1]}"
    Path(data_folder).mkdir(parents=True, exist_ok=True)

    issues = fetch_issues(repo, token)

    with open(f"{data_folder}/issues.json", "w") as f:
        json.dump(issues, f)

    _generate_and_save_plots(issues)
    _generate_and_save_sheets(issues)


if __name__ == "__main__":
    main()
