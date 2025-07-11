import pandas as pd
import numpy as np
import os
from pathlib import Path

# --- SEKCJA KONFIGURACJI ---

# 1. Ścieżka do głównego folderu z danymi
BASE_PATH = Path("D:/football_data")

# 2. Folder, w którym będą zapisywane wyniki analizy
# Zmieniamy to, aby było bardziej elastyczne
# OUTPUT_PATH = BASE_PATH / "wyniki_analizy_remisow" # Usunięto

# 3. Liczba ostatnich sezonów do analizy
X_SEASONS = 5 

# 4. Struktura państw i lig
COUNTRIES_LEAGUES = {
    "England": ["E0", "E1", "E2"],
    "Germany": ["D1", "D2"], # Usunięto D3, gdyż często brakuje danych
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

# 5. Aktualny sezon (do wygenerowania listy sezonów do analizy)
# Zakładamy format ROK/ROK+1
CURRENT_SEASON_END_YEAR = 2025


# --- FUNKCJE ANALITYCZNE ---

def get_seasons_to_analyze(last_season_end_year, num_seasons):
    """Generuje listę nazw folderów sezonów do analizy."""
    seasons = []
    for i in range(num_seasons):
        start_year = last_season_end_year - 1 - i
        end_year = last_season_end_year - i
        # Format folderu: 2023-2024
        seasons.append(f"{start_year}-{end_year}")
    return seasons

def calculate_team_stats(team_df, team_name):
    """
    Oblicza wszystkie wymagane statystyki dla jednej drużyny na podstawie jej meczów.
    """
    if team_df.empty:
        return None

    # Podstawowe statystyki
    total_matches = len(team_df)
    draws_df = team_df[team_df['FTR'] == 'D']
    total_draws = len(draws_df)
    draw_percentage = (total_draws / total_matches) * 100 if total_matches > 0 else 0

    # Analiza serii bez remisu
    team_df['is_draw'] = team_df['FTR'] == 'D'
    # Tworzymy grupy kolejnych takich samych wartości (remis / brak remisu)
    team_df['streak_group'] = (team_df['is_draw'] != team_df['is_draw'].shift()).cumsum()
    
    streak_counts = team_df.groupby('streak_group')['is_draw'].agg(['count', 'first'])
    
    no_draw_streaks = streak_counts[streak_counts['first'] == False]['count']

    longest_streak_no_draw = no_draw_streaks.max() if not no_draw_streaks.empty else 0
    avg_streak_no_draw = no_draw_streaks.mean() if not no_draw_streaks.empty else 0
    
    # Aktualna seria bez remisu (NAJWAŻNIEJSZY WSKAŹNIK DLA PROGRESJI)
    current_streak_no_draw = 0
    if not team_df.empty:
        # Sprawdzamy od ostatniego meczu wstecz
        last_match = team_df.iloc[-1]
        if not last_match['is_draw']:
            last_draw_index = team_df[team_df['is_draw']].index.max()
            if pd.notna(last_draw_index):
                current_streak_no_draw = len(team_df.loc[last_draw_index:].iloc[1:])
            else: # Nigdy nie zremisowała w analizowanym okresie
                current_streak_no_draw = total_matches

    # Stałość remisowania (odchylenie standardowe % remisów na sezon)
    seasonal_stats = team_df.groupby('Season').apply(
        lambda s: (s['is_draw'].sum() / len(s)) * 100 if len(s) > 0 else 0
    ).rename('draw_percentage')
    
    draw_consistency_std_dev = seasonal_stats.std()

    # Trend remisów (nachylenie linii regresji)
    seasonal_stats_df = seasonal_stats.reset_index()
    # Przekształcamy '2023-24' w numeryczną wartość, np. 2023
    seasonal_stats_df['season_numeric'] = seasonal_stats_df['Season'].apply(lambda s: int(s.split('-')[0]))
    
    # Obliczamy trend tylko jeśli mamy co najmniej 2 sezony
    draw_trend_slope = 0.0
    if len(seasonal_stats_df) > 1:
        # y = mx + c, gdzie 'm' to nachylenie (slope)
        m, c = np.polyfit(seasonal_stats_df['season_numeric'], seasonal_stats_df['draw_percentage'], 1)
        draw_trend_slope = m

    return {
        'Team': team_name,
        'Total Matches': total_matches,
        'Total Draws': total_draws,
        'Draw Percentage (%)': round(draw_percentage, 2),
        'Current Streak Without Draw': current_streak_no_draw,
        'Longest Streak Without Draw': longest_streak_no_draw,
        'Average Streak Without Draw': round(avg_streak_no_draw, 2),
        'Draw Consistency (Std Dev %)': round(draw_consistency_std_dev, 2),
        'Draw Trend (Slope)': round(draw_trend_slope, 4)
    }


def analyze_league(country, league_code, seasons_list, output_base_path): # Dodano output_base_path
    """
    Główna funkcja, która wczytuje dane dla ligi, przetwarza je i zapisuje wyniki.
    """
    print(f"\n--- Analizuję ligę: {country} - {league_code} dla {len(seasons_list)} sezonów ---")
    
    all_league_data = []
    for season in seasons_list:
        # Dostosowujemy nazwę kraju do ścieżki (np. Netherlands -> Netherlands)
        file_path = BASE_PATH / season / country / f"{league_code}.csv"
        
        if not file_path.exists():
            print(f"Ostrzeżenie: Plik nie istnieje: {file_path}")
            continue
            
        try:
            # Używamy różnych kodowań, bo stare pliki mogą mieć inne
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1')
            
            # Ważne: dodajemy kolumnę z sezonem
            df['Season'] = season
            all_league_data.append(df)
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku {file_path}: {e}")

    if not all_league_data:
        print(f"Nie znaleziono żadnych danych dla ligi {league_code}. Przechodzę do następnej.")
        return

    master_df = pd.concat(all_league_data, ignore_index=True)
    
    # Upewniamy się, że kolumna Date istnieje i sortujemy po niej dane
    if 'Date' in master_df.columns:
        master_df['Date'] = pd.to_datetime(master_df['Date'], dayfirst=True, errors='coerce')
        master_df = master_df.sort_values(by='Date').reset_index(drop=True)
    else:
        print(f"Ostrzeżenie: Brak kolumny 'Date' w danych dla {league_code}. Chronologia może być niepoprawna.")


    # Znajdujemy wszystkie unikalne drużyny w analizowanym okresie
    home_teams = master_df['HomeTeam'].unique()
    away_teams = master_df['AwayTeam'].unique()
    all_teams = pd.unique(np.concatenate((home_teams, away_teams)))

    league_results = []
    for team in all_teams:
        team_df = master_df[(master_df['HomeTeam'] == team) | (master_df['AwayTeam'] == team)].copy()
        team_stats = calculate_team_stats(team_df, team)
        if team_stats:
            league_results.append(team_stats)
    
    if not league_results:
        print(f"Nie udało się wygenerować statystyk dla ligi {league_code}.")
        return

    # Tworzymy DataFrame z wynikami i sortujemy
    results_df = pd.DataFrame(league_results)
    # Sortujemy malejąco wg kluczowych wskaźników dla progresji:
    # 1. Aktualna seria bez remisu (im dłuższa, tym lepiej)
    # 2. Ogólny procent remisów (im wyższy, tym większa skłonność drużyny do remisów)
    results_df = results_df.sort_values(by=['Current Streak Without Draw', 'Draw Percentage (%)'], ascending=[False, False])
    
    # Tworzymy ścieżkę do zapisu uwzględniającą kraj
    output_country_path = output_base_path / country
    output_country_path.mkdir(parents=True, exist_ok=True) # Tworzymy folder kraju

    # Zapisujemy wyniki do pliku CSV
    output_filename = f"{country}_{league_code}_analiza_remisow.csv"
    output_filepath = output_country_path / output_filename # Zmieniamy ścieżkę zapisu
    results_df.to_csv(output_filepath, index=False)
    
    print(f"✅ Analiza zakończona. Wyniki zapisano w: {output_filepath}")


# --- GŁÓWNA PĘTLA WYKONAWCZA ---

if __name__ == "__main__":
    # Nowa ścieżka bazowa dla wyników analizy
    # D:/football_data/analiza_1/ostatnie_X_sezonow
    ANALYSIS_OUTPUT_BASE_PATH = BASE_PATH / "analiza_1" / f"ostatnie_{X_SEASONS}_sezonow"
    
    # Utwórz folder na wyniki, jeśli nie istnieje
    ANALYSIS_OUTPUT_BASE_PATH.mkdir(parents=True, exist_ok=True)
    
    seasons = get_seasons_to_analyze(CURRENT_SEASON_END_YEAR, X_SEASONS)
    print(f"Rozpoczynam analizę dla sezonów: {seasons}")
    
    for country, leagues in COUNTRIES_LEAGUES.items():
        for league in leagues:
            # Przekazujemy nową ścieżkę bazową do funkcji analyze_league
            analyze_league(country, league, seasons, ANALYSIS_OUTPUT_BASE_PATH)
            
    print("\n\n--- Wszystkie analizy zostały zakończone! ---")