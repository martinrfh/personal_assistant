import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")
CITY_NAME = "Bandar-e Anzali"
BASE_URL = "http://api.weatherapi.com/v1"


def get_weather(target_time="today"):
    url = f"{BASE_URL}/forecast.json"
    params = {
        "key": API_KEY,
        "q": CITY_NAME,
        "days": 2
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        index = 0 if target_time == "today" else 1 if target_time == "tomorrow" else None
        if index is None:
            raise ValueError(
                "Invalid target time. Use 'today' or 'tomorrow'.")

        day = data["forecast"]["forecastday"][index]["day"]
        return {
            "weather_condition": day.get("condition", {}).get("text", "Unknown"),
            "average_temperature": day.get("avgtemp_c", 0.0),
            "maximum_temperature": day.get("maxtemp_c", 0.0),
            "minimum_temperature": day.get("mintemp_c", 0.0),
            "chance_of_rain_percent": day.get("daily_chance_of_rain", 0)
        }

    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
    except (KeyError, IndexError, ValueError) as e:
        print(f"[ERROR] Data parsing failed: {e}")

    return {}


if __name__ == "__main__":
    weather = get_weather('sunday')
    print(weather)
