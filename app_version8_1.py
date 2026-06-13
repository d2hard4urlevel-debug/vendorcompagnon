"""VendorCompagnon V8.1

Version de test basee sur app_version8.py.
- Chemins robustes Windows avec APP_DIR
- Lancement du scraper depuis le dossier de l'app
- Mode de filtres Souple / Strict
- Diagnostic CSV visible
- Depot recu conserve dans l'historique

Ce fichier ne modifie pas app_version8.py ni carpart_scraper.py.
"""

from pathlib import Path
import re


APP_FILE = Path(__file__).resolve().parent / "app_version8.py"

if not APP_FILE.exists():
    raise FileNotFoundError(f"Fichier introuvable : {APP_FILE}")

source = APP_FILE.read_text(encoding="utf-8")

source = source.replace(
    "# VendorCompagnon - VERSION 8\n# Filtres stricts + options économique / recommandée / premium",
    "# VendorCompagnon - VERSION 8.1\n# V8 stable + diagnostics, chemins Windows et filtres souples",
)
source = source.replace(
    'APP_NAME = "VendorCompagnon V8 - Filtres stricts"',
    'APP_NAME = "VendorCompagnon V8.1 - Diagnostic"',
)
source = source.replace(
    'BASE_DIR = os.path.join(os.getcwd(), "carpart_app")',
    'APP_DIR = os.path.dirname(os.path.abspath(__file__))\n\nBASE_DIR = os.path.join(APP_DIR, "carpart_app")',
)
source = source.replace(
    'SCRAPER_FILE = "carpart_scraper.py"',
    'SCRAPER_FILE = os.path.join(APP_DIR, "carpart_scraper.py")',
)
source = source.replace(
    'process = subprocess.run([sys.executable, SCRAPER_FILE], capture_output=True, text=True)',
    'process = subprocess.run(\n            [sys.executable, SCRAPER_FILE],\n            capture_output=True,\n            text=True,\n            encoding="utf-8",\n            errors="replace",\n            cwd=APP_DIR\n        )',
)

filter_block = r'''def get_filter_reason(row):.*?def apply_strict_filters\(df\):.*?    return df\n'''
filter_replacement = '''def get_warning_reason(row):
    raw = str(row.get("raw", "")).strip()
    warranty = row.get("warranty", "")

    warnings = []

    if not has_good_description(raw):
        warnings.append("description courte ou absente")

    if not has_valid_warranty(warranty):
        warnings.append("garantie absente")

    return " | ".join(warnings)


def get_filter_reason(row, strict_mode=True):
    raw = str(row.get("raw", "")).strip()
    km = row.get("km", "")
    warranty = row.get("warranty", "")
    distance = row.get("distance", "")

    reasons = []

    if strict_mode and not has_good_description(raw):
        reasons.append("description absente ou trop courte")
    if not has_valid_km(km):
        reasons.append("kilométrage inconnu ou invalide")
    if strict_mode and not has_valid_warranty(warranty):
        reasons.append("garantie absente")
    if not has_valid_distance(distance):
        reasons.append(f"distance trop élevée : plus de {MAX_DISTANCE_KM} km")
    if is_bad(raw):
        reasons.append("terme négatif : " + bad_words_found(raw))

    return " | ".join(reasons)


def apply_v8_filters(df, strict_mode=True):
    df = df.copy()
    df["avertissements"] = df.apply(get_warning_reason, axis=1)
    df["raison_exclusion"] = df.apply(lambda row: get_filter_reason(row, strict_mode), axis=1)
    df["excluded"] = df["raison_exclusion"].astype(str).str.strip() != ""
    return df
'''
source = re.sub(filter_block, filter_replacement, source, flags=re.S)

source = source.replace(
    'def calculate_report(df, marge_souhaitee, marge_minimale):\n    df = normalize_columns(df)\n    if len(df) == 0:\n        return None',
    'def calculate_report(df, marge_souhaitee, marge_minimale, filter_mode):\n    source_rows = len(df)\n    df = normalize_columns(df)\n    if len(df) == 0:\n        return {"df": df, "valid": pd.DataFrame(), "excluded": pd.DataFrame(), "error": "Aucun prix exploitable dans le CSV.", "nb_lignes_source": source_rows, "nb_lignes_avec_prix": 0, "filter_mode": filter_mode}',
)
source = source.replace(
    'df = apply_strict_filters(df)',
    'strict_mode = filter_mode == "Strict"\n    df = apply_v8_filters(df, strict_mode)',
)
source = source.replace(
    'return {"df": df, "valid": valid, "excluded": excluded, "error": "Aucun moteur valide après les filtres stricts."}',
    'return {"df": df, "valid": valid, "excluded": excluded, "error": "Aucun moteur valide après les filtres sélectionnés.", "nb_lignes_source": source_rows, "nb_lignes_avec_prix": len(df), "filter_mode": filter_mode}',
)
source = source.replace(
    '"df": df, "valid": valid, "excluded": excluded, "error": None,',
    '"df": df, "valid": valid, "excluded": excluded, "error": None,\n        "nb_lignes_source": source_rows, "nb_lignes_avec_prix": len(df), "filter_mode": filter_mode,',
)

source = source.replace(
    'marge_minimale = st.number_input("Marge minimale acceptable", min_value=0, max_value=10000, value=400, step=50)\n    status = st.selectbox',
    'marge_minimale = st.number_input("Marge minimale acceptable", min_value=0, max_value=10000, value=400, step=50)\n    filter_mode = st.selectbox("Mode de filtres", ["Souple", "Strict"], help="Souple garde les moteurs sans garantie ou avec description courte, mais les affiche avec avertissement.")\n    status = st.selectbox',
)
source = source.replace(
    'else:\n        report = calculate_report(df_source, marge_souhaitee, marge_minimale)',
    'else:\n        with st.expander("Diagnostic CSV", expanded=True):\n            st.write("Source :", "CSV importé" if uploaded_file is not None else RESULTS_FILE)\n            st.write("Lignes lues :", len(df_source))\n            st.write("Colonnes détectées :", ", ".join([str(c) for c in df_source.columns]))\n            st.write("Mode de filtres :", filter_mode)\n\n        report = calculate_report(df_source, marge_souhaitee, marge_minimale, filter_mode)',
)
source = source.replace(
    'st.write(f"Nombre exclus : {len(excluded)}")\n            if len(excluded) > 0:',
    'st.write("Lignes avec prix exploitable :", report.get("nb_lignes_avec_prix", 0))\n            st.write(f"Nombre exclus : {len(excluded)}")\n            if len(excluded) > 0:',
)
source = source.replace(
    '"raison_exclusion", "fournisseur_confiance"',
    '"raison_exclusion", "avertissements", "fournisseur_confiance"',
)
source = source.replace(
    '"warranty", "fournisseur_confiance"',
    '"warranty", "avertissements", "fournisseur_confiance"',
)
source = source.replace(
    'new_depot = st.selectbox("Dépôt reçu", ["", "Non", "Oui"], index=0)',
    'depot_options = ["", "Non", "Oui"]\n            current_depot = str(selected_row.get("depot_recu", ""))\n            depot_index = depot_options.index(current_depot) if current_depot in depot_options else 0\n            new_depot = st.selectbox("Dépôt reçu", depot_options, index=depot_index)',
)

compiled = compile(source, str(APP_FILE), "exec")
exec_globals = {
    "__file__": str(Path(__file__).resolve()),
    "__name__": "__main__",
}
exec(compiled, exec_globals)
