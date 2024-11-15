from numpy import tri
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from alive_progress import alive_bar

from collections import Counter

from issues import (
    normalize_issues,
    get_issues,
    label_v9,
    label_epic,
    label_needs_backlog_grooming,
    label_needs_triage,
    label_bug,
    label_feature,
)


def save_dataframe(df, filename_base):
    """
    Save the given DataFrame to CSV and Excel files.
    """
    df.to_csv(f"spreadsheets/{filename_base}.csv", index=False)
    df.to_excel(f"spreadsheets/{filename_base}.xlsx", index=False)


def prepare_and_save_dataframe(data, columns, filename_base):
    """
    Create a DataFrame from data and columns, then save it.
    """
    df = pd.DataFrame(data, columns=columns)
    save_dataframe(df, filename_base)
    return df


def initialize_plot(figsize, title, invert_xaxis=False):
    """
    Initialize a matplotlib plot with the given size and title.
    Optionally invert the x-axis.
    """
    _, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    if invert_xaxis:
        ax.invert_xaxis()
    return ax


def annotate_bars(ax, bars):
    """
    Annotate bars in a bar chart with their respective values.
    """
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax.text(
                bar.get_x() + width / 2,
                bar.get_y() + bar.get_height() / 2,
                f"{int(width)}",
                ha="center",
                va="center",
                color="black",
            )


def annotate_line(ax, x_data, y_data, offset=(0, 7)):
    """
    Annotate points in a line chart with their respective values.
    """
    for i, txt in enumerate(y_data):
        ax.annotate(
            txt,
            (x_data[i], y_data[i]),
            textcoords="offset points",
            xytext=offset,
            ha="center",
        )


# TODO: use all issues, not just the ones from the past year?
def plot_labels_pie(issues):
    labels_counter = Counter()
    no_go_labels = set([label_v9])
    open_issues = [issue for issue in issues if issue["state"] == "OPEN"]

    for issue in open_issues:
        if issue["state"] == "closed":
            continue

        labels = issue["labels"]

        for label in labels:
            if label in no_go_labels:
                continue

            labels_counter.update([label])

    most_common_nr = 10

    labels = [
        f"{label} - {v}" for (label, v) in labels_counter.most_common(most_common_nr)
    ]
    values = [value for (_, value) in labels_counter.most_common(most_common_nr)]

    # Prepare DataFrame with label counts and save
    data = labels_counter.most_common(most_common_nr)

    prepare_and_save_dataframe(data, ["Label", "Count"], "stats-01")

    _, ax = plt.subplots(figsize=(16, 16))
    ax.set_title(
        f"Top {most_common_nr} labels out of {len(open_issues)} open v9 issues in microsoft/fluentui"
    )

    plt.pie(values, labels=labels, autopct="%1.0f%%")

    return plt


def plot_components_issue_bar(issues):
    component_stats = {}

    for issue in issues:
        is_component = False
        component_name = ""

        for label in issue["labels"]:
            if not label.startswith("Component: "):
                continue

            component_name = label.replace("Component: ", "")

            if component_name not in component_stats:
                component_stats[component_name] = Counter()

            is_component = True

        if is_component:
            if label_bug in issue["labels"]:
                component_stats[component_name].update(["Bugs"])

            if label_feature in issue["labels"]:
                component_stats[component_name].update(["Features"])

    for component, stats in component_stats.copy().items():
        if "Bugs" not in stats:
            stats["Bugs"] = 0

        if "Features" not in stats:
            stats["Features"] = 0

        if stats["Bugs"] == 0 and stats["Features"] == 0:
            del component_stats[component]

    ax = initialize_plot(figsize=(16, 20), title="v9 Component issues")

    categories = list(component_stats.keys())
    bugs = [component_stats[category]["Bugs"] for category in categories]
    features = [component_stats[category]["Features"] for category in categories]
    totals = [bugs[i] + features[i] for i in range(len(categories))]

    sorted_indices = sorted(range(len(categories)), key=lambda i: totals[i])

    categories_sorted = [categories[i] for i in sorted_indices]
    bugs_sorted = [bugs[i] for i in sorted_indices]
    features_sorted = [features[i] for i in sorted_indices]
    totals_sorted = [totals[i] for i in sorted_indices]
    categories_with_totals_sorted = [
        f"{categories_sorted[i]} ({totals_sorted[i]})"
        for i in range(len(categories_sorted))
    ]

    # Prepare DataFrame with component stats and save
    data = {
        "Component": categories_sorted,
        "Bugs": bugs_sorted,
        "Features": features_sorted,
        "Total": totals_sorted,
    }
    df_components = pd.DataFrame(data)
    save_dataframe(df_components, "stats-02")

    bars_features = ax.barh(
        categories_with_totals_sorted,
        features_sorted,
        color="#99ff99",
        label="Features",
    )  # Light green

    bars_bugs = ax.barh(
        categories_with_totals_sorted,
        bugs_sorted,
        left=features_sorted,
        color="#ff9999",
        label="Bugs",
    )  # Lighter red

    annotate_bars(ax, bars_features)
    annotate_bars(ax, bars_bugs)

    ax.set_xlabel("Count")
    ax.legend()

    return plt


def plot_issues_in_the_past_12_months_line(issues):
    open_issues = [issue for issue in issues if issue["state"] == "OPEN"]
    closed_issues = [issue for issue in issues if issue["state"] == "CLOSED"]

    data_source = pd.DataFrame(open_issues)
    data_source_closed = pd.DataFrame(closed_issues)

    data_source["createdAt"] = pd.to_datetime(data_source["createdAt"], yearfirst=True)

    data_source_closed["closedAt"] = pd.to_datetime(
        data_source_closed["closedAt"], yearfirst=True
    )

    data = (
        data_source.groupby(
            [
                data_source["createdAt"].dt.year,
                data_source["createdAt"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_closed = (
        data_source_closed.groupby(
            [
                data_source_closed["closedAt"].dt.year,
                data_source_closed["closedAt"].dt.month_name(),
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

    # Prepare DataFrames for opened and closed issues and save
    df_opened = pd.DataFrame({"Month": labels, "Opened_Issues": values})
    df_closed = pd.DataFrame({"Month": closed_labels, "Closed_Issues": closed_values})
    df_combined = pd.merge(df_opened, df_closed, on="Month", how="outer")
    save_dataframe(df_combined, "stats-03")

    ax = initialize_plot(
        figsize=(26, 9),
        title="Issues states in the past 12 months",
        invert_xaxis=True,
    )

    for i, txt in enumerate(values):
        ax.annotate(
            txt,
            (labels[i], values[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    for i, txt in enumerate(closed_values):
        ax.annotate(
            txt,
            (closed_labels[i], closed_values[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    plt.plot(labels, values, label="Opened issues", linestyle="-", marker="o")
    plt.plot(
        closed_labels, closed_values, label="Closed issues", linestyle="--", marker="o"
    )

    annotate_line(ax, labels, values)
    annotate_line(ax, closed_labels, closed_values, offset=(0, -15))

    plt.legend()

    return plt


def plot_backlog_grooming_line(issues):
    backlog_grooming_issues = [
        issue for issue in issues if label_needs_backlog_grooming in issue["labels"]
    ]

    groomed_issues = []

    for issue in issues:
        if any(
            label_needs_backlog_grooming == item["label"]
            for item in issue.get("timelineItems", [])
            if item["type"] == "LabeledEvent"
        ):
            backlog_grooming_issues.append(issue)

        if any(
            label_needs_backlog_grooming == item["label"]
            for item in issue.get("timelineItems", [])
            if item["type"] == "UnlabeledEvent"
        ):
            groomed_issues.append(issue)

    backlog_grooming_df = pd.DataFrame(backlog_grooming_issues).sort_values(
        by="createdAt", ascending=False
    )

    backlog_grooming_df["createdAt"] = pd.to_datetime(
        backlog_grooming_df["createdAt"], yearfirst=True
    )

    groomed_df = pd.DataFrame(groomed_issues).sort_values(
        by="createdAt", ascending=False
    )

    groomed_df["createdAt"] = pd.to_datetime(groomed_df["createdAt"], yearfirst=True)

    data = (
        backlog_grooming_df.groupby(
            [
                backlog_grooming_df["createdAt"].dt.year,
                backlog_grooming_df["createdAt"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    data_groomed = (
        groomed_df.groupby(
            [
                groomed_df["createdAt"].dt.year,
                groomed_df["createdAt"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    values = list(data.values)
    labels = [f"{k[0]} {k[1]}" for k in list(data.index)]

    groomed_values = list(data_groomed.values)
    groomed_labels = [f"{k[0]} {k[1]}" for k in list(data_groomed.index)]

    # Prepare DataFrames for backlog grooming stats and save
    df_backlog = pd.DataFrame({"Month": labels, "Added_for_Grooming": values})
    df_groomed = pd.DataFrame({"Month": groomed_labels, "Groomed": groomed_values})
    df_combined = pd.merge(df_backlog, df_groomed, on="Month", how="outer")
    save_dataframe(df_combined, "stats-04")

    ax = initialize_plot(
        figsize=(26, 9),
        title="Issues that required backlog grooming in the past 12 months",
    )
    ax.invert_xaxis()

    plt.plot(
        labels,
        values,
        label="Added for grooming",
        linestyle="-",
        marker="o",
        linewidth=2,
    )
    plt.plot(
        groomed_labels,
        groomed_values,
        label="Groomed",
        linestyle="--",
        marker="o",
        linewidth=2,
    )

    annotate_line(
        ax,
        labels,
        values,
        offset=(0, 10),
    )
    annotate_line(
        ax,
        groomed_labels,
        groomed_values,
        offset=(0, 10),
    )

    plt.legend()

    return plt


def plot_closed_epics_line(issues):
    closed_epics = [
        issue
        for issue in issues
        if issue["state"] == "CLOSED" and label_epic in issue["labels"]
    ]

    closed_epics_df = pd.DataFrame(closed_epics).sort_values(
        by="closedAt", ascending=False
    )
    closed_epics_df["closedAt"] = pd.to_datetime(
        closed_epics_df["closedAt"], yearfirst=True
    )

    data = (
        closed_epics_df.groupby(
            [
                closed_epics_df["closedAt"].dt.year,
                closed_epics_df["closedAt"].dt.month_name(),
            ],
            sort=False,
        )["labels"]
        .count()
        .head(12)
    )

    values = list(data.values)
    labels = [f"{k[0]} {k[1]}" for k in list(data.index)]

    # Prepare DataFrame for closed epics and save
    df_closed_epics = pd.DataFrame({"Month": labels, "Closed_Epics": values})
    save_dataframe(df_closed_epics, "stats-05")

    ax = initialize_plot(
        figsize=(26, 9),
        title="Closed Epics in the past 12 months",
    )
    ax.invert_xaxis()

    for i, txt in enumerate(values):
        ax.annotate(
            txt,
            (labels[i], values[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    plt.plot(labels, values, label="Closed Epics", linestyle="-", marker="o")

    annotate_line(ax, labels, values)

    plt.legend()

    return plt


def plot_triage_issues_line(issues):
    from datetime import datetime, timedelta

    # Collect dates when issues required triage (label added)
    triage_needed_dates = []
    for issue in issues:
        for event in issue.get("timelineItems", []):
            if event["type"] == "LabeledEvent" and event["label"] == label_needs_triage:
                triage_needed_dates.append(event["createdAt"])
                break  # Only consider the first time it was labeled

    # Collect dates when issues were triaged (label removed)
    triaged_dates = []
    for issue in issues:
        for event in issue.get("timelineItems", []):
            if (
                event["type"] == "UnlabeledEvent"
                and event["label"] == label_needs_triage
            ):
                triaged_dates.append(event["createdAt"])
                break  # Only consider the first time it was unlabeled

    # Convert to DataFrames and parse dates
    df_triage_needed = pd.DataFrame({"date": triage_needed_dates})
    df_triage_needed["date"] = pd.to_datetime(df_triage_needed["date"], yearfirst=True)
    df_triage_needed = df_triage_needed.sort_values(by="date")

    df_triaged = pd.DataFrame({"date": triaged_dates})
    df_triaged["date"] = pd.to_datetime(df_triaged["date"], yearfirst=True)
    df_triaged = df_triaged.sort_values(by="date")

    # Calculate the cutoff date for 12 weeks ago
    cutoff_date = datetime.now() - timedelta(weeks=12)

    # Filter the DataFrames to include only the past 12 weeks
    df_triage_needed = df_triage_needed[df_triage_needed["date"] >= cutoff_date]
    df_triaged = df_triaged[df_triaged["date"] >= cutoff_date]

    # Group by week starting on Monday
    data_needed = (
        df_triage_needed.groupby(pd.Grouper(key="date", freq="W-MON"))["date"]
        .size()
        .reset_index(name="count")
    )

    data_triaged = (
        df_triaged.groupby(pd.Grouper(key="date", freq="W-MON"))["date"]
        .size()
        .reset_index(name="count")
    )

    # Prepare data for plotting
    labels_needed = data_needed["date"].dt.strftime("%Y-%m-%d").tolist()
    values_needed = data_needed["count"].tolist()

    labels_triaged = data_triaged["date"].dt.strftime("%Y-%m-%d").tolist()
    values_triaged = data_triaged["count"].tolist()

    # Prepare DataFrames for triage stats and save
    df_triage_needed = pd.DataFrame(
        {"Week": labels_needed, "Issues_Needing_Triage": values_needed}
    )
    df_triaged = pd.DataFrame(
        {"Week": labels_triaged, "Issues_Triaged": values_triaged}
    )
    df_combined = pd.merge(df_triage_needed, df_triaged, on="Week", how="outer")
    save_dataframe(df_combined, "stats-06")

    ax = initialize_plot(
        figsize=(26, 9),
        title="Issues Needing Triage vs Issues Triaged Per Week",
    )

    plt.plot(
        labels_needed,
        values_needed,
        label="Issues Needing Triage",
        linestyle="--",
        marker="o",
        color="orange",
    )
    plt.plot(
        labels_triaged,
        values_triaged,
        label="Issues Triaged",
        linestyle="-",
        marker="o",
    )

    annotate_line(ax, labels_needed, values_needed)
    annotate_line(ax, labels_triaged, values_triaged, offset=(0, -15))

    # Annotate data points
    for i, txt in enumerate(values_needed):
        ax.annotate(
            txt,
            (labels_needed[i], values_needed[i]),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
        )

    for i, txt in enumerate(values_triaged):
        ax.annotate(
            txt,
            (labels_triaged[i], values_triaged[i]),
            textcoords="offset points",
            xytext=(0, -15),
            ha="center",
        )

    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    return plt


def _generate_and_save_plots(issues):
    with alive_bar(6, title="Generating and saving charts", unit=" charts") as bar:
        plt = plot_labels_pie(issues)
        plt.tight_layout()
        plt.savefig("images/stats-01.png")

        bar()

        plt = plot_components_issue_bar(issues)
        plt.tight_layout()
        plt.savefig("images/stats-02.png")

        bar()

        plt = plot_issues_in_the_past_12_months_line(issues)
        plt.tight_layout()
        plt.savefig("images/stats-03.png")

        bar()

        plt = plot_backlog_grooming_line(issues)
        plt.tight_layout()
        plt.savefig("images/stats-04.png")

        bar()

        plt = plot_closed_epics_line(issues)
        plt.tight_layout()
        plt.savefig("images/stats-05.png")

        bar()

        plt = plot_triage_issues_line(issues)
        plt.tight_layout()
        plt.savefig("images/stats-06.png")
        bar()


def main():
    issues = get_issues(True)
    normalized_issues = normalize_issues(issues)

    _generate_and_save_plots(normalized_issues)


if __name__ == "__main__":
    main()
