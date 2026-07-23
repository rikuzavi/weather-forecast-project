import io
import json
import requests

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


input_file = "westbengal_cities.json"
# input_file = f"/content/drive/MyDrive/weather_project/{cities}"
df = pd.read_json(input_file)


output_file = "westbengal_param.json"
# output_file = f"/content/drive/MyDrive/weather_project/{output}"
with open(output_file, "r", encoding="utf-8") as f:
    df_output = json.load(f)

ist = ZoneInfo("Asia/Kolkata")
yesterday = (datetime.now(ist) - timedelta(days=1)).strftime("%Y-%m-%d")
print(yesterday)
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

# Save updated file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(df_output, f, indent=4)
