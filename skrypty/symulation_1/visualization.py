import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

# --- Konfiguracja ścieżek (musi być zgodna z symulacją) ---
BASE_PATH = Path("D:/football_data")
SIMULATION_OUTPUT_BASE_PATH = BASE_PATH / "symulacja_1"

# --- WYBIERZ LIGĘ DO ANALIZY ---
# Podaj pełną nazwę kraju i kod ligi. Np. "England_E0"
# Upewnij się, że taka kombinacja występuje w Twoich danych symulacji.
# Jeśli chcesz analizować wszystkie dane (bez filtrowania na ligę), pozostaw None.
SELECTED_LEAGUE_FILTER = "England_E0" # Przykładowo, zmień na interesującą Cię ligę

# Ustawienia stylu wykresów
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 7) # Domyślny rozmiar wykresu
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12


def load_all_simulation_results(base_path: Path) -> pd.DataFrame:
    """
    Ładuje wszystkie pliki CSV z wynikami symulacji z podfolderów do jednego DataFrame.
    """
    all_dfs = []
    print(f"Ładowanie plików z: {base_path}")
    for country_folder in base_path.iterdir():
        if country_folder.is_dir():
            for simulation_file in country_folder.glob("*_symulacja_progresji.csv"):
                try:
                    df = pd.read_csv(simulation_file)
                    # Dodaj kolumnę z nazwą ligi do filtrowania
                    df['League'] = f"{country_folder.name}_{simulation_file.stem.split('_')[1]}"
                    all_dfs.append(df)
                    print(f"Załadowano: {simulation_file.name}")
                except Exception as e:
                    print(f"Błąd podczas ładowania {simulation_file}: {e}")
    
    if not all_dfs:
        print("Brak plików symulacji do załadowania. Upewnij się, że symulacja została uruchomiona.")
        return pd.DataFrame() # Zwróć pusty DataFrame
        
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Załadowano łącznie {len(combined_df)} wierszy danych symulacji.")
    return combined_df

# Wczytaj wszystkie wyniki symulacji
simulation_results_df = load_all_simulation_results(SIMULATION_OUTPUT_BASE_PATH)

if simulation_results_df.empty:
    print("Brak danych do wizualizacji. Skrypt zakończy działanie.")
    exit() # Zakończ skrypt, jeśli nie ma danych

# Filtrowanie danych, jeśli wybrano konkretną ligę
if SELECTED_LEAGUE_FILTER:
    initial_rows = len(simulation_results_df)
    simulation_results_df = simulation_results_df[simulation_results_df['League'] == SELECTED_LEAGUE_FILTER].copy()
    if simulation_results_df.empty:
        print(f"Brak danych dla wybranej ligi: {SELECTED_LEAGUE_FILTER}. Sprawdź nazwę.")
        exit()
    print(f"Filtrowanie: Wybrano ligę '{SELECTED_LEAGUE_FILTER}'. Zredukowano z {initial_rows} do {len(simulation_results_df)} wierszy.")

print("\n--- Generowanie wykresów szczegółowych ---")


# --- 1. Ile razy dana drużyna pojawiła się w danej kategorii doboru (Bar Chart) ---

# Użyj FacetGrid, aby stworzyć oddzielny wykres dla każdego scenariusza
g = sns.FacetGrid(simulation_results_df, col="Scenario", col_wrap=2, height=6, aspect=1.2, sharey=False)

def plot_team_counts(data, **kwargs):
    ax = plt.gca()
    # Zlicz wystąpienia drużyn i wybierz top 10
    team_counts = data['Team'].value_counts().nlargest(10).reset_index()
    team_counts.columns = ['Team', 'Count']
    sns.barplot(x='Count', y='Team', data=team_counts, palette='viridis', ax=ax)
    ax.set_title(f"Top 10 drużyn w scenariuszu: {kwargs['scenario_title']}", fontsize=12) # Mniejszy tytuł
    ax.set_xlabel('Liczba wystąpień')
    ax.set_ylabel('Drużyna')

g.map_dataframe(plot_team_counts, scenario_title=g.col_names)
g.set_axis_labels("Liczba wystąpień", "Drużyna")
g.set_titles(col_template="Scenariusz: {col_name}")
g.fig.suptitle(f'Częstotliwość Wyboru Drużyn w Kategoriach Doboru ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18, y=1.02)
plt.tight_layout(rect=[0, 0, 1, 0.98])
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"1_team_selection_frequency_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "1_team_selection_frequency_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 1: Częstotliwość wyboru drużyn wyświetlony.")


# --- 2. Średnie zyski/straty na drużynę dla każdej strategii (Grouped Bar Chart) ---

# Oblicz średni zysk/stratę dla każdej drużyny w każdym scenariuszu
avg_profit_by_team_scenario = simulation_results_df.groupby(['Scenario', 'Team'])['Profit/Loss (Units)'].mean().reset_index()

plt.figure(figsize=(16, 9))
sns.barplot(
    x='Profit/Loss (Units)',
    y='Team',
    hue='Scenario',
    data=avg_profit_by_team_scenario.sort_values(by=['Scenario', 'Profit/Loss (Units)'], ascending=[True, False]),
    palette='coolwarm' # Paleta, która dobrze rozróżnia zyski i straty
)
plt.axvline(0, color='grey', linestyle='--', linewidth=1.5, label='Zero Profit/Loss Line')
plt.title(f'Średni Zysk/Strata na Drużynę wg Scenariusza ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18)
plt.xlabel('Średni Zysk/Strata (Jednostki)', fontsize=14)
plt.ylabel('Drużyna', fontsize=14)
plt.legend(title='Scenariusz', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"2_avg_profit_loss_per_team_scenario_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "2_avg_profit_loss_per_team_scenario_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 2: Średni zysk/strata na drużynę wyświetlony.")


# --- 3. Zyskowność strategii (Total Profit/Loss) i liczba wygranych/przegranych progresji (Bar Chart) ---

# Całkowity zysk/strata na scenariusz
total_profit_by_scenario = simulation_results_df.groupby('Scenario')['Profit/Loss (Units)'].sum().reset_index()

plt.figure(figsize=(14, 8))
sns.barplot(x='Scenario', y='Profit/Loss (Units)', data=total_profit_by_scenario, palette='viridis')
plt.axhline(0, color='grey', linestyle='--', linewidth=1.5, label='Zero Profit/Loss Line')
plt.title(f'Całkowity Zysk/Strata na Scenariusz ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18)
plt.xlabel('Scenariusz', fontsize=14)
plt.ylabel('Całkowity Zysk/Strata (Jednostki)', fontsize=14)
plt.xticks(rotation=15)
plt.tight_layout()
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"3a_total_profit_loss_by_scenario_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "3a_total_profit_loss_by_scenario_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 3a: Całkowity zysk/strata na scenariusz wyświetlony.")


# Liczba wygranych/przegranych progresji na scenariusz
outcome_counts = simulation_results_df.groupby(['Scenario', 'Outcome']).size().unstack(fill_value=0).reset_index()
# Upewnij się, że są kolumny 'Win' i 'Loss'
for col in ['Win', 'Loss']:
    if col not in outcome_counts.columns:
        outcome_counts[col] = 0

outcome_counts_long = outcome_counts.melt(id_vars='Scenario', var_name='Outcome', value_name='Count')

plt.figure(figsize=(14, 8))
sns.barplot(x='Scenario', y='Count', hue='Outcome', data=outcome_counts_long, palette={'Win': 'mediumseagreen', 'Loss': 'lightcoral'})
plt.title(f'Liczba Wygranych/Przegranych Progresji na Scenariusz ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18)
plt.xlabel('Scenariusz', fontsize=14)
plt.ylabel('Liczba Progresji', fontsize=14)
plt.xticks(rotation=15)
plt.legend(title='Wynik Progresji')
plt.tight_layout()
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"3b_outcome_counts_by_scenario_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "3b_outcome_counts_by_scenario_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 3b: Liczba wygranych/przegranych progresji wyświetlona.")


# --- 4. Maksymalny potrzebny kapitał vs. Zysk/Strata (Faceted Scatter Plot) ---

# Tworzenie KOPii DataFrame, aby wprowadzić zmiany tylko dla TEGO wykresu
plot_df_4 = simulation_results_df.copy()
# Zmiana wartości ujemnych na -10 dla osi Y
plot_df_4['Profit/Loss (Units)'] = plot_df_4['Profit/Loss (Units)'].apply(lambda x: -10 if x < 0 else x)


g = sns.FacetGrid(plot_df_4, col="Scenario", col_wrap=2, height=5, aspect=1.3, sharey=False, sharex=False)
g.map_dataframe(sns.scatterplot, x='Max Capital Needed (Units)', y='Profit/Loss (Units)', hue='Outcome', s=100, alpha=0.7, palette={'Win': 'mediumseagreen', 'Loss': 'lightcoral'})

# Dodaj linię zero i dostosuj skale
for ax in g.axes.flat:
    ax.axhline(0, color='grey', linestyle='--', linewidth=1)
    # Próbujemy ustawić skalę logarytmiczną dla osi X
    # Jeśli wartości kapitału są zerowe lub ujemne, skala logarytmiczna nie zadziała.
    if (plot_df_4['Max Capital Needed (Units)'] > 0).all():
        ax.set_xscale('log')
    ax.set_xlabel('Maks. Potrzebny Kapitał (Jednostki)')
    ax.set_ylabel('Zysk/Strata (Jednostki) (Straty Ustandaryzowane do -10)')
    ax.grid(True, which="both", ls="--", c='0.7')
    
g.add_legend(title='Wynik')
g.set_titles("Scenariusz: {col_name}")
g.fig.suptitle(f'Maks. Potrzebny Kapitał vs. Zysk/Strata wg Scenariusza ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18, y=1.02)
plt.tight_layout(rect=[0, 0, 1, 0.98])
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"4_faceted_capital_vs_profit_loss_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "4_faceted_capital_vs_profit_loss_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 4: Faceted scatter plot kapitał vs. zysk/strata (zmodyfikowany) wyświetlony.")


# --- 5. Rozkład Długości Progresji (Games In Progression) dla każdej Strategii (Violin Plot) ---
plt.figure(figsize=(14, 8))
sns.violinplot(x='Scenario', y='Games In Progression', data=simulation_results_df, inner='quartile', palette='pastel')
plt.title(f'Rozkład Długości Progresji (Gier) dla Różnych Scenariuszy ({SELECTED_LEAGUE_FILTER if SELECTED_LEAGUE_FILTER else "Wszystkie Ligi"})', fontsize=18)
plt.xlabel('Scenariusz Wyboru Drużyny', fontsize=14)
plt.ylabel('Liczba Gier w Progresji', fontsize=14)
plt.xticks(rotation=15)
plt.tight_layout()
# plt.savefig(SIMULATION_OUTPUT_BASE_PATH / (f"5_games_in_progression_violin_{SELECTED_LEAGUE_FILTER}.png" if SELECTED_LEAGUE_FILTER else "5_games_in_progression_violin_all_leagues.png"))
plt.show() # <-- Wyświetl wykres
print("Wykres 5: Rozkład długości progresji (violin plot) wyświetlony.")

