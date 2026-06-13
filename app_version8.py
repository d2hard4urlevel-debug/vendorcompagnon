import os
import sys
import math
import re
import subprocess
from datetime import datetime, date

import pandas as pd
import streamlit as st


# ============================================================
# VendorCompagnon - VERSION 8
# Filtres stricts + options économique / recommandée / premium
# ============================================================

APP_NAME = "VendorCompagnon V8 - Filtres stricts"

BASE_DIR = os.path.join(os.getcwd(), "carpart_app")
HIST_DIR = os.path.join(BASE_DIR, "historiques")
REPORTS_DIR = os.path.join(BASE_DIR, "rapports")
ANALYSES_DIR = os.path.join(BASE_DIR, "analyses")
MEMORY_DIR = os.path.join(BASE_DIR, "memoire")

RESULTS_FILE = os.path.join(BASE_DIR, "resultats.csv")
OFFERS_FILE = os.path.join(HIST_DIR, "offres_clients.csv")
ANALYSES_INDEX_FILE = os.path.join(ANALYSES_DIR, "analyses_index.csv")
MEMORY_MOTORS_FILE = os.path.join(MEMORY_DIR, "memoire_moteurs.csv")
MEMORY_CLIENTS_FILE = os.path.join(MEMORY_DIR, "memoire_clients.csv")

SCRAPER_FILE = "carpart_scraper.py"
MAX_DISTANCE_KM = 1000

for folder in [BASE_DIR, HIST_DIR, REPORTS_DIR, ANALYSES_DIR, MEMORY_DIR]:
    os.makedirs(folder, exist_ok=True)

st.set_page_config(page_title=APP_NAME, page_icon="🚗", layout="wide")


# ============================================================
# ÉCRITURE FICHIER SANS open()
# ============================================================

def write_bytes_to_file(path, content_bytes):
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o666)
    try:
        os.write(fd, content_bytes)
    finally:
        os.close(fd)


def safe_to_csv(df, path):
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    write_bytes_to_file(path, csv_bytes)


# ============================================================
# FOURNISSEURS CONNUS
# ============================================================

TRUSTED_SUPPLIERS = [
    "pieces d'autos fernand begin",
    "pièces d'autos fernand begin",
    "fernand begin",
    "fernand bégin",
    "lkq",
]


def normalize_text(text):
    text = str(text).lower()
    replacements = {
        "é": "e", "è": "e", "ê": "e", "à": "a", "â": "a",
        "î": "i", "ï": "i", "ô": "o", "û": "u", "ç": "c",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def is_trusted_supplier_text(text):
    clean = normalize_text(text)
    return any(normalize_text(s) in clean for s in TRUSTED_SUPPLIERS)


def trusted_supplier_name(text):
    clean = normalize_text(text)
    if "lkq" in clean:
        return "LKQ"
    if "fernand" in clean and "begin" in clean:
        return "Pieces d'autos Fernand Begin"
    return ""


# ============================================================
# FILTRES STRICTS - VERSION 8
# ============================================================

BAD_WORDS = [
    # Reman / rebuilt / pas comparable
    "reman", "remanufactured", "re-man", "re man",
    "rebuilt", "rebuild", "new rebuild", "new reman",
    "long block", "short block", "crate engine", "brand new",

    # Core / pour pièces
    "core", "running core", "need core", "needs core",
    "parts only", "for parts", "part only", "as is", "as-is",

    # Moteur pas testé / problème connu
    "no start", "non running", "does not run",
    "not tested", "needs test", "untested", "to be tested", "no keys",
    "bad", "nfg", "defective", "damaged", "problem", "problems",
    "issue", "issues", "needs repair", "repair needed",

    # Dommages physiques anglais
    "burnt", "burned", "fire", "fire damage", "flood",
    "water damage", "water damaged", "cracked", "broken", "hole",
    "damage", "collision damage", "damaged parts", "broken part",
    "broken parts", "broken piece", "broken pieces", "damaged component",
    "broken component",

    # Dommages physiques français
    "brisé", "brisee", "brisée", "briser", "cassé", "cassee", "cassée",
    "endommagé", "endommage", "endommagée", "piece brisee", "pièce brisée",
    "piece brisé", "pièce brisé", "piece casse", "pièce cassée",
    "pieces brisees", "pièces brisées", "pieces cassees", "pièces cassées",
    "composant brisé", "composant cassé",

    # Pièces manquantes / moteur incomplet
    "missing", "missing parts", "head gone", "no head", "heads removed",
    "head removed", "no intake", "no manifold", "no accessories", "bare",
    "bare engine", "manquant", "manquante", "pieces manquantes",
    "pièces manquantes", "piece manquante", "pièce manquante",
    "sans tete", "sans tête", "tete enlevee", "tête enlevée",
    "tete retiree", "tête retirée", "moteur incomplet",

    # Problèmes mécaniques anglais
    "misfire", "knock", "knocking", "low compression", "no compression",
    "bad compression", "compression issue", "seized", "locked up", "locked",
    "overheated", "overheat", "oil leak", "coolant leak", "smokes",
    "smoking", "timing issue", "timing problem",

    # Problèmes mécaniques français
    "raté", "rate", "cogne", "cognement", "compression basse",
    "pas de compression", "mauvaise compression", "saisi", "moteur saisi",
    "bloqué", "bloque", "surchauffe", "surchauffé", "surchauffe moteur",
    "fuite huile", "fuite d'huile", "fuite prestone", "fuite coolant",
    "fumee", "fumée", "boucanne",

    # Timing chain / chaîne à faire
    "timing chain", "timing chains", "timing chain issue",
    "timing chain problem", "timing chain noise", "timing chain rattle",
    "needs timing chain", "needs timing chains", "needs chain", "needs chains",
    "chain noise", "chain rattle", "chain problem", "chain issue",
    "chaines a faire", "chaînes à faire", "chaine a faire", "chaîne à faire",
    "chaine de timing", "chaîne de timing", "chaines de timing",
    "chaînes de timing", "chaine brisee", "chaîne brisée", "chaine etiree",
    "chaîne étirée", "chaine sautee", "chaîne sautée", "probleme de chaine",
    "problème de chaîne", "bruit de chaine", "bruit de chaîne", "guide de chaine",
    "guide de chaîne", "tendeur de chaine", "tendeur de chaîne",

    # Notes négatives fréquentes
    "do not sell", "do not use", "needs new head", "needs head",
    "needs timing", "needs rebuild", "needs rebuilt", "a reparer", "à réparer",
    "besoin reparation", "besoin réparation", "doit etre repare", "doit être réparé",
]

BAD_WORDS_EXACT = ["ns"]


def is_bad(text):
    text = normalize_text(text)
    for word in BAD_WORDS:
        if normalize_text(word) in text:
            return True
    for word in BAD_WORDS_EXACT:
        pattern = r"\b" + re.escape(normalize_text(word)) + r"\b"
        if re.search(pattern, text):
            return True
    return False


def bad_words_found(text):
    text = normalize_text(text)
    found = []
    for word in BAD_WORDS:
        if normalize_text(word) in text:
            found.append(word)
    for word in BAD_WORDS_EXACT:
        pattern = r"\b" + re.escape(normalize_text(word)) + r"\b"
        if re.search(pattern, text):
            found.append(word.upper())
    return ", ".join(found[:6])


def has_good_description(raw_text):
    raw_text = str(raw_text).strip()
    if raw_text == "":
        return False
    if raw_text.lower() in ["nan", "none", "null"]:
        return False
    if len(raw_text) < 40:
        return False
    return True


def has_valid_km(value):
    try:
        if pd.isna(value):
            return False
        km = float(value)
        if km <= 0:
            return False
        if km > 500000:
            return False
        return True
    except Exception:
        return False


def has_valid_warranty(value):
    text = str(value).strip().lower()
    bad_warranty_values = [
        "", "nan", "none", "null", "n/a", "na", "no warranty", "no warr",
        "as is", "as-is", "0", "-",
    ]
    return text not in bad_warranty_values


def has_valid_distance(value):
    try:
        if pd.isna(value):
            return True
        distance = float(value)
        if distance <= 0:
            return True
        return distance <= MAX_DISTANCE_KM
    except Exception:
        return True


def get_filter_reason(row):
    raw = str(row.get("raw", "")).strip()
    km = row.get("km", "")
    warranty = row.get("warranty", "")
    distance = row.get("distance", "")

    reasons = []

    if not has_good_description(raw):
        reasons.append("description absente ou trop courte")
    if not has_valid_km(km):
        reasons.append("kilométrage inconnu ou invalide")
    if not has_valid_warranty(warranty):
        reasons.append("garantie absente")
    if not has_valid_distance(distance):
        reasons.append(f"distance trop élevée : plus de {MAX_DISTANCE_KM} km")
    if is_bad(raw):
        reasons.append("terme négatif : " + bad_words_found(raw))

    return " | ".join(reasons)


def apply_strict_filters(df):
    df = df.copy()
    df["raison_exclusion"] = df.apply(get_filter_reason, axis=1)
    df["excluded"] = df["raison_exclusion"].astype(str).str.strip() != ""
    return df


# ============================================================
# OUTILS
# ============================================================

def money(value):
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):,.0f} $".replace(",", " ")
    except Exception:
        return "-"


def km_format(value):
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):,.0f} km".replace(",", " ")
    except Exception:
        return "-"


def percent_format(value):
    try:
        return f"{float(value):.1f} %"
    except Exception:
        return "-"


def round_to_5(value):
    try:
        return int(round(float(value) / 5) * 5)
    except Exception:
        return 0


def clean_numeric(value):
    try:
        if pd.isna(value):
            return None
        text = str(value)
        text = text.replace("$", "")
        text = text.replace(",", "")
        text = text.replace("km", "")
        text = text.replace("KM", "")
        text = text.replace("K", "")
        text = text.replace(" ", "")
        text = text.strip()
        if text == "" or text.lower() == "call":
            return None
        return float(text)
    except Exception:
        return None


def normalize_columns(df):
    df = df.copy()
    required_columns = [
        "price", "km", "distance", "grade", "warranty", "raw", "page",
        "search_title", "selected_model", "vehicule_moteur_auto",
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    df["price"] = df["price"].apply(clean_numeric)
    df["km"] = df["km"].apply(clean_numeric)
    df["distance"] = df["distance"].apply(clean_numeric)
    df["raw"] = df["raw"].fillna("").astype(str)
    df["warranty"] = df["warranty"].fillna("").astype(str)
    df["grade"] = df["grade"].fillna("").astype(str)

    df = df[df["price"].notna()].copy()
    df = df[df["price"] > 0].copy()
    return df


def get_distance_fee(distance):
    try:
        if pd.isna(distance):
            return 250
        distance = float(distance)
        if distance <= 40:
            return 50
        elif distance <= 150:
            return round_to_5(distance)
        elif distance <= 400:
            return 250
        elif distance <= MAX_DISTANCE_KM:
            return 500
        else:
            return 9999
    except Exception:
        return 250


def get_vehicle_auto(df):
    for col in ["vehicule_moteur_auto", "selected_model", "search_title"]:
        if col in df.columns:
            values = df[col].dropna().astype(str)
            values = values[values.str.strip() != ""]
            if len(values) > 0:
                return values.iloc[0].strip()
    return ""


def calculate_km_branches(valid):
    km_values = valid["km"].dropna().astype(float).sort_values().tolist()

    if len(km_values) == 0:
        return {
            "premium": {"min": None, "avg": None, "max": None},
            "recommande": {"min": None, "avg": None, "max": None},
            "economique": {"min": None, "avg": None, "max": None},
        }

    n = len(km_values)
    if n == 1:
        branches = {"premium": km_values, "recommande": km_values, "economique": km_values}
    elif n == 2:
        branches = {"premium": [km_values[0]], "recommande": km_values, "economique": [km_values[1]]}
    else:
        third = max(1, n // 3)
        premium = km_values[:third]
        recommande = km_values[third:third * 2] or km_values
        economique = km_values[third * 2:] or [km_values[-1]]
        branches = {"premium": premium, "recommande": recommande, "economique": economique}

    result = {}
    for key, values in branches.items():
        if len(values) == 0:
            result[key] = {"min": None, "avg": None, "max": None}
        else:
            result[key] = {"min": min(values), "avg": sum(values) / len(values), "max": max(values)}
    return result


def branch_text(branch):
    if branch["min"] is None:
        return "-"
    return f"{km_format(branch['min'])} à {km_format(branch['max'])}"


# ============================================================
# HISTORIQUE
# ============================================================

OFFER_COLUMNS = [
    "date", "client", "type_client", "vehicule_moteur", "vehicule_moteur_manuel",
    "vehicule_moteur_auto", "search_title", "selected_model", "prix_economique",
    "prix_recommande", "prix_premium", "prix_minimum_economique",
    "prix_minimum_recommande", "prix_minimum_premium", "cout_achat_max_economique",
    "cout_achat_max_recommande", "cout_achat_max_premium", "marge_souhaitee",
    "marge_minimale", "status", "date_rappel", "raison_refus", "prix_final_vendu",
    "depot_recu", "fournisseur_choisi", "note_commande", "note_interne",
    "nb_total", "nb_valides", "nb_exclus", "prix_median_marche", "km_min",
    "km_moyen", "km_max",
]


def load_offers():
    if not os.path.exists(OFFERS_FILE):
        return pd.DataFrame(columns=OFFER_COLUMNS)
    try:
        df = pd.read_csv(OFFERS_FILE)
        for col in OFFER_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[OFFER_COLUMNS].copy()
    except Exception:
        return pd.DataFrame(columns=OFFER_COLUMNS)


def save_all_offers(df):
    for col in OFFER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    safe_to_csv(df[OFFER_COLUMNS], OFFERS_FILE)


def add_offer(row):
    df = load_offers()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_all_offers(df)


def update_offer(index, updates):
    df = load_offers()
    for key, value in updates.items():
        if key in df.columns:
            df.at[index, key] = value
    save_all_offers(df)


# ============================================================
# ANALYSE
# ============================================================

def calculate_report(df, marge_souhaitee, marge_minimale):
    df = normalize_columns(df)
    if len(df) == 0:
        return None

    df["fournisseur_confiance"] = df["raw"].apply(is_trusted_supplier_text)
    df["fournisseur_detecte"] = df["raw"].apply(trusted_supplier_name)
    df = apply_strict_filters(df)

    valid = df[df["excluded"] == False].copy()
    excluded = df[df["excluded"] == True].copy()

    if len(valid) == 0:
        return {"df": df, "valid": valid, "excluded": excluded, "error": "Aucun moteur valide après les filtres stricts."}

    prices = valid["price"].dropna().astype(float)
    median_price = prices.median()
    avg_price = prices.mean()
    min_price = prices.min()
    max_price = prices.max()

    avg_distance = valid["distance"].dropna().astype(float).mean() if "distance" in valid.columns else 0
    distance_fee = get_distance_fee(avg_distance)

    base_economique = round_to_5(median_price * 0.90)
    base_recommande = round_to_5(median_price * 1.05)
    base_premium = round_to_5(median_price * 1.18)

    prix_economique = round_to_5(base_economique + distance_fee + marge_souhaitee)
    prix_recommande = round_to_5(base_recommande + distance_fee + marge_souhaitee)
    prix_premium = round_to_5(base_premium + distance_fee + marge_souhaitee)

    prix_minimum_economique = round_to_5(base_economique + distance_fee + marge_minimale)
    prix_minimum_recommande = round_to_5(base_recommande + distance_fee + marge_minimale)
    prix_minimum_premium = round_to_5(base_premium + distance_fee + marge_minimale)

    cout_achat_max_economique = round_to_5(prix_minimum_economique - distance_fee - marge_minimale)
    cout_achat_max_recommande = round_to_5(prix_minimum_recommande - distance_fee - marge_minimale)
    cout_achat_max_premium = round_to_5(prix_minimum_premium - distance_fee - marge_minimale)

    km_values = valid["km"].dropna().astype(float)
    km_min = km_values.min() if len(km_values) else None
    km_avg = km_values.mean() if len(km_values) else None
    km_max = km_values.max() if len(km_values) else None
    km_branches = calculate_km_branches(valid)

    return {
        "df": df, "valid": valid, "excluded": excluded, "error": None,
        "nb_total": len(df), "nb_valides": len(valid), "nb_exclus": len(excluded),
        "median_price": median_price, "avg_price": avg_price, "min_price": min_price,
        "max_price": max_price, "avg_distance": avg_distance, "distance_fee": distance_fee,
        "prix_economique": prix_economique, "prix_recommande": prix_recommande,
        "prix_premium": prix_premium, "prix_minimum_economique": prix_minimum_economique,
        "prix_minimum_recommande": prix_minimum_recommande,
        "prix_minimum_premium": prix_minimum_premium,
        "cout_achat_max_economique": cout_achat_max_economique,
        "cout_achat_max_recommande": cout_achat_max_recommande,
        "cout_achat_max_premium": cout_achat_max_premium,
        "km_min": km_min, "km_avg": km_avg, "km_max": km_max,
        "km_branches": km_branches,
        "vehicule_moteur_auto": get_vehicle_auto(df),
    }


# ============================================================
# SCRAPER / ANALYSES
# ============================================================

def run_scraper():
    if not os.path.exists(SCRAPER_FILE):
        st.error(f"Fichier introuvable : {SCRAPER_FILE}")
        return False
    try:
        process = subprocess.run([sys.executable, SCRAPER_FILE], capture_output=True, text=True)
        if process.returncode != 0:
            st.error("Erreur pendant l’analyse Car-Part.")
            st.code(process.stderr)
            return False
        return True
    except Exception as e:
        st.error(f"Erreur : {e}")
        return False


def save_analysis_snapshot(df, vehicule_moteur):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join(c if c.isalnum() else "_" for c in str(vehicule_moteur))[:50]
    filename = f"analyse_{timestamp}_{clean_name}.csv"
    path = os.path.join(ANALYSES_DIR, filename)
    safe_to_csv(df, path)

    index_row = pd.DataFrame([{
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "vehicule_moteur": vehicule_moteur,
        "fichier": filename,
        "nb_lignes": len(df),
    }])

    if os.path.exists(ANALYSES_INDEX_FILE):
        try:
            index_df = pd.read_csv(ANALYSES_INDEX_FILE)
        except Exception:
            index_df = pd.DataFrame()
    else:
        index_df = pd.DataFrame()

    index_df = pd.concat([index_df, index_row], ignore_index=True)
    safe_to_csv(index_df, ANALYSES_INDEX_FILE)


# ============================================================
# INTERFACE
# ============================================================

st.title("🚗 VendorCompagnon")
st.caption("Version 8 — Filtres stricts, options client et zone interne.")

with st.sidebar:
    st.header("Nouvelle offre")
    client = st.text_input("Nom du client")
    type_client = st.selectbox("Type de client", ["Particulier", "Garage", "Dealer", "Recyclage", "Client régulier"])
    vehicule_moteur_manuel = st.text_input("Véhicule / moteur recherché", placeholder="Laisser vide pour utiliser le choix Car-Part automatiquement")
    marge_souhaitee = st.number_input("Marge souhaitée", min_value=0, max_value=10000, value=700, step=50)
    marge_minimale = st.number_input("Marge minimale acceptable", min_value=0, max_value=10000, value=400, step=50)
    status = st.selectbox("Statut de l'offre", ["En attente", "Acceptée", "Refusée", "À rappeler"])

    date_rappel_value = ""
    if status == "À rappeler":
        date_rappel_value = st.date_input("Date de rappel", value=date.today()).strftime("%Y-%m-%d")

    raison_refus = ""
    if status == "Refusée":
        raison_refus = st.text_input("Raison du refus")

    prix_final_vendu = ""
    depot_recu = ""
    fournisseur_choisi = ""
    note_commande = ""
    if status == "Acceptée":
        prix_final_vendu = st.number_input("Prix final vendu", min_value=0, value=0, step=50)
        depot_recu = st.selectbox("Dépôt reçu", ["Non", "Oui"])
        fournisseur_choisi = st.text_input("Fournisseur choisi")
        note_commande = st.text_area("Note de commande")

    note_interne = st.text_area("Note interne")
    st.divider()
    run_button = st.button("🔎 Analyser Car-Part", use_container_width=True)
    uploaded_file = st.file_uploader("Ou importer un CSV manuellement", type=["csv"])

if run_button:
    with st.spinner("Ouverture de Car-Part Pro..."):
        success = run_scraper()
    if success:
        st.success("Analyse terminée. Résultats chargés.")

tabs = st.tabs(["Nouvelle offre", "À rappeler aujourd’hui", "Historique des offres", "Statistiques", "Messages", "Analyses sauvegardées", "Mémoire"])


with tabs[0]:
    df_source = None
    if uploaded_file is not None:
        try:
            df_source = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Impossible de lire le CSV : {e}")
            df_source = None
    elif os.path.exists(RESULTS_FILE):
        try:
            df_source = pd.read_csv(RESULTS_FILE)
        except Exception as e:
            st.error(f"Impossible de lire resultats.csv : {e}")
            df_source = None

    if df_source is None:
        st.info("Clique sur **Analyser Car-Part** ou importe un CSV.")
    else:
        report = calculate_report(df_source, marge_souhaitee, marge_minimale)
        if report is None:
            st.error("Aucune donnée exploitable.")
        elif report.get("error"):
            st.error(report["error"])
            excluded = report.get("excluded", pd.DataFrame())
            st.subheader("Moteurs exclus")
            st.write(f"Nombre exclus : {len(excluded)}")
            if len(excluded) > 0:
                cols = [c for c in ["page", "price", "km", "distance", "grade", "warranty", "raison_exclusion", "fournisseur_confiance", "fournisseur_detecte", "raw"] if c in excluded.columns]
                st.dataframe(excluded[cols], use_container_width=True)
        else:
            vehicule_moteur_auto = report["vehicule_moteur_auto"]
            vehicule_moteur = vehicule_moteur_manuel.strip() if vehicule_moteur_manuel.strip() else vehicule_moteur_auto
            if vehicule_moteur.strip() == "":
                vehicule_moteur = "Moteur non identifié"

            save_analysis_snapshot(report["df"], vehicule_moteur)

            st.subheader("Résumé du marché")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Résultats total", report["nb_total"])
            c2.metric("Utilisés dans le calcul", report["nb_valides"])
            c3.metric("Exclus par filtres", report["nb_exclus"])
            c4.metric("Prix médian fournisseur", money(report["median_price"]))

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Km minimum", km_format(report["km_min"]))
            c6.metric("Km moyen", km_format(report["km_avg"]))
            c7.metric("Km maximum", km_format(report["km_max"]))
            c8.metric("Transport estimé", money(report["distance_fee"]))

            st.info(f"Modèle utilisé : **{vehicule_moteur}**")
            st.divider()
            st.subheader("Options client")

            km_branches = report["km_branches"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### Option économique")
                st.metric("Prix client", money(report["prix_economique"]))
                st.write("Km branche :", branch_text(km_branches["economique"]))
                st.write("Km moyen :", km_format(km_branches["economique"]["avg"]))
                st.caption("Prix plus bas / kilométrage plus élevé.")
            with col2:
                st.markdown("### Option recommandée")
                st.metric("Prix client", money(report["prix_recommande"]))
                st.write("Km branche :", branch_text(km_branches["recommande"]))
                st.write("Km moyen :", km_format(km_branches["recommande"]["avg"]))
                st.caption("Meilleur équilibre prix / kilométrage.")
            with col3:
                st.markdown("### Option premium")
                st.metric("Prix client", money(report["prix_premium"]))
                st.write("Km branche :", branch_text(km_branches["premium"]))
                st.write("Km moyen :", km_format(km_branches["premium"]["avg"]))
                st.caption("Plus bas kilométrages disponibles.")

            st.divider()
            st.subheader("Zone interne - minimum vendeur")
            st.warning("Cette section est interne. Ne pas montrer au client.")
            i1, i2, i3 = st.columns(3)
            with i1:
                st.markdown("#### Économique")
                st.write("Prix client affiché :", money(report["prix_economique"]))
                st.write("Prix minimum vendeur :", money(report["prix_minimum_economique"]))
                st.write("Coût achat max interne :", money(report["cout_achat_max_economique"]))
            with i2:
                st.markdown("#### Recommandé")
                st.write("Prix client affiché :", money(report["prix_recommande"]))
                st.write("Prix minimum vendeur :", money(report["prix_minimum_recommande"]))
                st.write("Coût achat max interne :", money(report["cout_achat_max_recommande"]))
            with i3:
                st.markdown("#### Premium")
                st.write("Prix client affiché :", money(report["prix_premium"]))
                st.write("Prix minimum vendeur :", money(report["prix_minimum_premium"]))
                st.write("Coût achat max interne :", money(report["cout_achat_max_premium"]))

            st.divider()
            st.subheader("Message client prêt à envoyer")
            message_client = f"""Bonjour {client if client else ""},

J’ai vérifié les disponibilités pour votre moteur.

J’ai une option recommandée autour de {money(report["prix_recommande"])}.
Le marché actuel se situe avec des kilométrages entre {branch_text(km_branches["recommande"])} pour cette option.

J’ai aussi une option plus économique autour de {money(report["prix_economique"])} et une option premium autour de {money(report["prix_premium"])} selon le kilométrage et la disponibilité.

Les moteurs sont vérifiés selon les informations disponibles, avec garantie indiquée par le fournisseur.
"""
            st.text_area("Message", message_client, height=220)

            if st.button("💾 Sauvegarder l'offre", use_container_width=True):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = {
                    "date": now, "client": client, "type_client": type_client,
                    "vehicule_moteur": vehicule_moteur,
                    "vehicule_moteur_manuel": vehicule_moteur_manuel,
                    "vehicule_moteur_auto": vehicule_moteur_auto,
                    "search_title": report["df"]["search_title"].iloc[0] if "search_title" in report["df"].columns and len(report["df"]) > 0 else "",
                    "selected_model": report["df"]["selected_model"].iloc[0] if "selected_model" in report["df"].columns and len(report["df"]) > 0 else "",
                    "prix_economique": report["prix_economique"],
                    "prix_recommande": report["prix_recommande"],
                    "prix_premium": report["prix_premium"],
                    "prix_minimum_economique": report["prix_minimum_economique"],
                    "prix_minimum_recommande": report["prix_minimum_recommande"],
                    "prix_minimum_premium": report["prix_minimum_premium"],
                    "cout_achat_max_economique": report["cout_achat_max_economique"],
                    "cout_achat_max_recommande": report["cout_achat_max_recommande"],
                    "cout_achat_max_premium": report["cout_achat_max_premium"],
                    "marge_souhaitee": marge_souhaitee, "marge_minimale": marge_minimale,
                    "status": status, "date_rappel": date_rappel_value,
                    "raison_refus": raison_refus, "prix_final_vendu": prix_final_vendu,
                    "depot_recu": depot_recu, "fournisseur_choisi": fournisseur_choisi,
                    "note_commande": note_commande, "note_interne": note_interne,
                    "nb_total": report["nb_total"], "nb_valides": report["nb_valides"],
                    "nb_exclus": report["nb_exclus"], "prix_median_marche": report["median_price"],
                    "km_min": report["km_min"], "km_moyen": report["km_avg"], "km_max": report["km_max"],
                }
                add_offer(row)
                st.success("Offre sauvegardée.")

            with st.expander("Moteurs utilisés dans le calcul"):
                valid = report["valid"]
                cols = [c for c in ["page", "price", "km", "distance", "grade", "warranty", "fournisseur_confiance", "fournisseur_detecte", "search_title", "selected_model", "vehicule_moteur_auto", "raw"] if c in valid.columns]
                st.dataframe(valid[cols], use_container_width=True)

            with st.expander("Moteurs exclus par les filtres"):
                excluded = report["excluded"]
                cols = [c for c in ["page", "price", "km", "distance", "grade", "warranty", "raison_exclusion", "fournisseur_confiance", "fournisseur_detecte", "search_title", "selected_model", "vehicule_moteur_auto", "raw"] if c in excluded.columns]
                st.dataframe(excluded[cols], use_container_width=True)


with tabs[1]:
    st.subheader("À rappeler aujourd’hui")
    offers = load_offers()
    if len(offers) == 0:
        st.info("Aucune offre sauvegardée.")
    else:
        today_str = date.today().strftime("%Y-%m-%d")
        rappels = offers[(offers["status"] == "À rappeler") & (offers["date_rappel"].astype(str) <= today_str)].copy()
        if len(rappels) == 0:
            st.success("Aucun rappel dû aujourd’hui.")
        else:
            st.dataframe(rappels, use_container_width=True)


with tabs[2]:
    st.subheader("Historique des offres")
    offers = load_offers()
    if len(offers) == 0:
        st.info("Aucune offre sauvegardée.")
    else:
        search = st.text_input("Recherche historique")
        filtered = offers.copy()
        if search.strip():
            text = search.lower()
            filtered = filtered[filtered.apply(lambda row: text in " ".join(row.astype(str)).lower(), axis=1)]
        st.dataframe(filtered, use_container_width=True)

        st.divider()
        st.subheader("Modifier une offre")
        index_options = filtered.index.tolist()
        if len(index_options) > 0:
            selected_index = st.selectbox("Choisir une ligne", index_options)
            selected_row = offers.loc[selected_index]
            statuses = ["En attente", "Acceptée", "Refusée", "À rappeler"]
            current_status = selected_row["status"] if selected_row["status"] in statuses else "En attente"
            new_status = st.selectbox("Nouveau statut", statuses, index=statuses.index(current_status))
            new_date_rappel = st.text_input("Date rappel YYYY-MM-DD", str(selected_row.get("date_rappel", "")))
            new_raison_refus = st.text_input("Raison refus", str(selected_row.get("raison_refus", "")))
            new_prix_final = st.text_input("Prix final vendu", str(selected_row.get("prix_final_vendu", "")))
            new_depot = st.selectbox("Dépôt reçu", ["", "Non", "Oui"], index=0)
            new_fournisseur = st.text_input("Fournisseur choisi", str(selected_row.get("fournisseur_choisi", "")))
            new_note_interne = st.text_area("Note interne", str(selected_row.get("note_interne", "")))
            new_note_commande = st.text_area("Note commande", str(selected_row.get("note_commande", "")))
            if st.button("Mettre à jour l'offre"):
                update_offer(selected_index, {
                    "status": new_status, "date_rappel": new_date_rappel,
                    "raison_refus": new_raison_refus, "prix_final_vendu": new_prix_final,
                    "depot_recu": new_depot, "fournisseur_choisi": new_fournisseur,
                    "note_interne": new_note_interne, "note_commande": new_note_commande,
                })
                st.success("Offre mise à jour.")


with tabs[3]:
    st.subheader("Statistiques")
    offers = load_offers()
    if len(offers) == 0:
        st.info("Aucune donnée.")
    else:
        total = len(offers)
        accepted = len(offers[offers["status"] == "Acceptée"])
        refused = len(offers[offers["status"] == "Refusée"])
        waiting = len(offers[offers["status"] == "En attente"])
        close_rate = accepted / total * 100 if total > 0 else 0
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Offres total", total)
        c2.metric("Acceptées", accepted)
        c3.metric("Refusées", refused)
        c4.metric("En attente", waiting)
        c5.metric("Taux fermeture", percent_format(close_rate))
        st.divider()
        st.subheader("Offres par moteur")
        motor_counts = offers["vehicule_moteur"].fillna("").astype(str).value_counts()
        st.dataframe(motor_counts.reset_index(), use_container_width=True)


with tabs[4]:
    st.subheader("Messages rapides")
    nom = st.text_input("Nom client pour message", value=client)
    moteur_msg = st.text_input("Moteur pour message", value=vehicule_moteur_manuel)
    msg_type = st.selectbox("Type de message", ["Relance simple", "Client hésitant", "Option premium", "Option économique", "Refus poli"])

    if msg_type == "Relance simple":
        msg = f"""Bonjour {nom},

Je voulais simplement faire un suivi avec vous concernant le moteur {moteur_msg}.

J’ai encore des options disponibles présentement. Vous pouvez me revenir quand vous êtes prêt et je vais vérifier la meilleure disponibilité pour vous.
"""
    elif msg_type == "Client hésitant":
        msg = f"""Bonjour {nom},

Je comprends que vous voulez prendre le temps de comparer.

De mon côté, je regarde surtout le bon équilibre entre le prix, le kilométrage, la garantie et la provenance du moteur. Le moins cher n’est pas toujours le meilleur choix si le kilométrage ou la garantie ne sont pas intéressants.
"""
    elif msg_type == "Option premium":
        msg = f"""Bonjour {nom},

L’option premium est plus chère, mais elle est intéressante parce qu’elle vise les plus bas kilométrages disponibles et une meilleure qualité générale.

C’est l’option que je recommande si vous voulez garder le véhicule plus longtemps.
"""
    elif msg_type == "Option économique":
        msg = f"""Bonjour {nom},

J’ai aussi une option plus économique disponible.

Elle permet de réduire le prix, mais normalement le kilométrage est plus élevé. Ça peut être une bonne option si vous voulez réparer le véhicule au plus bas coût possible.
"""
    else:
        msg = f"""Bonjour {nom},

Aucun problème, je comprends votre décision.

Si jamais vous avez besoin d’une autre vérification ou d’une autre option plus tard, vous pouvez me réécrire et je vais regarder ce qui est disponible.
"""
    st.text_area("Message prêt à envoyer", msg, height=220)


with tabs[5]:
    st.subheader("Analyses sauvegardées")
    if not os.path.exists(ANALYSES_INDEX_FILE):
        st.info("Aucune analyse sauvegardée.")
    else:
        try:
            index_df = pd.read_csv(ANALYSES_INDEX_FILE)
            st.dataframe(index_df, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur lecture index analyses : {e}")


with tabs[6]:
    st.subheader("Mémoire moteur / client")
    st.info("Version 8 simplifiée : la mémoire détaillée est conservée dans les fichiers existants, mais cette version met l’accent sur les filtres stricts et les options de prix.")
