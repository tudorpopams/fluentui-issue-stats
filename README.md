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

![Top 10 labels](./images/stats-01.png)

![Components issues](./images/stats-02.png)

![Issues opened in the past 12 months](./images/stats-03.png)

![Number of issues that required backlog grooming](./images/stats-04.png)

![Number of closed epics per month](./images/stats-05.png)
