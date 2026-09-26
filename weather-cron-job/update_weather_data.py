import io
import json
import time
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import (
    MediaIoBaseDownload,
    MediaIoBaseUpload
)


# ============================================================
# CONFIGURATION
# ============================================================

SERVICE_ACCOUNT_FILE = "weather-project-service-account.json"

FILE_ID = "12Eijy87QCseHV7kH82gKcXRDcMFbxnCv"

INDIA_CITIES_FILE = "india_cities.json"


# ============================================================
# GOOGLE DRIVE AUTHENTICATION
# ============================================================

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=[
        "https://www.googleapis.com/auth/drive"
    ]
)

service = build(
    "drive",
    "v3",
    credentials=creds
)


# ============================================================
# READ DATA FROM GOOGLE DRIVE
# ============================================================

def getdata():

    print("Reading data from Google Drive...")

    request = service.files().get_media(
        fileId=FILE_ID
    )

    fh = io.BytesIO()

    downloader = MediaIoBaseDownload(
        fh,
        request
    )

    done = False

    while not done:

        status, done = downloader.next_chunk()

        if status:
            print(
                f"Download progress: "
                f"{int(status.progress() * 100)}%"
            )

    fh.seek(0)

    data = json.load(fh)

    print("Data loaded successfully.")

    return data


# ============================================================
# GET YESTERDAY'S DATE
# ============================================================

ist = ZoneInfo("Asia/Kolkata")

yesterday = (
    datetime.now(ist) - timedelta(days=1)
).strftime("%Y-%m-%d")

print()
print("Updating data for:", yesterday)
print()


# ============================================================
# LOAD EXISTING WEATHER DATA
# ============================================================

df_output = getdata()


# ============================================================
# LOAD CITY COORDINATES
# ============================================================

print("Reading city coordinates...")

df = pd.read_json(
    INDIA_CITIES_FILE
)

print(
    f"Found {len(df.columns)} cities."
)

print()


# ============================================================
# UPDATE EACH CITY
# ============================================================

for city in df:

    try:

        # ----------------------------------------------------
        # GET LATITUDE AND LONGITUDE
        # ----------------------------------------------------

        lat = df[city]["lat"]
        lon = df[city]["lon"]

        print(
            f"Processing {city}..."
        )


        # ----------------------------------------------------
        # OPEN-METEO URL
        # ----------------------------------------------------

        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&start_date={yesterday}"
            f"&end_date={yesterday}"
            "&hourly="
            "temperature_2m,"
            "relative_humidity_2m,"
            "dew_point_2m,"
            "surface_pressure,"
            "precipitation,"
            "rain,"
            "snowfall,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "wind_direction_10m,"
            "shortwave_radiation"
            "&timezone=auto"
        )


        # ----------------------------------------------------
        # REQUEST WITH RETRIES
        # ----------------------------------------------------

        success = False

        for attempt in range(3):

            try:

                response = requests.get(
                    url,
                    timeout=60
                )

                if response.status_code == 200:

                    success = True
                    break

                else:

                    print(
                        f"{city}: "
                        f"HTTP {response.status_code}"
                    )

            except requests.exceptions.Timeout:

                print(
                    f"{city}: "
                    f"Timeout "
                    f"(attempt {attempt + 1}/3)"
                )

            except requests.exceptions.RequestException as e:

                print(
                    f"{city}: "
                    f"Request error "
                    f"(attempt {attempt + 1}/3): "
                    f"{e}"
                )

            # Wait before retry

            if attempt < 2:

                time.sleep(5)


        # ----------------------------------------------------
        # SKIP CITY IF ALL RETRIES FAILED
        # ----------------------------------------------------

        if not success:

            print(
                f"✗ {city}: "
                "Failed after 3 attempts"
            )

            continue


        # ----------------------------------------------------
        # GET JSON RESPONSE
        # ----------------------------------------------------

        hourly = response.json()["hourly"]


        # ----------------------------------------------------
        # UPDATE WEATHER ARRAYS
        # ----------------------------------------------------

        for key in df_output[city]["daily"]:

            # Add yesterday's 24 hours

            df_output[city]["daily"][key].extend(
                hourly[key]
            )


            # Remove oldest 24 hours

            df_output[city]["daily"][key] = (
                df_output[city]["daily"][key][24:]
            )


        print(
            f"✓ {city}"
        )


    except Exception as e:

        print(
            f"Problem with {city}: {e}"
        )

        continue


# ============================================================
# WEATHER UPDATE FINISHED
# ============================================================

print()
print("Weather update completed.")
print()


# ============================================================
# CONVERT JSON TO MEMORY
# ============================================================

json_data = json.dumps(
    df_output,
    ensure_ascii=False
)


# ============================================================
# UPLOAD UPDATED DATA TO GOOGLE DRIVE
# ============================================================

print(
    "Uploading updated data to Google Drive..."
)


media = MediaIoBaseUpload(
    io.BytesIO(
        json_data.encode("utf-8")
    ),
    mimetype="application/json",
    resumable=True
)


# ============================================================
# UPLOAD WITH RETRIES
# ============================================================

upload_success = False

for attempt in range(5):

    try:

        service.files().update(
            fileId=FILE_ID,
            media_body=media
        ).execute()

        upload_success = True

        print(
            "Upload completed successfully."
        )

        break


    except Exception as e:

        print(
            f"Upload attempt "
            f"{attempt + 1}/5 failed:"
        )

        print(e)

        if attempt < 4:

            print(
                "Retrying in 10 seconds..."
            )

            time.sleep(10)


# ============================================================
# FINAL STATUS
# ============================================================

if not upload_success:

    print(
        "ERROR: Failed to upload "
        "updated data to Google Drive."
    )

    raise Exception(
        "Google Drive upload failed."
    )


print()
print("Weather data update finished successfully.")
