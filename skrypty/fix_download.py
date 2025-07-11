import os
import shutil

BASE_DIR = "D:/football_data"

def fix_folder_structure(base_dir):
    for root, dirs, files in os.walk(base_dir):
        parts = root[len(base_dir):].strip(os.sep).split(os.sep)
        if len(parts) == 2:
            try:
                start_year = int(parts[0])
                end_year = int(parts[1])
                new_folder = os.path.join(base_dir, f"{start_year}-{end_year}")
                old_folder = os.path.join(base_dir, parts[0], parts[1])

                if not os.path.exists(new_folder):
                    os.makedirs(new_folder)

                # Przenieś wszystkie podfoldery do nowej lokalizacji
                for item in os.listdir(old_folder):
                    src = os.path.join(old_folder, item)
                    dst = os.path.join(new_folder, item)
                    shutil.move(src, dst)
                    print(f"Przeniesiono: {src} -> {dst}")

                # Usuń puste foldery
                shutil.rmtree(os.path.join(base_dir, parts[0]))
            except ValueError:
                continue  # Pomijamy foldery niepasujące do schematu

if __name__ == "__main__":
    fix_folder_structure(BASE_DIR)
