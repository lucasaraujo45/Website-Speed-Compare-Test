# Website Speed Test

This Python script uses Google Lighthouse to perform website performance testing. It allows users to enter multiple URLs and specify the number of tests to run per website. The script aggregates the performance metrics from Lighthouse and displays the average in a user-friendly GUI.

## Features

- Run Google Lighthouse tests multiple times on multiple URLs.
- Display average performance metrics in a table format.
- Customizable number of test runs.
- GUI with customizable color themes.

## Prerequisites

Before running this script, you must have the following installed:
- Python 3
- Node.js
- Lighthouse (can be installed via npm with `npm install -g lighthouse`)

## Usage

1. Clone the repository or download the `speed-test.py` script.
2. Run the script using Python:
3. Enter the website URLs in the provided text area, one URL per line.
4. Specify the number of tests to run for each URL in the 'Number of tests per URL' entry field.
5. Click the 'Start Performance Test' button to begin testing.
6. Results will be displayed in a table with sortable columns for each metric.

