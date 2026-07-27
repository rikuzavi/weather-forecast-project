# CRON JOB FOR WEST BENGAL WEATHER PARAMETER

# GOOGLE DRIVE AND SERVICE ACCOUNT INTEGRATION

Every 1AM the GitHub triggers the code and workflow job it takes the data, modify it, push it to Drive 

GitHub Repository

        │
        ▼
GitHub Actions starts automatically

        │
        ▼
Installs Python and required packages

        │
        ▼
Creates service_account.json from GitHub Secret

        │
        ▼
Runs your Python script

        │
        ▼
Downloads/updates weather data

        │
        ▼
Uploads the updated JSON back to Google Drive

        │
        ▼
Workflow finishes

PROCEDURE FOR THE WORKFLOW 
-----------------------------------------------------------------------------------------
a) Take the Data first time and save it to google drive
b) Create a service account in GOOGLE CLOUD CONSOLE
c) after creating keys and dummy email give permission to the specific folder to access
d) write the connection code and updating code in python  
e) setup GitHub and add the files under folders and set it for workflows
f) run the workflow for once then let it run itself at a particular time 

FILE STRUCTURE 
-------------------------------
weather-cron-job

| ----requirements.txt

| ----update_weather_data.py

| ----westbengal_cities.json

| ----weather-project-XXXXXX-XXXXXX.json (Hidden, gitignore, shouldn't be uploaded)

SERVICE ACCOUNT CREATION
---------------------------------------------------------------------------------------------------------------
service account is created cause it will act as a bot mail to fetch the data and change the drive file for us 

1. Open https://console.cloud.google.com/
2. Sign in with your Google account.
3. Click the Project drop-down at the top.
4. Click "New Project".
5. Enter a project name (e.g., weather-project).
6. Click "Create".
7. Select the newly created project.
8. From the left menu, go to:
   APIs & Services → Library
9. Search for "Google Drive API".
10. Open Google Drive API and click "Enable".
11. (Optional) If you will use Google Sheets, search for "Google Sheets API" and click "Enable".
12. From the left menu, go to:
    IAM & Admin → Service Accounts
13. Click "Create Service Account".
14. Enter a Service Account Name (e.g., weather-data-bot).
15. Click "Create and Continue".
16. Choose a role (e.g., Basic → Editor).
17. Click "Continue".
18. Skip the optional user access section by clicking "Done".
19. In the Service Accounts list, click the newly created service account.
20. Open the "Keys" tab.
21. Click "Add Key".
22. Select "Create New Key".
23. Choose "JSON" as the key type.
24. Click "Create".
25. The JSON key file will automatically download to your computer.
26. Move the downloaded JSON file into your project folder.
27. Keep this JSON file private and never upload it to GitHub or share it publicly.

PERMISSION FOR A SPECIFIC FILE TO SERVICE ACCOUNT
--------------------------------------------------------------
1. Open Google Drive.
2. Locate the file you want the service account to access.
3. Right-click the file.
4. Click "Share".
5. In the "Add people and groups" field, enter the service account email address.
   Example:
   weather-data-bot@weather-project-xXXXXX.iam.gserviceaccount.com
6. Select the appropriate permission:
   - Viewer (read only)
   - Commenter
   - Editor (read and update the file)
7. Click "Send" or "Share".
8. Wait a few seconds for the permissions to be applied.
9. In your Python code, use the file's Google Drive File ID to access the file.
10. The service account can now read or modify that specific file according to the permission you granted. 

SETTING UP GITHUB ACTION AND UPLOADING STUFFS
-------------------------------------------------------------------
1. Create a new repository on GitHub.
2. Upload your project files, for example:
   - update_weather_data.py
   - requirements.txt
   - westbengal_cities.json
   - Any other required files
3. Do NOT upload the service account JSON file.
4. Open your GitHub repository.
5. Go to:
   Settings → Secrets and variables → Actions
6. Click "New repository secret".
7. Enter the secret name:
   GCP_SERVICE_ACCOUNT
8. Open your downloaded service account JSON file in a text editor.
9. Copy the ENTIRE contents of the JSON file.
10. Paste the copied JSON into the "Secret" value box.
11. Click "Add secret".
12. In your project, create the following folder structure using GitHub(do not upload it):
   .github/
       workflows/
           update.yml
13. Inside update.yml, add your GitHub Actions workflow code(consult cgpt)
14. In the workflow, create the JSON file from the secret using:
   echo '${{ secrets.GOOGLE_CREDENTIALS }}' > service_account.json
15. Use "service_account.json" in your Python code as the credentials file.
16. Commit and push all project files (except the JSON key).
17. Open the GitHub repository.
18. Go to the "Actions" tab.
19. Select your workflow.
20. Click "Run workflow" if it uses workflow_dispatch, or wait for the scheduled time if it runs automatically.
21. Check the workflow logs to verify that the script executed successfully.
22. See the error logs and verify it 

weather-project-XXXXXX-XXXXXX.json FILE CONTENT
-------------------------------------------------------
This is a content when you will download the service account json
You will also find the service mail over there 
settings -> secret and variables you will find there

MY UPDATE.YML CODE
-----------------------------------------------------------------------------------

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
        echo '${{ secrets.GCP_SERVICE_ACCOUNT }}' > weather-project-503316-7928a8a4716c.json

    - name: Run Weather Script
      run: |
        python update_weather_data.py
