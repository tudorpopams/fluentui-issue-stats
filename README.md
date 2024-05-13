# Fluent UI repository issue stats

This project uses the Github REST API to fetch all v9 issues and generate charts for that data.

## Prerequisites

This project uses [Poetry](https://python-poetry.org/) as package manager, so it needs to be preinstalled before running any command

## Installing

Once you have Poetry installed, you can run:

```bash
poetry install
```

Enter a Poetry shell by running:

```bash
poetry shell
```

Start the Jupyter server by running:

```bash
poetry run jupyter notebook
```

## Current stats

![Top 10 labels](./fluent-issues_files/fluent-issues_1_0.png)

![Components issues](./fluent-issues_files/fluent-issues_2_0.png)

![Issues opened in the past 12 months](./fluent-issues_files/fluent-issues_3_0.png)

![Number of issues that required backlog grooming](./fluent-issues_files/fluent-issues_4_0.png)

![Number of closed epics per month](./fluent-issues_files/fluent-issues_5_0.png)
