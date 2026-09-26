import json
import pandas as pd
import requests
import time

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from huggingface_hub import login, hf_hub_download, HfApi


# ============================================================
# HUGGING FACE CONFIGURATION
# ============================================================

HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

REPO_ID = "YOUR_USERNAME/weather-data"

FILE_NAME = "india_param.json"


# Login to Hugging Face
login(HF_TOKEN)

api = HfApi()


# ============================================================
# GET DATA FROM HUGGING FACE
# ============================================================

def getdata():

    print("Reading data from Hugging Face...")

    file_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILE_NAME,
        repo_type="dataset",
        token=HF_TOKEN
    )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Data loaded successfully.")

    return data


# ============================================================
# LOAD EXISTING WEATHER DATA
# ============================================================

df_output = getdata()


# ============================================================
# YESTERDAY DATE
# ============================================================

ist = ZoneInfo("Asia/Kolkata")

yesterday = (
    datetime.now(ist) - timedelta(days=1)
).strftime("%Y-%m-%d")

print("Updating data for:", yesterday)


# ============================================================
# READ CITY COORDINATES
# ============================================================

df = pd.read_json("./india_cities.json")


# ============================================================
# GET WEATHER DATA FOR EACH CITY
# ============================================================

for city in df:

    try:

        lat = df[city]["lat"]
        lon = df[city]["lon"]

        print(f"Processing {city}...")


        # ----------------------------------------------------
        # OPEN-METEO ARCHIVE URL
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # REQUEST DATA
        # ----------------------------------------------------

        res = requests.get(
            url,
            timeout=60
        )


        if res.status_code != 200:

            print(
                f"{city}: Failed "
                f"({res.status_code})"
            )

            continue


        hourly = res.json()["hourly"]


        # ----------------------------------------------------
        # UPDATE CITY DATA
        # ----------------------------------------------------

        for key in df_output[city]["daily"]:

            # Add new 24 hours
            df_output[city]["daily"][key].extend(
                hourly[key]
            )

            # Keep only the required amount
            # Remove oldest 24 hours
            df_output[city]["daily"][key] = (
                df_output[city]["daily"][key][24:]
            )


        print(f"✓ {city}")


    except Exception as e:

        print(
            f"Problem with {city}:",
            e
        )


# ============================================================
# SAVE UPDATED JSON
# ============================================================

print("Weather update completed.")

print("Preparing file for upload...")


with open(
    FILE_NAME,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        df_output,
        f,
        ensure_ascii=False
    )


# ============================================================
# UPLOAD TO HUGGING FACE
# ============================================================

print("Uploading to Hugging Face...")


for attempt in range(5):

    try:

        api.upload_file(

            path_or_fileobj=FILE_NAME,

            path_in_repo=FILE_NAME,

            repo_id=REPO_ID,

            repo_type="dataset",

            commit_message="Update weather data"

        )


        print("Upload completed successfully.")

        break


    except Exception as e:

        print(
            f"Upload attempt "
            f"{attempt + 1} failed:",
            e
        )


        if attempt == 4:

            raise


        time.sleep(10)
