import os
import requests

TARGET_DIR = "D:/football_data"
START_YEAR = 2000
END_YEAR = 2024

# Najpopularniejsze ligi dla danego kraju
TOP_LEAGUES = {
    "England": ["E0", "E1", "E2"],
    "Germany": ["D1", "D2", "D3"],
    "Italy": ["I1", "I2"],
    "Spain": ["SP1", "SP2"],
    "France": ["F1", "F2"],
    "Scotland": ["SC0", "SC1", "SC2"],
    "Netherlands": ["N1"],
    "Belgium": ["B1"],
    "Portugal": ["P1"],
    "Turkey": ["T1"],
    "Greece": ["G1"]
}

def download_csv(url, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Pobrano: {url}")
        else:
            print(f"Brak pliku: {url}")
    except Exception as e:
        print(f"Błąd przy pobieraniu {url}: {e}")

def main():
    for year in range(END_YEAR, START_YEAR - 1, -1):
        next_year = year + 1
        season_code = f"{str(year)[-2:]}{str(next_year)[-2:]}"  # np. '2324'
        season_folder = f"{year}-{next_year}"                   # np. '2023-2024'

        for country, leagues in TOP_LEAGUES.items():
            for league_code in leagues:
                url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{league_code}.csv"
                save_path = os.path.join(TARGET_DIR, season_folder, country, f"{league_code}.csv")
                download_csv(url, save_path)

if __name__ == "__main__":
    main()
