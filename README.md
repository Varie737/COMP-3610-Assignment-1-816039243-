# NYC Yellow Taxi Data Pipeline & Interactive Dashboard  
COMP 3610 – Big Data Analytics  
Varsha Roopchand 816039243
## Project Overview

This project implements an end-to-end data pipeline and interactive visualization dashboard using the NYC Yellow Taxi Trip dataset (January 2024).

The pipeline includes:

- Programmatic data ingestion
- Data validation and verification
- Data cleaning and transformation
- Feature engineering
- SQL analysis using DuckDB
- Interactive visualization dashboard built with Streamlit

The final dashboard enables users to explore trip patterns, fare behavior, and payment trends through interactive filters and visualizations.

## Dataset
Source: NYC Taxi & Limousine Commission (TLC)

Files used:

1. Yellow Taxi Trip Data (January 2024)
2. Taxi Zone Lookup Table

The dataset contains approximately 3 million trip records.

## Technologies Used

- Python 3.12
- Polars (data processing)
- DuckDB (SQL analytics)
- Plotly (interactive visualizations)
- Streamlit (dashboard framework)
- Pandas (visualization compatibility)

## Project Structure
├── assignment1.ipynb # Parts 1 & 2 + Part 3 (visualization prototypes)
├── app.py # Streamlit dashboard application
├── README.md
├── requirements.txt
├── .gitignore
└── data/
├── raw/ # Raw downloaded datasets (not committed)
└── processed/ # Cleaned dataset for dashboard (not committed)
### Streamlit URL
http://localhost:8501/

## Setup Instructions

### Step 1: Clone the Repository
git clone: https://github.com/Varie737/COMP-3610-Assignment-1-816039243-

### Step 2: Install Dependencies
pip install -r requirements.txt
### Step 3: Run the Dashboard
python -m streamlit run app.py

pip install -r requirements.txt
### Step 3: Run the Dashboard
python -m streamlit run app.py
