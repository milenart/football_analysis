import os
import pandas as pd

# Ścieżka do folderu "Ligi" w katalogu projektu
BASE_DIR = os.path.join(os.getcwd(), "Ligi")

# Skróty do identyfikacji nazw plików
LEAGUE_PREFIXES = ["eng", "esp", "ger", "ita", "fra", "por"]

# Wczytywanie danych z plików CSV w podanym zakresie sezonów
def load_match_data(start_season, end_season):
    data = []
    for folder in os.listdir(BASE_DIR):
        folder_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        for file in os.listdir(folder_path):
            if file.endswith(".csv"):
                for prefix in LEAGUE_PREFIXES:
                    if file.startswith(prefix):
                        season = file[len(prefix):-4]
                        if start_season <= season <= end_season:
                            file_path = os.path.join(folder_path, file)
                            try:
                                df = pd.read_csv(file_path)
                                df = df[["HomeTeam", "AwayTeam", "FTR"]].dropna()
                                data.append(df)
                            except Exception as e:
                                print(f"❌ Błąd wczytywania {file}: {e}")
    return pd.concat(data, ignore_index=True) if data else pd.DataFrame()

# Obliczanie liczby remisów i meczów każdej drużyny
def analyze_draws(df):
    teams = {}
    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        result = row["FTR"]

        for team in [home, away]:
            if team not in teams:
                teams[team] = {"draws": 0, "matches": 0}

        teams[home]["matches"] += 1
        teams[away]["matches"] += 1

        if result == "D":
            teams[home]["draws"] += 1
            teams[away]["draws"] += 1

    summary = []
    for team, stats in teams.items():
        matches = stats["matches"]
        draws = stats["draws"]
        if matches > 0:
            percent = 100 * draws / matches
            summary.append((team, percent, draws, matches))

    summary.sort(key=lambda x: x[1], reverse=True)
    return summary

# Główna funkcja programu
def main():
    print("📅 Podaj zakres sezonów do analizy (np. 08/09)")
    start = input("Początkowy sezon (np. 08/09): ")
    end = input("Końcowy sezon (np. 17/18): ")
    top_n = int(input("Ile drużyn chcesz wyświetlić?: "))

    print("\n📥 Wczytywanie danych...")
    df = load_match_data(start, end)

    if df.empty:
        print("❌ Brak danych dla podanego zakresu.")
        return

    print("📊 Analiza remisów...")
    results = analyze_draws(df)

    print(f"\n🔝 Top {top_n} drużyn z największym odsetkiem remisów ({start}–{end}):\n")
    print(f"{'Drużyna':<25} {'% remisów':>10} {'Remisy':>10} {'Mecze':>10}")
    print("-" * 60)
    for team, percent, draws, matches in results[:top_n]:
        print(f"{team:<25} {percent:>10.2f} {draws:>10} {matches:>10}")

if __name__ == "__main__":
    main()
