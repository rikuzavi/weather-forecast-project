import io
import json
import pandas as pd
import requests
import time
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

SERVICE_ACCOUNT_FILE = "weather-project-service-account.json"
FILE_LINK = "https://drive.google.com/file/d/1-SCP57A_QOQn0vFpoovMMQlEYDEJevsf/view?usp=drive_link"
FILE_ID = "1-SCP57A_QOQn0vFpoovMMQlEYDEJevsf"
# Authenticate
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=creds)
# getting data
def getdata():
    # Download file
    request = service.files().get_media(fileId=FILE_ID)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)

    # Load JSON
    data = json.load(fh)
    return data

# df_output is the output file
df_output = getdata()

ist = ZoneInfo("Asia/Kolkata")
yesterday = (datetime.now(ist) - timedelta(days=1)).strftime("%Y-%m-%d")
print(yesterday)
df = pd.read_json("./westbengal_cities.json")
for city in df:

    lat = df[city]["lat"]
    lon = df[city]["lon"]

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&start_date={yesterday}"
        f"&end_date={yesterday}"
        f"&hourly="
        f"temperature_2m,"
        f"relative_humidity_2m,"
        f"dew_point_2m,"
        f"surface_pressure,"
        f"precipitation,"
        f"rain,"
        f"snowfall,"
        f"cloud_cover,"
        f"wind_speed_10m,"
        f"wind_gusts_10m,"
        f"wind_direction_10m,"
        f"shortwave_radiation"
        f"&timezone=auto"
    )

    try:
        res = requests.get(url, timeout=60)
        if res.status_code != 200:
            print(f"{city}: Failed ({res.status_code})")
            continue

        hourly = res.json()["hourly"]
        # Every hourly variable
        # print(hourly)
        for key in df_output[city]["daily"]:
            # Append new data
            df_output[city]["daily"][key].extend(hourly[key])

            # Remove oldest 24 hours
            df_output[city]["daily"][key] = df_output[city]["daily"][key][24:]

        print(f"✓ {city}")

    except Exception as e:
        print('problem',city, e)

print('waiting to upload')

upload_buffer = io.BytesIO(
    json.dumps(df_output).encode("utf-8")
)
upload_buffer.seek(0)

media = MediaIoBaseUpload(
    upload_buffer,
    mimetype="application/json",
    resumable=True
)

for attempt in range(5):
    try:
        request = service.files().update(
            fileId=FILE_ID,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()

        print("Upload completed.")
        break

    except Exception as e:
        print(f"Upload attempt {attempt+1} failed:", e)

        if attempt == 4:
            raise

        time.sleep(10)
