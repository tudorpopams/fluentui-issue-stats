import pandas as pd


def overall_issue_stats(df_issues, label_bug, label_feature, label_epic):
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

    issue_stats_df.to_excel("xsls/overall_issue_stats.xlsx", index=False)


def monthly_stats(df_issues, df_issues_closed):
    data = (
        df_issues.groupby(
            [
                df_issues["created_at"].dt.year,
                df_issues["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_closed = (
        df_issues_closed.groupby(
            [
                df_issues_closed["created_at"].dt.year,
                df_issues_closed["created_at"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    monthly_stats = pd.DataFrame(columns=["Month", "Closed Issues", "Opened Issues"])
    monthly_stats["Closed Issues"] = data_closed.values
    monthly_stats["Opened Issues"] = data.values

    dates = []

    for index in data.index:
        formatted_index = f"{index[0]} {index[1]}"
        dates.append(formatted_index)

    monthly_stats["Month"] = dates
    monthly_stats.sort_index(ascending=False, inplace=True)

    monthly_stats.to_excel("xsls/monthly_stats.xlsx", index=False)


def component_stats(component_names, df_issues, label_bug, label_feature, label_epic):
    component_data = []

    for component_name in component_names:
        component_label = f"Component: {component_name}"
        component_df = df_issues[
            df_issues["labels"].map(lambda labels: component_label in labels)
        ]

        bugs = component_df[
            component_df["labels"].map(
                lambda x: label_bug in x or not (label_feature in x or label_epic in x)
            )
        ]
        features = component_df[
            component_df["labels"].map(lambda x: label_feature in x)
        ]
        total = len(bugs) + len(features)

        component_data.append([component_name, len(bugs), len(features), total])

    component_stats = pd.DataFrame(
        component_data, columns=["Component", "Bugs", "Features", "Total"]
    )

    component_stats.sort_values(by="Total", ascending=False, inplace=True)

    component_stats.to_excel("xsls/component_stats.xlsx", index=False)
