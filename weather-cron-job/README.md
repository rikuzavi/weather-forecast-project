# CRON JOB FOR WEATHER PARAMETERS

This directory contains the scheduled weather-data update system for the weather forecast project.

The GitHub Actions workflow runs automatically every **1:00 AM IST**. It retrieves the existing weather dataset from **Hugging Face**, fetches the previous day's weather data from **Open-Meteo**, updates the dataset, and uploads the updated JSON back to Hugging Face.

---

# HUGGING FACE INTEGRATION

The project uses a Hugging Face Dataset Repository as the storage location for the weather data.

The workflow:

```text
GitHub Repository
        │
        ▼
GitHub Actions starts automatically
        │
        ▼
Install Python and required packages
        │
        ▼
Load HF_TOKEN from GitHub Secrets
        │
        ▼
Run update_weather_data.py
        │
        ▼
Read existing weather JSON
from Hugging Face
        │
        ▼
Fetch previous day's weather
from Open-Meteo
        │
        ▼
Update weather data
        │
        ▼
Upload updated JSON
to Hugging Face
        │
        ▼
Workflow finishes
```

---

# DATA FLOW

The complete process is:

```text
                    GitHub Actions
                          │
                          ▼
                 update_weather_data.py
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Hugging Face              Open-Meteo
       Existing Data             Archive API
             │                         │
             │                         │
             └──────────┬──────────────┘
                        ▼
                 Update Weather
                     Data
                        │
                        ▼
                 Hugging Face
                 Updated JSON
```

The script does not use Google Drive anymore.

---

# PROCEDURE FOR THE WORKFLOW

The setup process is:

1. Create the initial weather dataset.
2. Create a Hugging Face account.
3. Create a Hugging Face Dataset Repository.
4. Upload the initial JSON file to Hugging Face.
5. Create a Hugging Face Access Token with **Write** permission.
6. Create a GitHub repository/workflow for the cron job.
7. Add the Hugging Face token to GitHub Actions Secrets.
8. Add the Python script, city data and `requirements.txt`.
9. Configure the GitHub Actions workflow.
10. Run the workflow manually once using `workflow_dispatch`.
11. Verify that the weather data was updated.
12. Allow GitHub Actions to execute automatically every day.

---

# FILE STRUCTURE

```text
weather-cron-job
│
├── requirements.txt
│
├── update_weather_data.py
│
├── india_cities.json
│
└── .github
    │
    └── workflows
        │
        └── update.yml
```

The Hugging Face dataset is stored separately:

```text
Hugging Face Dataset Repository
│
└── india_param.json
```

No Hugging Face token should be stored inside the repository.

---

# HUGGING FACE DATASET SETUP

## 1. Create a Hugging Face account

Open:

https://huggingface.co/

Create an account or sign in.

---

## 2. Create a Dataset Repository

From Hugging Face:

```text
New → Dataset
```

Create a repository, for example:

```text
weather-data
```

The repository will have a URL similar to:

```text
https://huggingface.co/datasets/YOUR_USERNAME/weather-data
```

---

## 3. Upload the initial JSON

Upload:

```text
india_param.json
```

The repository should contain:

```text
weather-data
│
├── india_param.json
└── README.md
```

---

# HUGGING FACE ACCESS TOKEN

The Python script needs permission to read and update the dataset.

1. Open:

https://huggingface.co/settings/tokens

2. Create a new Access Token.
3. Give it a name, for example:

```text
weather-project
```

4. Select **Write** permission.
5. Create the token.
6. Copy the token beginning with:

```text
hf_
```

Keep the token private.

Do not put it directly inside:

```text
update_weather_data.py
```

and do not commit it to GitHub.

---

# ADDING HUGGING FACE TOKEN TO GITHUB

Open the GitHub repository.

Go to:

```text
Settings
    ↓
Secrets and variables
    ↓
Actions
```

Click:

```text
New repository secret
```

Use:

```text
Name:
HF_TOKEN
```

For the value, paste your Hugging Face Access Token:

```text
hf_xxxxxxxxxxxxxxxxxxxxxxxxx
```

Click:

```text
Add secret
```

GitHub will then provide the token to the workflow without exposing its value in the repository.

---

# PYTHON SCRIPT

The Python script performs the following operations:

```text
1. Authenticate with Hugging Face
2. Read india_param.json
3. Calculate yesterday's date
4. Read city coordinates
5. Request previous day's data from Open-Meteo
6. Add the new 24 hours of data
7. Remove the oldest 24 hours
8. Save the updated JSON
9. Upload the JSON to Hugging Face
```

The main file is:

```text
update_weather_data.py
```

---

# REQUIREMENTS.TXT

The project uses:

```text
pandas==2.3.2
requests==2.32.5
huggingface_hub==0.34.4
```

`requirements.txt`:

```text
pandas==2.3.2
requests==2.32.5
huggingface_hub==0.34.4
```

Google Drive and Google Cloud packages are no longer required.

---

# HUGGING FACE CONFIGURATION IN PYTHON

The token is read from the environment rather than being written directly into the Python file.

```python
import os

HF_TOKEN = os.environ["HF_TOKEN"]

REPO_ID = "YOUR_USERNAME/weather-data"

FILE_NAME = "india_param.json"
```

The GitHub Actions workflow provides:

```text
HF_TOKEN
```

to the Python program.

---

# READING DATA FROM HUGGING FACE

The dataset can be read using:

```python
from huggingface_hub import hf_hub_download

file_path = hf_hub_download(
    repo_id=REPO_ID,
    filename=FILE_NAME,
    repo_type="dataset",
    token=HF_TOKEN
)
```

Then:

```python
import json

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)
```

For example:

```python
kolkata = data["Kolkata"]

print(kolkata["lat"])
print(kolkata["lon"])
```

Weather parameters can be accessed through:

```python
data["Kolkata"]["daily"]
```

---

# UPLOADING DATA TO HUGGING FACE

After modifying the JSON:

```python
api.upload_file(
    path_or_fileobj=FILE_NAME,
    path_in_repo=FILE_NAME,
    repo_id=REPO_ID,
    repo_type="dataset",
    commit_message="Update weather data"
)
```

This creates a new commit in the Hugging Face Dataset Repository.

---

# SETTING UP GITHUB ACTION

The workflow file is:

```text
.github/workflows/update.yml
```

The workflow automatically executes every day at:

```text
1:00 AM IST
```

The cron expression is:

```yaml
cron: '30 19 * * *'
```

GitHub Actions uses UTC, so:

```text
19:30 UTC
     ↓
01:00 IST
```

on the following day.

---

# MY UPDATE.YML CODE

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

    - name: Run Weather Script
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
      run: |
        python update_weather_data.py
```

---

# WHY THE SERVICE ACCOUNT IS NO LONGER REQUIRED

The previous implementation used:

```text
Google Cloud
      │
      ▼
Service Account
      │
      ▼
Google Drive API
      │
      ▼
Weather JSON
```

The new implementation uses:

```text
GitHub Actions
      │
      ▼
HF_TOKEN
      │
      ▼
Hugging Face Hub
      │
      ▼
Weather JSON
```

Therefore these are no longer required:

```text
weather-project-XXXXXX-XXXXXX.json
GCP_SERVICE_ACCOUNT
Google Drive API
Google Cloud Service Account
google-api-python-client
google-auth
google-auth-httplib2
google-auth-oauthlib
```

---

# RUNNING THE WORKFLOW MANUALLY

The workflow contains:

```yaml
workflow_dispatch:
```

This allows you to run it manually.

Go to:

```text
GitHub Repository
    ↓
Actions
    ↓
Weather Update
    ↓
Run workflow
```

GitHub will start the workflow.

Check the logs for:

```text
Reading data from Hugging Face...
Data loaded successfully.
Updating data for: YYYY-MM-DD
Processing Kolkata...
✓ Kolkata
...
waiting to upload
Upload completed successfully.
```

---

# DAILY AUTOMATIC UPDATE

After the workflow has been tested successfully, GitHub Actions will execute it automatically according to:

```yaml
- cron: '30 19 * * *'
```

The intended schedule is:

```text
Every day
1:00 AM IST
```

The workflow can also be triggered manually at any time.

---

# WEATHER DATA UPDATE LOGIC

For every city, the script:

```text
Existing data
      │
      ▼
Remove oldest 24 hours
      │
      ▼
Fetch previous day's 24 hours
      │
      ▼
Append new 24 hours
      │
      ▼
Save updated data
```

For example:

```text
Before:

Hour 1 ───────────── Hour N
   │
   └── oldest data

After:

Hour 25 ──────────── Hour N + 24
                      │
                      └── newest data
```

This maintains a rolling weather-data window.

---

# OPEN-METEO

Historical weather data is retrieved from the Open-Meteo Archive API.

The script requests parameters including:

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

The request is made separately for each city.

---

# ERROR HANDLING

If Open-Meteo fails for one city, the script continues processing the remaining cities.

For example:

```text
Processing Gangtok...
Problem with Gangtok: HTTPSConnectionPool(...): Read timed out

Processing Imphal...
✓ Imphal
```

A failure for one city does not necessarily stop the complete workflow.

The script can also retry requests when a timeout occurs.

---

# GITHUB SECRETS

The repository should contain only non-sensitive configuration.

### Required GitHub Secret

```text
HF_TOKEN
```

### Do NOT commit

```text
hf_...
```

or any other private access token.

The token should only be stored in:

```text
GitHub → Settings → Secrets and variables → Actions
```

---

# SECURITY

Never commit the Hugging Face Access Token to GitHub.

Bad:

```python
HF_TOKEN = "hf_xxxxxxxxxxxxxxxxx"
```

Good:

```python
import os

HF_TOKEN = os.environ["HF_TOKEN"]
```

The GitHub Actions workflow provides it securely:

```yaml
env:
  HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

---

# FINAL PROJECT STRUCTURE

```text
weather-forecast-project
│
├── weather-cron-job
│   │
│   ├── requirements.txt
│   ├── update_weather_data.py
│   ├── india_cities.json
│   │
│   └── .github
│       │
│       └── workflows
│           │
│           └── update.yml
│
└── ...
```

Hugging Face:

```text
Hugging Face
│
└── weather-data
    │
    ├── india_param.json
    └── README.md
```

---

# COMPLETE SYSTEM

```text
                    ┌─────────────────────┐
                    │    GitHub Actions   │
                    │                     │
                    │   1:00 AM IST       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ update_weather_data │
                    │        .py          │
                    └───────┬─────┬───────┘
                            │     │
                 Read data  │     │ Fetch weather
                            │     │
                            ▼     ▼
                   ┌──────────┐ ┌──────────┐
                   │Hugging   │ │Open-     │
                   │Face      │ │Meteo     │
                   └────┬─────┘ └────┬─────┘
                        │             │
                        └──────┬──────┘
                               ▼
                       Update JSON Data
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Hugging Face    │
                    │                     │
                    │ india_param.json    │
                    └─────────────────────┘
```

The result is a daily automated weather-data pipeline with **GitHub Actions as the scheduler, Open-Meteo as the historical weather-data source, and Hugging Face as the dataset storage**.
