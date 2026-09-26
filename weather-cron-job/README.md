# Weather Data Cron Job

This project automatically updates historical weather data for cities across India using **Open-Meteo**, **Google Drive**, and **GitHub Actions**.

The workflow runs automatically every day at **1:00 AM IST**.

---

## How It Works

```text
GitHub Actions
      │
      │ 1:00 AM IST
      ▼
Python Script
      │
      ├──────────────► Google Drive
      │                 │
      │                 ▼
      │            india_param.json
      │
      ▼
Open-Meteo Archive API
      │
      │ Yesterday's 24-hour data
      ▼
Update weather data
      │
      ▼
Google Drive
      │
      ▼
Updated india_param.json
```

The script:

1. Starts automatically using GitHub Actions.
2. Authenticates with Google Drive using a Google Service Account.
3. Reads `india_param.json` from Google Drive.
4. Gets yesterday's weather data from Open-Meteo.
5. Updates the data for every city.
6. Removes the oldest 24 hours.
7. Uploads the updated JSON back to Google Drive.

---

# Project Structure

```text
weather-cron-job/
│
├── update_weather_data.py
├── india_cities.json
├── requirements.txt
│
└── .github/
    └── workflows/
        └── update.yml
```

The Google Service Account JSON file is used locally but should **not be committed to GitHub**.

```text
weather-project-service-account.json
```

For GitHub Actions, the service account credentials are stored as a GitHub Secret.

---

# Requirements

The project uses:

* Python 3.12
* Google Drive API
* Google Service Account
* Open-Meteo Archive API
* GitHub Actions
* Pandas
* Requests

---

# Python Packages

`requirements.txt`:

```text
pandas==2.3.2
requests==2.32.5
google-api-python-client==2.179.0
google-auth==2.40.3
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.2
```

Install them with:

```bash
pip install -r requirements.txt
```

---

# Google Cloud Setup

## 1. Create a Google Cloud Project

Open:

https://console.cloud.google.com/

Create a project for the weather application.

---

## 2. Enable Google Drive API

In Google Cloud Console:

```text
APIs & Services
        ↓
Library
        ↓
Google Drive API
        ↓
Enable
```

---

# Create a Service Account

Go to:

```text
IAM & Admin
        ↓
Service Accounts
```

Create a new service account.

Example:

```text
weather-data-updater
```

After creating the service account, open it.

---

# Create Service Account Key

Go to:

```text
Service Account
        ↓
Keys
        ↓
Add Key
        ↓
Create new key
        ↓
JSON
```

Download the JSON file.

Rename it:

```text
weather-project-service-account.json
```

Keep this file private.

**Never commit this file to GitHub.**

---

# Give the Service Account Access to Google Drive

Open the Google Drive file containing:

```text
india_param.json
```

Share the file with the service account email.

The email will look similar to:

```text
weather-data-updater@your-project.iam.gserviceaccount.com
```

Give it:

```text
Editor
```

permission because the Python script needs to update the file.

---

# Google Drive File

The weather dataset is stored in Google Drive as:

```text
india_param.json
```

The Python script identifies the file using its Google Drive File ID:

```python
FILE_ID = "YOUR_FILE_ID"
```

For example:

```python
FILE_ID = "12Eijy87QCseHV7kH82gKcXRDcMFbxnCv"
```

---

# Weather Data

The city coordinates are stored in:

```text
india_cities.json
```

Example:

```json
{
    "Kolkata": {
        "lat": 22.56263,
        "lon": 88.36304
    },
    "Delhi": {
        "lat": 28.6139,
        "lon": 77.2090
    }
}
```

The main weather file contains the historical weather data.

Example structure:

```json
{
    "Kolkata": {
        "lat": 22.56263,
        "lon": 88.36304,
        "daily": {
            "temperature_2m": [],
            "relative_humidity_2m": [],
            "dew_point_2m": [],
            "surface_pressure": [],
            "precipitation": [],
            "rain": [],
            "snowfall": [],
            "cloud_cover": [],
            "wind_speed_10m": [],
            "wind_gusts_10m": [],
            "wind_direction_10m": [],
            "shortwave_radiation": []
        }
    }
}
```

---

# Open-Meteo Data

The script requests the following hourly parameters:

```text
temperature_2m
relative_humidity_2m
dew_point_2m
surface_pressure
precipitation
rain
snowfall
cloud_cover
wind_speed_10m
wind_gusts_10m
wind_direction_10m
shortwave_radiation
```

The request is made to the Open-Meteo Archive API.

---

# Daily Update Process

The script calculates yesterday's date using Indian Standard Time.

```python
ist = ZoneInfo("Asia/Kolkata")

yesterday = (
    datetime.now(ist) - timedelta(days=1)
).strftime("%Y-%m-%d")
```

For example, if the workflow runs on:

```text
2026-09-26
```

the script requests:

```text
2026-09-25
```

from Open-Meteo.

---

# Updating the Rolling Dataset

Each city receives 24 new hourly values.

The script first adds the new data:

```python
df_output[city]["daily"][key].extend(
    hourly[key]
)
```

Then it removes the oldest 24 values:

```python
df_output[city]["daily"][key] = (
    df_output[city]["daily"][key][24:]
)
```

Therefore, the dataset maintains a rolling window of historical weather data.

---

# Handling API Failures

Open-Meteo requests can occasionally timeout.

The script retries each city up to **3 times**.

```text
Attempt 1
   ↓
Failed?
   ↓
Wait 5 seconds
   ↓
Attempt 2
   ↓
Failed?
   ↓
Wait 5 seconds
   ↓
Attempt 3
```

If all attempts fail, that city is skipped and the script continues with the next city.

This prevents one failed API request from stopping the entire update.

---

# Upload Retry

After updating all cities, the script uploads the new JSON file to Google Drive.

The upload is attempted up to **5 times**.

```text
Upload
  ↓
Failed?
  ↓
Wait 10 seconds
  ↓
Retry
```

If all five attempts fail, the GitHub Actions job fails.

---

# GitHub Actions

The workflow is located at:

```text
.github/workflows/update.yml
```

The workflow runs every day at:

```text
1:00 AM IST
```

GitHub Actions uses UTC.

Therefore:

```text
1:00 AM IST
=
7:30 PM UTC
```

Since the date is the previous day in UTC, the cron expression is:

```yaml
cron: '30 19 * * *'
```

---

# GitHub Actions Workflow

```yaml
name: Weather Update

on:
  schedule:
    # 1:00 AM IST = 19:30 UTC previous day
    - cron: '30 19 * * *'

  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: weather-cron-job

    steps:

    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"

    - name: Install packages
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Create Service Account File
      run: |
        echo '${{ secrets.GCP_SERVICE_ACCOUNT }}' > weather-project-service-account.json

    - name: Run Weather Script
      run: |
        python update_weather_data.py
```

---

# GitHub Secret

The service account JSON must be stored in GitHub Secrets.

Go to:

```text
GitHub Repository
        ↓
Settings
        ↓
Secrets and variables
        ↓
Actions
        ↓
New repository secret
```

Create:

```text
Name:
GCP_SERVICE_ACCOUNT
```

Paste the complete contents of:

```text
weather-project-service-account.json
```

into the secret.

---

# Security

Do **not** upload the service account JSON to GitHub.

Do not put this in your repository:

```text
weather-project-service-account.json
```

Add it to `.gitignore`:

```gitignore
weather-project-service-account.json
```

Also never put the private key directly into Python code.

---

# Running Locally

Place these files together:

```text
weather-cron-job/
│
├── update_weather_data.py
├── india_cities.json
├── requirements.txt
└── weather-project-service-account.json
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python update_weather_data.py
```

The script will:

```text
Read Google Drive
       ↓
Get yesterday's weather
       ↓
Update all cities
       ↓
Remove oldest 24 hours
       ↓
Upload to Google Drive
```

---

# Manual GitHub Actions Run

The workflow also contains:

```yaml
workflow_dispatch:
```

This allows you to manually run the workflow.

Go to:

```text
GitHub
   ↓
Actions
   ↓
Weather Update
   ↓
Run workflow
```

---

# Data Flow

```text
                    ┌───────────────────┐
                    │   GitHub Actions  │
                    │    1:00 AM IST    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Python Script     │
                    │ update_weather_   │
                    │ data.py           │
                    └───────┬───────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
        ┌─────────────────┐   ┌──────────────────┐
        │  Google Drive   │   │    Open-Meteo    │
        │                 │   │                  │
        │ india_param.json│   │ Yesterday's data│
        └────────┬────────┘   └────────┬─────────┘
                 │                     │
                 └──────────┬──────────┘
                            ▼
                    ┌───────────────────┐
                    │ Update Weather    │
                    │ Data              │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Google Drive      │
                    │ Updated JSON      │
                    └───────────────────┘
```

---

# Summary

The system uses:

```text
Python
   +
Google Service Account
   +
Google Drive
   +
Open-Meteo
   +
GitHub Actions
```

Every day at **1:00 AM IST**, GitHub Actions runs the Python script.

The script reads the existing weather dataset from Google Drive, retrieves the previous day's 24-hour weather data from Open-Meteo, updates the rolling dataset, and writes the updated file back to Google Drive.
