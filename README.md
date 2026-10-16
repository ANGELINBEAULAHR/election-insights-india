# Election Polling and Vote Estimation

A Streamlit data science dashboard for exploring historical election records
and demonstrating sampling probability.

## Features

- Election dashboard with elector, voter and turnout metrics
- State and year filters
- Turnout trend and regional comparisons
- Gender-wise participation analysis when source columns are available
- Random record-sampling experiment
- Candidate, winner and expenditure dataset exploration
- Data quality report and CSV download
- Election-related news feed and official links

## Project structure

```text
Election-Polling-Vote-Estimation/
├── app.py
├── requirements.txt
├── README.md
└── data/
    ├── dataset1.csv
    ├── dataset2.csv
    └── dataset3.csv
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important note

The sampling exercise samples rows from historical aggregate records. It is
an educational statistics demonstration, not a sample of individual voters,
a live poll, or an official prediction of election results.

The dashboard needs `data/dataset1.csv` with elector and voter total columns
such as `Total_Electors` and `Total_Voters`. Other columns are detected when
recognisable names are available.
