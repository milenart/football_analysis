import pandas as pd
import numpy as np
import os
from pathlib import Path

# --- SEKCJA KONFIGURACJI ---

# 1. Ścieżka do głównego folderu z danymi
BASE_PATH = Path("D:/football_data")

# 2. Folder bazowy dla wyników symulacji
SIMULATION_OUTPUT_BASE_PATH = BASE_PATH / "symulacja_1"

# 3. Liczba ostatnich sezonów do analizy
X_SEASONS = 24 

# 4. Struktura państw i lig
COUNTRIES_LEAGUES = {
    "England": ["E0", "E1"], # Ograniczyłem dla szybszego testowania, możesz rozszerzyć
    "Germany": ["D1"], 
    "Italy": ["I1"],
    "Spain": ["SP1"],
    "France": ["F1"],
    "Scotland": ["SC0"],
    "Netherlands": ["N1"],
    "Belgium": ["B1"],
    "Portugal": ["P1"],
    "Turkey": ["T1"],
    "Greece": ["G1"]
}

# 5. Aktualny sezon (do wygenerowania listy sezonów do analizy)
CURRENT_SEASON_END_YEAR = 2025

# 6. Konfiguracja symulacji
FIBONACCI_START_UNIT = 1
FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946] # Możesz rozszerzyć
DRAW_ODDS = 3.0 # Stały kurs na remis

# --- FUNKCJE POMOCNICZE ---

def get_seasons_to_analyze(last_season_end_year, num_seasons):
    """Generuje listę nazw folderów sezonów do analizy."""
    seasons = []
    for i in range(num_seasons):
        start_year = last_season_end_year - 1 - i
        end_year = last_season_end_year - i
        seasons.append(f"{start_year}-{end_year}")
    return seasons

def simulate_fibonacci_progression(team_matches, fib_sequence, draw_odds):
    """
    Symuluje progresję Fibonacciego dla danej drużyny.
    Zwraca zysk/stratę, liczbę iteracji i maksymalny potrzebny kapitał.
    """
    current_bet_index = 0
    total_spent = 0
    total_profit_loss = 0
    max_capital_needed = 0
    games_in_progression = 0

    for _, match in team_matches.iterrows():
        games_in_progression += 1
        
        # Sprawdzamy, czy w ciągu Fibonacciego są jeszcze kroki
        if current_bet_index >= len(fib_sequence):
            # Jeśli zabraknie kroków, traktujemy to jako potencjalnie nieskończoną stratę
            # lub po prostu kończymy symulację, odnotowując stratę do tego momentu
            # Dla celów tej symulacji zakładamy "nieskończony majatek", więc kontynuujemy
            # z ostatnią dostępną stawką Fibonacciego.
            current_stake = fib_sequence[-1] 
        else:
            current_stake = fib_sequence[current_bet_index]
        
        total_spent += current_stake
        max_capital_needed = max(max_capital_needed, current_stake)

        if match['FTR'] == 'D':
            # Remis - zakład wygrany
            profit = current_stake * (draw_odds - 1) # Zysk netto
            total_profit_loss += profit - (total_spent - current_stake) # Zysk minus poprzednie straty
            return games_in_progression, total_profit_loss, max_capital_needed, "Win"
        else:
            # Brak remisu - zakład przegrany, przechodzimy do kolejnego kroku Fibonacciego
            current_bet_index += 1
            
    # Jeśli sezon się skończył i nie było remisu
    total_profit_loss = -total_spent
    return games_in_progression, total_profit_loss, max_capital_needed, "Loss"


def analyze_and_simulate_league(country, league_code, seasons_list):
    """
    Główna funkcja, która wczytuje dane dla ligi, przetwarza je i uruchamia symulacje.
    """
    print(f"\n--- Symuluję ligę: {country} - {league_code} dla {len(seasons_list)} sezonów ---")
    
    all_simulation_results = []

    for season in seasons_list:
        file_path = BASE_PATH / season / country / f"{league_code}.csv"
        
        if not file_path.exists():
            print(f"Ostrzeżenie: Plik nie istnieje: {file_path}")
            continue
            
        try:
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1')
            
            df['Season'] = season
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                df = df.sort_values(by='Date').reset_index(drop=True)
            else:
                print(f"Ostrzeżenie: Brak kolumny 'Date' w danych dla {league_code}. Chronologia może być niepoprawna.")
                continue

            # --- Przygotowanie danych dla drużyn ---
            team_match_data = {}
            for team in pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel()):
                team_df = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].copy()
                team_match_data[team] = team_df.sort_values(by='Date').reset_index(drop=True)
            
            if not team_match_data:
                print(f"Brak danych meczowych dla ligi {league_code} w sezonie {season}.")
                continue

            # --- Znajdowanie punktu 50% meczów dla każdej drużyny ---
            teams_mid_season_stats = []
            for team_name, team_df in team_match_data.items():
                total_team_matches = len(team_df)
                if total_team_matches == 0:
                    continue

                half_season_matches_count = total_team_matches // 2
                
                # Upewniamy się, że mamy co najmniej jeden mecz do analizy
                if half_season_matches_count == 0: 
                    #print(f"Ostrzeżenie: Drużyna {team_name} w sezonie {season} ma za mało meczów ({total_team_matches}) do analizy połowy sezonu.")
                    continue

                mid_season_df = team_df.head(half_season_matches_count)
                
                # Obliczanie statystyk do połowy sezonu
                num_draws = len(mid_season_df[mid_season_df['FTR'] == 'D'])
                num_wins = len(mid_season_df[((mid_season_df['HomeTeam'] == team_name) & (mid_season_df['FTR'] == 'H')) | ((mid_season_df['AwayTeam'] == team_name) & (mid_season_df['FTR'] == 'A'))])
                num_losses = len(mid_season_df[((mid_season_df['HomeTeam'] == team_name) & (mid_season_df['FTR'] == 'A')) | ((mid_season_df['AwayTeam'] == team_name) & (mid_season_df['FTR'] == 'H'))])
                
                draw_percent = (num_draws / half_season_matches_count) * 100 if half_season_matches_count > 0 else 0
                win_percent = (num_wins / half_season_matches_count) * 100 if half_season_matches_count > 0 else 0
                loss_percent = (num_losses / half_season_matches_count) * 100 if half_season_matches_count > 0 else 0

                # Obliczanie aktualnej serii bez porażki do połowy sezonu
                current_unbeaten_streak = 0
                for i in range(half_season_matches_count - 1, -1, -1):
                    match = mid_season_df.iloc[i]
                    if (match['HomeTeam'] == team_name and match['FTR'] == 'A') or \
                       (match['AwayTeam'] == team_name and match['FTR'] == 'H'):
                        # To była porażka
                        break
                    current_unbeaten_streak += 1


                teams_mid_season_stats.append({
                    'Team': team_name,
                    'MatchesToMidSeason': half_season_matches_count,
                    'DrawPercent': draw_percent,
                    'UnbeatenStreak': current_unbeaten_streak,
                    'WinPercent': win_percent,
                    'LossPercent': loss_percent,
                    'StartIndex': half_season_matches_count # Indeks pierwszego meczu w progresji
                })

            teams_mid_season_df = pd.DataFrame(teams_mid_season_stats)
            if teams_mid_season_df.empty:
                print(f"Brak wystarczających danych do obliczenia statystyk połowy sezonu dla ligi {league_code} w sezonie {season}.")
                continue


            # --- Wybór Top 3 drużyn dla każdego scenariusza i symulacja ---
            
            # Scenariusz 1: Najniższy procent remisów
            if not teams_mid_season_df.empty:
                top3_lowest_draw = teams_mid_season_df.sort_values(by='DrawPercent', ascending=True).head(3)
                for _, row in top3_lowest_draw.iterrows():
                    team_name = row['Team']
                    start_index = row['StartIndex']
                    sim_team_df = team_match_data[team_name].iloc[start_index:]
                    games_in_prog, profit, max_cap, outcome = simulate_fibonacci_progression(sim_team_df, FIBONACCI_SEQUENCE, DRAW_ODDS)
                    all_simulation_results.append({
                        'Season': season,
                        'Scenario': 'Lowest Draw %',
                        'Team': team_name,
                        'Matches To 50% Mark': row['MatchesToMidSeason'],
                        'Games In Progression': games_in_prog,
                        'Outcome': outcome,
                        'Profit/Loss (Units)': round(profit, 2),
                        'Max Capital Needed (Units)': max_cap
                    })

            # Scenariusz 2: Najdłuższa seria bez porażki
            if not teams_mid_season_df.empty:
                top3_longest_unbeaten = teams_mid_season_df.sort_values(by='UnbeatenStreak', ascending=False).head(3)
                for _, row in top3_longest_unbeaten.iterrows():
                    team_name = row['Team']
                    start_index = row['StartIndex']
                    sim_team_df = team_match_data[team_name].iloc[start_index:]
                    games_in_prog, profit, max_cap, outcome = simulate_fibonacci_progression(sim_team_df, FIBONACCI_SEQUENCE, DRAW_ODDS)
                    all_simulation_results.append({
                        'Season': season,
                        'Scenario': 'Longest Unbeaten Streak',
                        'Team': team_name,
                        'Matches To 50% Mark': row['MatchesToMidSeason'],
                        'Games In Progression': games_in_prog,
                        'Outcome': outcome,
                        'Profit/Loss (Units)': round(profit, 2),
                        'Max Capital Needed (Units)': max_cap
                    })

            # Scenariusz 3: Najwyższy procent porażek
            if not teams_mid_season_df.empty:
                top3_highest_loss = teams_mid_season_df.sort_values(by='LossPercent', ascending=False).head(3)
                for _, row in top3_highest_loss.iterrows():
                    team_name = row['Team']
                    start_index = row['StartIndex']
                    sim_team_df = team_match_data[team_name].iloc[start_index:]
                    games_in_prog, profit, max_cap, outcome = simulate_fibonacci_progression(sim_team_df, FIBONACCI_SEQUENCE, DRAW_ODDS)
                    all_simulation_results.append({
                        'Season': season,
                        'Scenario': 'Highest Loss %',
                        'Team': team_name,
                        'Matches To 50% Mark': row['MatchesToMidSeason'],
                        'Games In Progression': games_in_prog,
                        'Outcome': outcome,
                        'Profit/Loss (Units)': round(profit, 2),
                        'Max Capital Needed (Units)': max_cap
                    })
            
            # Scenariusz 4: Najwyższy procent zwycięstw
            if not teams_mid_season_df.empty:
                top3_highest_win = teams_mid_season_df.sort_values(by='WinPercent', ascending=False).head(3)
                for _, row in top3_highest_win.iterrows():
                    team_name = row['Team']
                    start_index = row['StartIndex']
                    sim_team_df = team_match_data[team_name].iloc[start_index:]
                    games_in_prog, profit, max_cap, outcome = simulate_fibonacci_progression(sim_team_df, FIBONACCI_SEQUENCE, DRAW_ODDS)
                    all_simulation_results.append({
                        'Season': season,
                        'Scenario': 'Highest Win %',
                        'Team': team_name,
                        'Matches To 50% Mark': row['MatchesToMidSeason'],
                        'Games In Progression': games_in_prog,
                        'Outcome': outcome,
                        'Profit/Loss (Units)': round(profit, 2),
                        'Max Capital Needed (Units)': max_cap
                    })


        except Exception as e:
            print(f"Błąd podczas przetwarzania lub symulacji dla pliku {file_path}: {e}")

    if not all_simulation_results:
        print(f"Nie wygenerowano żadnych wyników symulacji dla ligi {league_code}.")
        return

    # Zapisujemy wyniki do pliku CSV
    results_df = pd.DataFrame(all_simulation_results)
    
    # Tworzymy ścieżkę do zapisu uwzględniającą kraj
    output_country_path = SIMULATION_OUTPUT_BASE_PATH / country
    output_country_path.mkdir(parents=True, exist_ok=True) # Tworzymy folder kraju

    output_filename = f"{country}_{league_code}_symulacja_progresji.csv"
    output_filepath = output_country_path / output_filename 
    results_df.to_csv(output_filepath, index=False)
    
    print(f"✅ Symulacja zakończona. Wyniki zapisano w: {output_filepath}")


# --- GŁÓWNA PĘTLA WYKONAWCZA ---

if __name__ == "__main__":
    
    seasons = get_seasons_to_analyze(CURRENT_SEASON_END_YEAR, X_SEASONS)
    print(f"Rozpoczynam symulację progresji dla sezonów: {seasons}")
    
    # Upewniamy się, że folder bazowy symulacji istnieje
    SIMULATION_OUTPUT_BASE_PATH.mkdir(parents=True, exist_ok=True)

    for country, leagues in COUNTRIES_LEAGUES.items():
        for league in leagues:
            analyze_and_simulate_league(country, league, seasons)
            
    print("\n\n--- Wszystkie symulacje zostały zakończone! ---")