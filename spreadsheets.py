import pandas as pd

from issues import (
    label_v9,
    label_epic,
    label_needs_backlog_grooming,
    label_needs_triage,
    label_a11y,
    label_bug,
    label_feature,
)

from datetime import datetime, timedelta

SPREADSHEET_PATH = "spreadsheets"


def overall_issue_stats(issues):
    # Convert issues to DataFrame
    df_issues = pd.DataFrame(issues)
    df_issues["createdAt"] = pd.to_datetime(df_issues["createdAt"], yearfirst=True)
    # Filter open issues
    df_issues = df_issues[df_issues["state"] == "OPEN"]

    # Identify Bugs, Features, and Epics
    bugs = df_issues[
        df_issues["labels"].apply(
            lambda x: label_bug in x or not (label_feature in x or label_epic in x)
        )
    ]
    features = df_issues[df_issues["labels"].apply(lambda x: label_feature in x)]
    epics = df_issues[df_issues["labels"].apply(lambda x: label_epic in x)]

    data = [
        ["Bugs", len(bugs)],
        ["Features", len(features)],
        ["Epics", len(epics)],
    ]

    total_issues = len(bugs) + len(features) + len(epics)

    issue_stats_df = pd.DataFrame(
        data, columns=["Type", f"Count (Total: {total_issues})"]
    )

    issue_stats_df.to_excel(f"{SPREADSHEET_PATH}/overall_issue_stats.xlsx", index=False)
    issue_stats_df.to_csv(f"{SPREADSHEET_PATH}/overall_issue_stats.csv", index=False)


def monthly_stats(issues):
    # Convert issues to DataFrame
    df_issues = pd.DataFrame(issues)
    df_issues["createdAt"] = pd.to_datetime(df_issues["createdAt"], yearfirst=True)
    df_issues["closedAt"] = pd.to_datetime(df_issues["closedAt"], yearfirst=True)

    # Group by year and month for opened issues
    data_opened = (
        df_issues.groupby(
            [df_issues["createdAt"].dt.year, df_issues["createdAt"].dt.month_name()]
        )["number"]
        .count()
        .reset_index(name="Opened Issues")
    )

    # Group by year and month for closed issues
    data_closed = (
        df_issues.dropna(subset=["closedAt"])
        .groupby(
            [df_issues["closedAt"].dt.year, df_issues["closedAt"].dt.month_name()]
        )["number"]
        .count()
        .reset_index(name="Closed Issues")
    )

    # Merge opened and closed data
    monthly_stats = pd.merge(
        data_opened, data_closed, on=["createdAt", "closedAt"], how="outer"
    ).fillna(0)

    dates = []

    for index in data_opened.index:
        formatted_index = f"{index[0]} {index[1]}"
        dates.append(formatted_index)

    monthly_stats["Month"] = dates
    monthly_stats.sort_index(ascending=False, inplace=True)

    monthly_stats.to_excel(f"{SPREADSHEET_PATH}/monthly_stats.xlsx", index=False)
    monthly_stats.to_csv(f"{SPREADSHEET_PATH}/monthly_stats.csv", index=False)


def component_stats(issues):
    # Convert issues to DataFrame
    df_issues = pd.DataFrame(issues)
    df_issues["createdAt"] = pd.to_datetime(df_issues["createdAt"], yearfirst=True)
    # Filter open issues
    df_issues = df_issues[df_issues["state"] == "OPEN"]

    # Extract component names
    component_names = set()
    for labels in df_issues["labels"]:
        for label in labels:
            if label.startswith("Component:"):
                component_names.add(label.replace("Component: ", ""))

    component_data = []

    for component_name in component_names:
        component_label = f"Component: {component_name}"
        component_issues = df_issues[
            df_issues["labels"].apply(lambda labels: component_label in labels)
        ]

        bugs = component_issues[
            component_issues["labels"].apply(
                lambda x: label_bug in x or not (label_feature in x or label_epic in x)
            )
        ]
        features = component_issues[
            component_issues["labels"].apply(lambda x: label_feature in x)
        ]
        total = len(bugs) + len(features)

        component_data.append([component_name, len(bugs), len(features), total])

    component_stats = pd.DataFrame(
        component_data, columns=["Component", "Bugs", "Features", "Total"]
    )

    component_stats.sort_values(by="Total", ascending=False, inplace=True)

    component_stats.to_excel(f"{SPREADSHEET_PATH}/component_stats.xlsx", index=False)
    component_stats.to_csv(f"{SPREADSHEET_PATH}/component_stats.csv", index=False)
