#!/bin/bash

poetry run jupyter nbconvert --to markdown fluent-issues.ipynb
rm fluent-issues.md