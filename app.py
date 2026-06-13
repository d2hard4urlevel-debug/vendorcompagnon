import os
import sys
import re
import subprocess
from datetime import datetime, date

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "VendorCompagnon"

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

SCORE_PRICE_POINTS = 45
SCORE_KM_POINTS = 35
SCORE_DISTANCE_POINTS = 15
SCORE_TRUST_POINTS = 5

for folder in [BASE_DIR, HIST_DIR, REPORTS_DIR, ANALYSES_DIR, MEMORY_DIR]:
    os.makedirs(folder, exist_ok=True)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🚗",
    layout="wide"
)


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
# FOURNISSEURS DE CONFIANCE
# ============================================================

TRUSTED_SUPPLIERS = [
    "pieces d'autos fernand begin",
    "pièces d'autos fernand begin",
    "fernand begin",
    "fernand bégin",
    "lkq"
]


def normalize_text(text):
    text = str(text).lower()
    text = text.replace("é", "e")
    text = text.replace("è", "e")
    text = text.replace("ê", "e")
    text = text.replace("à", "a")
    text = text.replace("â", "a")
    text = text.replace("î", "i")
    text = text.replace("ï", "i")
    text = text.replace("ô", "o")
    text = text.replace("û", "u")
    text = text.replace("ç", "c")
    return text


def is_trusted_supplier_text(text):
    clean = normalize_text(text)

    for supplier in TRUSTED_SUPPLIERS:
        if normalize_text(supplier) in clean:
            return True

    return False


def trusted_supplier_name(text):
    clean = normalize_text(text)

    if "lkq" in clean:
        return "LKQ"

    if "fernand" in clean and "begin" in clean:
        return "Pieces d'autos Fernand Begin"

    return ""


# ============================================================
# FILTRES STRICTS
# ============================================================

BAD_WORDS = [
    # Reman / rebuilt / pas comparable
    "reman", "remanufactured", "re-man", "re man",
    "rebuilt", "rebuild", "new rebuild", "new reman",
    "long block", "short block", "crate engine",
    "brand new",

    # Core / pour pièces
    "core", "running core", "need core", "needs core",
    "parts only", "for parts", "part only",
    "as is", "as-is",

    # Moteur pas testé / problème connu
    "no start", "non running", "does not run",
    "not tested", "needs test", "untested",
    "to be tested", "no keys",
    "bad", "nfg", "defective", "damaged",
    "problem", "problems", "issue", "issues",
    "needs repair", "repair needed",

    # Dommages physiques anglais
    "burnt", "burned", "fire", "fire damage",
    "flood", "water damage", "water damaged",
    "cracked", "broken", "hole", "damage",
    "collision damage", "damaged parts",
    "broken part", "broken parts",
    "broken piece", "broken pieces",
    "damaged component", "broken component",

    # Dommages physiques français
    "brisé", "brisee", "brisée", "briser",
    "cassé", "cassee", "cassée",
    "endommagé", "endommage", "endommagée",
    "piece brisee", "pièce brisée",
    "piece brisé", "pièce brisé",
    "piece casse", "pièce cassée",
    "pieces brisees", "pièces brisées",
    "pieces cassees", "pièces cassées",
    "composant brisé", "composant cassé",

    # Pièces manquantes / moteur incomplet
    "missing", "missing parts", "head gone",
    "no head", "heads removed", "head removed",
    "no intake", "no manifold", "no accessories",
    "bare", "bare engine",

    # Pièces manquantes français
    "manquant", "manquante",
    "pieces manquantes", "pièces manquantes",
    "piece manquante", "pièce manquante",
    "sans tete", "sans tête",
    "tete enlevee", "tête enlevée",
    "tete retiree", "tête retirée",
    "moteur incomplet",

    # Problèmes mécaniques anglais
    "misfire", "knock", "knocking",
    "low compression", "no compression",
    "bad compression", "compression issue",
    "seized", "locked up", "locked",
    "overheated", "overheat",
    "oil leak", "coolant leak",
    "smokes", "smoking",
    "timing issue", "timing problem",

    # Problèmes mécaniques français
    "raté", "rate",
    "cogne", "cognement",
    "compression basse", "pas de compression",
    "mauvaise compression",
    "saisi", "moteur saisi",
    "bloqué", "bloque",
    "surchauffe", "surchauffé", "surchauffe moteur",
    "fuite huile", "fuite d'huile",
    "fuite prestone", "fuite coolant",
    "fumee", "fumée", "boucanne",

    # Timing chain / chaîne à faire
    "timing chain", "timing chains",
    "timing chain issue", "timing chain problem",
    "timing chain noise", "timing chain rattle",
    "needs timing chain", "needs timing chains",
    "needs chain", "needs chains",
    "chain noise", "chain rattle",
    "chain problem", "chain issue",
    "chaines a faire", "chaînes à faire",
    "chaine a faire", "chaîne à faire",
    "chaine de timing", "chaîne de timing",
    "chaines de timing", "chaînes de timing",
    "chaine brisee", "chaîne brisée",
    "chaine etiree", "chaîne étirée",
    "chaine sautee", "chaîne sautée",
    "probleme de chaine", "problème de chaîne",
    "bruit de chaine", "bruit de chaîne",
    "guide de chaine", "guide de chaîne",
    "tendeur de chaine", "tendeur de chaîne",

    # Notes négatives fréquentes
    "do not sell", "do not use",
    "needs new head", "needs head",
    "needs timing", "needs chain",
    "needs rebuild", "needs rebuilt",
    "a reparer", "à réparer",
    "besoin reparation", "besoin réparation",
    "doit etre repare", "doit être réparé"
]

BAD_WORDS_EXACT = [
    "ns"
]


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

    if text == "":
        return False

    bad_warranty_values = [
        "nan",
        "none",
        "null",
        "n/a",
        "na",
        "no warranty",
        "no warr",
        "as is",
        "as-is",
        "0",
        "-"
    ]

    if text in bad_warranty_values:
        return False

    return True


def has_valid_distance(value):
    try:
        if pd.isna(value):
            return True

        distance = float(value)

        if distance <= 0:
            return True

        if distance > MAX_DISTANCE_KM:
            return False

        return True
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

    raw_lower = normalize_text(raw)

    negative_words_found = []

    for word in BAD_WORDS:
        if normalize_text(word) in raw_lower:
            negative_words_found.append(word)

    for word in BAD_WORDS_EXACT:
        pattern = r"\b" + re.escape(normalize_text(word)) + r"\b"
        if re.search(pattern, raw_lower):
            negative_words_found.append(word.upper())

    if negative_words_found:
        reasons.append("terme négatif : " + ", ".join(negative_words_found[:5]))

    return " | ".join(reasons)


def apply_strict_filters(df):
    df = df.copy()

    exclusion_reasons = []

    for _, row in df.iterrows():
        reason = get_filter_reason(row)
        exclusion_reasons.append(reason)

    df["raison_exclusion"] = exclusion_reasons
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

        if text == "":
            return None

        return float(text)
    except Exception:
        return None


def normalize_columns(df):
    df = df.copy()

    required_columns = [
        "price",
        "km",
        "distance",
        "grade",
        "warranty",
        "raw",
        "page",
        "search_title",
        "selected_model",
        "vehicule_moteur_auto"
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    df["price"] = df["price"].apply(clean_numeric)
    df["km"] = df["km"].apply(clean_numeric)
    df["distance"] = df["distance"].apply(clean_numeric)

    df = df[df["price"].notna()].copy()
    df = df[df["price"] > 0].copy()

    df["raw"] = df["raw"].fillna("").astype(str)
    df["warranty"] = df["warranty"].fillna("").astype(str)
    df["grade"] = df["grade"].fillna("").astype(str)

    return df


def get_distance_fee(distance):
    try:
        if pd.isna(distance):
            return 250

        distance = float(distance)

        if distance <= 100:
            return 0
        elif distance <= 300:
            return 100
        elif distance <= 600:
            return 250
        elif distance <= MAX_DISTANCE_KM:
            return 400
        else:
            return 9999

    except Exception:
        return 250


def get_vehicle_auto(df):
    possible_cols = ["vehicule_moteur_auto", "selected_model", "search_title"]

    for col in possible_cols:
        if col in df.columns:
            values = df[col].dropna().astype(str)
            values = values[values.str.strip() != ""]
            if len(values) > 0:
                return values.iloc[0].strip()

    return ""


def safe_min(series):
    try:
        values = pd.to_numeric(series, errors="coerce").dropna()
        if len(values) == 0:
            return None
        return values.min()
    except Exception:
        return None


def safe_mean(series):
    try:
        values = pd.to_numeric(series, errors="coerce").dropna()
        if len(values) == 0:
            return None
        return values.mean()
    except Exception:
        return None


def safe_max(series):
    try:
        values = pd.to_numeric(series, errors="coerce").dropna()
        if len(values) == 0:
            return None
        return values.max()
    except Exception:
        return None


# ============================================================
# COHÉRENCE DE MARCHÉ
# ============================================================

def add_supplier_columns(df):
    df = df.copy()
    df["fournisseur_confiance"] = df["raw"].apply(is_trusted_supplier_text)
    df["fournisseur_detecte"] = df["raw"].apply(trusted_supplier_name)
    return df


def apply_market_coherence_filter(valid):
    valid = valid.copy()

    valid["raison_coherence"] = ""
    valid["excluded_coherence"] = False

    trusted = valid[valid["fournisseur_confiance"] == True].copy()
    trusted_prices = trusted["price"].dropna().astype(float)

    if len(trusted_prices) < 2:
        return valid, {
            "trusted_market_used": False,
            "trusted_median": None,
            "trusted_min": None,
            "trusted_max": None,
            "market_low": None,
            "market_high": None
        }

    trusted_median = trusted_prices.median()
    trusted_min = trusted_prices.min()
    trusted_max = trusted_prices.max()

    if trusted_median <= 0:
        return valid, {
            "trusted_market_used": False,
            "trusted_median": None,
            "trusted_min": None,
            "trusted_max": None,
            "market_low": None,
            "market_high": None
        }

    spread_low = trusted_min / trusted_median
    spread_high = trusted_max / trusted_median

    # On utilise les fournisseurs de confiance comme base seulement si leurs prix se suivent.
    trusted_prices_follow = spread_low >= 0.80 and spread_high <= 1.20

    if not trusted_prices_follow:
        return valid, {
            "trusted_market_used": False,
            "trusted_median": trusted_median,
            "trusted_min": trusted_min,
            "trusted_max": trusted_max,
            "market_low": None,
            "market_high": None
        }

    market_low = trusted_median * 0.80
    market_high = trusted_median * 1.40

    for idx, row in valid.iterrows():
        price = row.get("price", None)

        try:
            price = float(price)
        except Exception:
            continue

        if price < market_low:
            valid.at[idx, "excluded_coherence"] = True
            valid.at[idx, "raison_coherence"] = (
                f"prix incohérent trop bas vs fournisseurs fiables "
                f"(base {money(trusted_median)})"
            )

        elif price > market_high:
            valid.at[idx, "excluded_coherence"] = True
            valid.at[idx, "raison_coherence"] = (
                f"prix incohérent trop haut vs fournisseurs fiables "
                f"(base {money(trusted_median)})"
            )

    return valid, {
        "trusted_market_used": True,
        "trusted_median": trusted_median,
        "trusted_min": trusted_min,
        "trusted_max": trusted_max,
        "market_low": market_low,
        "market_high": market_high
    }


# ============================================================
# SCORE MOTEUR CIBLE
# ============================================================

def score_inverse(value, min_value, max_value, points):
    try:
        value = float(value)
        min_value = float(min_value)
        max_value = float(max_value)

        if max_value == min_value:
            return points

        score = (max_value - value) / (max_value - min_value) * points

        if score < 0:
            score = 0

        if score > points:
            score = points

        return score
    except Exception:
        return 0


def calculate_target_scores(valid):
    valid = valid.copy()

    if len(valid) == 0:
        return valid

    price_min = valid["price"].min()
    price_max = valid["price"].max()

    km_min = valid["km"].min()
    km_max = valid["km"].max()

    distance_values = valid["distance"].dropna().astype(float)

    if len(distance_values) == 0:
        distance_min = 0
        distance_max = MAX_DISTANCE_KM
    else:
        distance_min = distance_values.min()
        distance_max = distance_values.max()

    score_prices = []
    score_kms = []
    score_distances = []
    score_trusts = []
    score_totals = []
    decisions = []

    for _, row in valid.iterrows():
        price_score = score_inverse(
            row.get("price", 0),
            price_min,
            price_max,
            SCORE_PRICE_POINTS
        )

        km_score = score_inverse(
            row.get("km", 0),
            km_min,
            km_max,
            SCORE_KM_POINTS
        )

        distance = row.get("distance", None)

        if pd.isna(distance):
            distance_score = SCORE_DISTANCE_POINTS * 0.50
        else:
            distance_score = score_inverse(
                distance,
                distance_min,
                distance_max,
                SCORE_DISTANCE_POINTS
            )

        trust_score = SCORE_TRUST_POINTS if row.get("fournisseur_confiance", False) else 0

        total = price_score + km_score + distance_score + trust_score

        score_prices.append(round(price_score, 1))
        score_kms.append(round(km_score, 1))
        score_distances.append(round(distance_score, 1))
        score_trusts.append(round(trust_score, 1))
        score_totals.append(round(total, 1))

    valid["score_prix"] = score_prices
    valid["score_km"] = score_kms
    valid["score_distance"] = score_distances
    valid["score_confiance"] = score_trusts
    valid["score_total"] = score_totals

    valid = valid.sort_values(
        by=["score_total", "fournisseur_confiance", "km", "price"],
        ascending=[False, False, True, True]
    ).copy()

    for i in range(len(valid)):
        if i == 0:
            decisions.append("MOTEUR CIBLE")
        elif i == 1:
            decisions.append("Alternative #1")
        elif i == 2:
            decisions.append("Alternative #2")
        else:
            decisions.append("Autre option")

    valid["decision"] = decisions

    return valid


def get_target_motor(scored):
    if len(scored) == 0:
        return None

    return scored.iloc[0]


def calculate_client_prices_from_target(target, marge_souhaitee, marge_minimale):
    if target is None:
        return {
            "prix_client": 0,
            "prix_minimum": 0,
            "cout_achat_max": 0,
            "transport": 0
        }

    supplier_price = float(target.get("price", 0))
    distance = target.get("distance", None)
    transport = get_distance_fee(distance)

    prix_client = round_to_5(supplier_price + transport + marge_souhaitee)
    prix_minimum = round_to_5(supplier_price + transport + marge_minimale)
    cout_achat_max = round_to_5(prix_minimum - transport - marge_minimale)

    return {
        "prix_client": prix_client,
        "prix_minimum": prix_minimum,
        "cout_achat_max": cout_achat_max,
        "transport": transport
    }


def explain_target_motor(target):
    if target is None:
        return "Aucun moteur cible disponible."

    reasons = []

    if target.get("score_prix", 0) >= SCORE_PRICE_POINTS * 0.70:
        reasons.append("prix fournisseur intéressant")

    if target.get("score_km", 0) >= SCORE_KM_POINTS * 0.60:
        reasons.append("kilométrage compétitif")

    if target.get("score_distance", 0) >= SCORE_DISTANCE_POINTS * 0.60:
        reasons.append("distance raisonnable")

    if target.get("fournisseur_confiance", False):
        reasons.append("fournisseur de confiance")

    if len(reasons) == 0:
        reasons.append("meilleur équilibre global parmi les moteurs valides")

    return ", ".join(reasons)


# ============================================================
# HISTORIQUE
# ============================================================

OFFER_COLUMNS = [
    "date",
    "client",
    "type_client",
    "vehicule_moteur",
    "vehicule_moteur_manuel",
    "vehicule_moteur_auto",
    "search_title",
    "selected_model",
    "prix_economique",
    "prix_recommande",
    "prix_premium",
    "prix_cible_client",
    "prix_minimum_cible",
    "cout_achat_max_cible",
    "marge_souhaitee",
    "marge_minimale",
    "status",
    "date_rappel",
    "raison_refus",
    "prix_final_vendu",
    "depot_recu",
    "fournisseur_choisi",
    "note_commande",
    "note_interne",
    "nb_total",
    "nb_valides",
    "nb_exclus",
    "prix_median_marche",
    "km_min",
    "km_moyen",
    "km_max",
    "cible_prix_fournisseur",
    "cible_km",
    "cible_distance",
    "cible_garantie",
    "cible_grade",
    "cible_score",
    "cible_fournisseur_confiance"
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


def load_offers_without_refresh():
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
    refresh_memory_files()


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
# MÉMOIRE MOTEUR / CLIENT
# ============================================================

def refresh_memory_files():
    df = load_offers_without_refresh()

    if len(df) == 0:
        safe_to_csv(pd.DataFrame(), MEMORY_MOTORS_FILE)
        safe_to_csv(pd.DataFrame(), MEMORY_CLIENTS_FILE)
        return

    motors = build_motor_memory(df)
    clients = build_client_memory(df)

    safe_to_csv(motors, MEMORY_MOTORS_FILE)
    safe_to_csv(clients, MEMORY_CLIENTS_FILE)


def build_motor_memory(df):
    rows = []

    df = df.copy()
    df["vehicule_moteur"] = df["vehicule_moteur"].fillna("").astype(str)

    for motor, group in df.groupby("vehicule_moteur"):
        if motor.strip() == "":
            continue

        total = len(group)
        accepted = len(group[group["status"] == "Acceptée"])
        refused = len(group[group["status"] == "Refusée"])
        waiting = len(group[group["status"] == "En attente"])
        callback = len(group[group["status"] == "À rappeler"])

        taux = (accepted / total * 100) if total > 0 else 0

        prix_cible = pd.to_numeric(group["prix_cible_client"], errors="coerce")
        prix_vendu = pd.to_numeric(group["prix_final_vendu"], errors="coerce")
        prix_refuse = pd.to_numeric(
            group[group["status"] == "Refusée"]["prix_cible_client"],
            errors="coerce"
        )

        raisons = group["raison_refus"].dropna().astype(str)
        raisons = raisons[raisons.str.strip() != ""]
        raison_principale = raisons.mode().iloc[0] if len(raisons) > 0 else ""

        derniere = group.sort_values("date").iloc[-1] if "date" in group.columns else group.iloc[-1]

        if taux >= 60:
            conseil = "Bon historique. Prix généralement accepté."
        elif refused > accepted:
            conseil = "Attention. Plusieurs refus. Vérifier prix cible ou disponibilité."
        else:
            conseil = "Historique neutre. Comparer avec le marché actuel."

        rows.append({
            "vehicule_moteur": motor,
            "offres_total": total,
            "offres_acceptees": accepted,
            "offres_refusees": refused,
            "offres_en_attente": waiting,
            "offres_a_rappeler": callback,
            "taux_acceptation": round(taux, 1),
            "prix_cible_moyen": prix_cible.mean(),
            "prix_cible_min": prix_cible.min(),
            "prix_cible_max": prix_cible.max(),
            "prix_accepte_moyen": prix_vendu.mean(),
            "prix_refuse_moyen": prix_refuse.mean(),
            "raison_refus_principale": raison_principale,
            "derniere_offre": derniere.get("date", ""),
            "conseil": conseil
        })

    return pd.DataFrame(rows)


def build_client_memory(df):
    rows = []

    df = df.copy()
    df["client"] = df["client"].fillna("").astype(str)

    for client, group in df.groupby("client"):
        if client.strip() == "":
            continue

        total = len(group)
        accepted = len(group[group["status"] == "Acceptée"])
        refused = len(group[group["status"] == "Refusée"])
        waiting = len(group[group["status"] == "En attente"])
        callback = len(group[group["status"] == "À rappeler"])

        taux = (accepted / total * 100) if total > 0 else 0

        prix_cible = pd.to_numeric(group["prix_cible_client"], errors="coerce")
        prix_vendu = pd.to_numeric(group["prix_final_vendu"], errors="coerce")

        type_client = group["type_client"].dropna().astype(str)
        type_client = type_client[type_client.str.strip() != ""]
        type_frequent = type_client.mode().iloc[0] if len(type_client) > 0 else ""

        moteurs = group["vehicule_moteur"].dropna().astype(str)
        moteurs = moteurs[moteurs.str.strip() != ""]
        moteurs_demandes = " | ".join(moteurs.tail(5).tolist())

        derniere = group.sort_values("date").iloc[-1] if "date" in group.columns else group.iloc[-1]

        if taux >= 60:
            conseil = "Client avec bon potentiel de fermeture."
        elif refused > accepted:
            conseil = "Client sensible au prix. Présenter le meilleur deal clairement."
        else:
            conseil = "Client à suivre. Garder une relance simple."

        rows.append({
            "client": client,
            "type_client_frequent": type_frequent,
            "offres_total": total,
            "offres_acceptees": accepted,
            "offres_refusees": refused,
            "offres_en_attente": waiting,
            "offres_a_rappeler": callback,
            "taux_acceptation": round(taux, 1),
            "prix_cible_moyen": prix_cible.mean(),
            "prix_accepte_moyen": prix_vendu.mean(),
            "moteurs_demandes": moteurs_demandes,
            "derniere_offre": derniere.get("date", ""),
            "dernier_statut": derniere.get("status", ""),
            "derniere_note": derniere.get("note_interne", ""),
            "conseil": conseil
        })

    return pd.DataFrame(rows)


def load_motor_memory():
    if not os.path.exists(MEMORY_MOTORS_FILE):
        return pd.DataFrame()

    try:
        return pd.read_csv(MEMORY_MOTORS_FILE)
    except Exception:
        return pd.DataFrame()


def load_client_memory():
    if not os.path.exists(MEMORY_CLIENTS_FILE):
        return pd.DataFrame()

    try:
        return pd.read_csv(MEMORY_CLIENTS_FILE)
    except Exception:
        return pd.DataFrame()


# ============================================================
# ANALYSE
# ============================================================

def calculate_report(df, marge_souhaitee, marge_minimale):
    df = normalize_columns(df)

    if len(df) == 0:
        return None

    df = add_supplier_columns(df)
    df = apply_strict_filters(df)

    valid_pre_coherence = df[df["excluded"] == False].copy()
    excluded_strict = df[df["excluded"] == True].copy()

    if len(valid_pre_coherence) == 0:
        return {
            "df": df,
            "valid": valid_pre_coherence,
            "excluded": excluded_strict,
            "scored": pd.DataFrame(),
            "target": None,
            "target_prices": {},
            "coherence_info": {},
            "error": "Aucun moteur valide après les filtres stricts."
        }

    coherent_checked, coherence_info = apply_market_coherence_filter(valid_pre_coherence)

    valid = coherent_checked[coherent_checked["excluded_coherence"] == False].copy()
    excluded_coherence = coherent_checked[coherent_checked["excluded_coherence"] == True].copy()

    if len(excluded_coherence) > 0:
        excluded_coherence["raison_exclusion"] = excluded_coherence["raison_coherence"]

    excluded = pd.concat([excluded_strict, excluded_coherence], ignore_index=True)

    if len(valid) == 0:
        return {
            "df": df,
            "valid": valid,
            "excluded": excluded,
            "scored": pd.DataFrame(),
            "target": None,
            "target_prices": {},
            "coherence_info": coherence_info,
            "error": "Aucun moteur valide après les filtres de cohérence."
        }

    scored = calculate_target_scores(valid)
    target = get_target_motor(scored)
    target_prices = calculate_client_prices_from_target(target, marge_souhaitee, marge_minimale)

    prices = valid["price"].dropna().astype(float)
    median_price = prices.median()
    avg_price = prices.mean()
    min_price = prices.min()
    max_price = prices.max()

    km_min = safe_min(valid["km"])
    km_avg = safe_mean(valid["km"])
    km_max = safe_max(valid["km"])

    avg_distance = safe_mean(valid["distance"])
    distance_fee = get_distance_fee(avg_distance)

    return {
        "df": df,
        "valid": valid,
        "excluded": excluded,
        "scored": scored,
        "target": target,
        "target_prices": target_prices,
        "coherence_info": coherence_info,
        "error": None,
        "nb_total": len(df),
        "nb_valides": len(valid),
        "nb_exclus": len(excluded),
        "median_price": median_price,
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "avg_distance": avg_distance,
        "distance_fee": distance_fee,
        "km_min": km_min,
        "km_avg": km_avg,
        "km_max": km_max,
        "vehicule_moteur_auto": get_vehicle_auto(df)
    }


# ============================================================
# SCRAPER
# ============================================================

def run_scraper():
    if not os.path.exists(SCRAPER_FILE):
        st.error(f"Fichier introuvable : {SCRAPER_FILE}")
        return False

    try:
        process = subprocess.run(
            [sys.executable, SCRAPER_FILE],
            capture_output=True,
            text=True
        )

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
        "nb_lignes": len(df)
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
st.caption("Analyse Car-Part Pro, prix de vente, moteur cible, historique client et mémoire moteur.")

with st.sidebar:
    st.header("Nouvelle offre")

    client = st.text_input("Nom du client")

    type_client = st.selectbox(
        "Type de client",
        ["Particulier", "Garage", "Dealer", "Recyclage", "Client régulier"]
    )

    vehicule_moteur_manuel = st.text_input(
        "Véhicule / moteur recherché",
        placeholder="Laisser vide pour utiliser le choix Car-Part automatiquement"
    )

    marge_souhaitee = st.number_input(
        "Marge souhaitée",
        min_value=0,
        max_value=10000,
        value=700,
        step=50
    )

    marge_minimale = st.number_input(
        "Marge minimale acceptable",
        min_value=0,
        max_value=10000,
        value=400,
        step=50
    )

    status = st.selectbox(
        "Statut de l'offre",
        ["En attente", "Acceptée", "Refusée", "À rappeler"]
    )

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


tabs = st.tabs([
    "Nouvelle offre",
    "À rappeler aujourd’hui",
    "Historique des offres",
    "Statistiques",
    "Messages",
    "Analyses sauvegardées",
    "Mémoire"
])


# ============================================================
# TAB 1 - NOUVELLE OFFRE
# ============================================================

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

    if run_button:
        with st.spinner("Ouverture de Car-Part Pro..."):
            success = run_scraper()

        if success:
            st.success("Analyse terminée. Recharge les résultats si nécessaire.")
            try:
                df_source = pd.read_csv(RESULTS_FILE)
            except Exception:
                pass

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
                cols = [
                    c for c in [
                        "page",
                        "price",
                        "km",
                        "distance",
                        "grade",
                        "warranty",
                        "fournisseur_confiance",
                        "fournisseur_detecte",
                        "raison_exclusion",
                        "search_title",
                        "selected_model",
                        "vehicule_moteur_auto",
                        "raw"
                    ]
                    if c in excluded.columns
                ]
                st.dataframe(excluded[cols], use_container_width=True)

        else:
            vehicule_moteur_auto = report["vehicule_moteur_auto"]
            vehicule_moteur = vehicule_moteur_manuel.strip() if vehicule_moteur_manuel.strip() else vehicule_moteur_auto

            if vehicule_moteur.strip() == "":
                vehicule_moteur = "Moteur non identifié"

            save_analysis_snapshot(report["df"], vehicule_moteur)

            target = report["target"]
            target_prices = report["target_prices"]
            scored = report["scored"]
            coherence_info = report["coherence_info"]

            st.subheader("Résumé du marché")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Résultats total", report["nb_total"])
            c2.metric("Utilisés après filtres", report["nb_valides"])
            c3.metric("Exclus", report["nb_exclus"])
            c4.metric("Prix médian fournisseur", money(report["median_price"]))

            c5, c6, c7, c8 = st.columns(4)

            c5.metric("Km minimum valide", km_format(report["km_min"]))
            c6.metric("Km moyen valide", km_format(report["km_avg"]))
            c7.metric("Km maximum valide", km_format(report["km_max"]))
            c8.metric("Transport moyen estimé", money(report["distance_fee"]))

            st.info(f"Modèle utilisé : **{vehicule_moteur}**")

            if coherence_info.get("trusted_market_used"):
                st.success(
                    f"Base fournisseurs fiables active : marché fiable autour de "
                    f"{money(coherence_info.get('trusted_median'))}. "
                    f"Prix acceptés environ {money(coherence_info.get('market_low'))} à "
                    f"{money(coherence_info.get('market_high'))}."
                )
            else:
                st.warning(
                    "Base fournisseurs fiables non utilisée : pas assez de fournisseurs fiables "
                    "ou leurs prix ne se suivent pas assez."
                )

            st.divider()

            st.subheader("🎯 Moteur cible recommandé")

            if target is not None:
                t1, t2, t3, t4, t5 = st.columns(5)

                t1.metric("Score", f"{target.get('score_total', 0):.1f}/100")
                t2.metric("Prix fournisseur", money(target.get("price", None)))
                t3.metric("Kilométrage", km_format(target.get("km", None)))
                t4.metric("Distance", km_format(target.get("distance", None)))
                t5.metric("Prix client conseillé", money(target_prices.get("prix_client", 0)))

                i1, i2, i3, i4 = st.columns(4)
                i1.write(f"Garantie : {str(target.get('warranty', ''))}")
                i2.write(f"Grade : {str(target.get('grade', ''))}")
                i3.write(f"Fournisseur fiable : {'Oui' if target.get('fournisseur_confiance', False) else 'Non'}")
                i4.write(f"Fournisseur détecté : {str(target.get('fournisseur_detecte', ''))}")

                st.write("Pourquoi ce moteur :", explain_target_motor(target))

                st.warning("Zone interne - ne pas montrer au client.")
                z1, z2, z3 = st.columns(3)
                z1.metric("Prix client conseillé", money(target_prices.get("prix_client", 0)))
                z2.metric("Prix minimum vendeur", money(target_prices.get("prix_minimum", 0)))
                z3.metric("Coût achat max interne", money(target_prices.get("cout_achat_max", 0)))

            st.divider()

            st.subheader("Alternatives classées par score")

            display_cols = [
                c for c in [
                    "decision",
                    "score_total",
                    "score_prix",
                    "score_km",
                    "score_distance",
                    "score_confiance",
                    "price",
                    "km",
                    "distance",
                    "warranty",
                    "grade",
                    "fournisseur_confiance",
                    "fournisseur_detecte",
                    "raw"
                ]
                if c in scored.columns
            ]

            st.dataframe(scored[display_cols].head(15), use_container_width=True)

            st.divider()

            st.subheader("Message client prêt à envoyer")

            message_client = f"""Bonjour {client if client else ""},

J’ai vérifié les disponibilités pour votre moteur.

Le meilleur deal que j’ai trouvé présentement serait autour de {money(target_prices.get("prix_client", 0))}.

Ce choix est basé sur le meilleur équilibre entre le prix fournisseur, le kilométrage, la distance et la fiabilité de la provenance.

Kilométrage du moteur ciblé : {km_format(target.get("km", None))}
Garantie indiquée : {str(target.get("warranty", ""))}
Grade : {str(target.get("grade", ""))}

Je peux aussi vérifier une alternative si vous voulez comparer.
"""

            st.text_area("Message", message_client, height=240)

            st.divider()

            if st.button("💾 Sauvegarder l'offre", use_container_width=True):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                row = {
                    "date": now,
                    "client": client,
                    "type_client": type_client,
                    "vehicule_moteur": vehicule_moteur,
                    "vehicule_moteur_manuel": vehicule_moteur_manuel,
                    "vehicule_moteur_auto": vehicule_moteur_auto,
                    "search_title": report["df"]["search_title"].iloc[0] if "search_title" in report["df"].columns and len(report["df"]) > 0 else "",
                    "selected_model": report["df"]["selected_model"].iloc[0] if "selected_model" in report["df"].columns and len(report["df"]) > 0 else "",
                    "prix_economique": "",
                    "prix_recommande": "",
                    "prix_premium": "",
                    "prix_cible_client": target_prices.get("prix_client", 0),
                    "prix_minimum_cible": target_prices.get("prix_minimum", 0),
                    "cout_achat_max_cible": target_prices.get("cout_achat_max", 0),
                    "marge_souhaitee": marge_souhaitee,
                    "marge_minimale": marge_minimale,
                    "status": status,
                    "date_rappel": date_rappel_value,
                    "raison_refus": raison_refus,
                    "prix_final_vendu": prix_final_vendu,
                    "depot_recu": depot_recu,
                    "fournisseur_choisi": fournisseur_choisi,
                    "note_commande": note_commande,
                    "note_interne": note_interne,
                    "nb_total": report["nb_total"],
                    "nb_valides": report["nb_valides"],
                    "nb_exclus": report["nb_exclus"],
                    "prix_median_marche": report["median_price"],
                    "km_min": report["km_min"],
                    "km_moyen": report["km_avg"],
                    "km_max": report["km_max"],
                    "cible_prix_fournisseur": target.get("price", ""),
                    "cible_km": target.get("km", ""),
                    "cible_distance": target.get("distance", ""),
                    "cible_garantie": target.get("warranty", ""),
                    "cible_grade": target.get("grade", ""),
                    "cible_score": target.get("score_total", ""),
                    "cible_fournisseur_confiance": "Oui" if target.get("fournisseur_confiance", False) else "Non"
                }

                add_offer(row)
                st.success("Offre sauvegardée.")

            st.divider()

            with st.expander("Moteurs utilisés dans le calcul"):
                valid = report["valid"]
                cols = [
                    c for c in [
                        "page",
                        "price",
                        "km",
                        "distance",
                        "grade",
                        "warranty",
                        "fournisseur_confiance",
                        "fournisseur_detecte",
                        "search_title",
                        "selected_model",
                        "vehicule_moteur_auto",
                        "raw"
                    ]
                    if c in valid.columns
                ]
                st.dataframe(valid[cols], use_container_width=True)

            with st.expander("Moteurs exclus par les filtres"):
                excluded = report["excluded"]
                cols = [
                    c for c in [
                        "page",
                        "price",
                        "km",
                        "distance",
                        "grade",
                        "warranty",
                        "fournisseur_confiance",
                        "fournisseur_detecte",
                        "raison_exclusion",
                        "search_title",
                        "selected_model",
                        "vehicule_moteur_auto",
                        "raw"
                    ]
                    if c in excluded.columns
                ]
                st.dataframe(excluded[cols], use_container_width=True)


# ============================================================
# TAB 2 - RAPPELS
# ============================================================

with tabs[1]:
    st.subheader("À rappeler aujourd’hui")

    offers = load_offers()

    if len(offers) == 0:
        st.info("Aucune offre sauvegardée.")
    else:
        today_str = date.today().strftime("%Y-%m-%d")
        rappels = offers[
            (offers["status"] == "À rappeler") &
            (offers["date_rappel"].astype(str) <= today_str)
        ].copy()

        if len(rappels) == 0:
            st.success("Aucun rappel dû aujourd’hui.")
        else:
            st.dataframe(rappels, use_container_width=True)


# ============================================================
# TAB 3 - HISTORIQUE
# ============================================================

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
            filtered = filtered[
                filtered.apply(
                    lambda row: text in " ".join(row.astype(str)).lower(),
                    axis=1
                )
            ]

        st.dataframe(filtered, use_container_width=True)

        st.divider()
        st.subheader("Modifier une offre")

        index_options = filtered.index.tolist()

        if len(index_options) > 0:
            selected_index = st.selectbox("Choisir une ligne", index_options)
            selected_row = offers.loc[selected_index]

            new_status = st.selectbox(
                "Nouveau statut",
                ["En attente", "Acceptée", "Refusée", "À rappeler"],
                index=["En attente", "Acceptée", "Refusée", "À rappeler"].index(
                    selected_row["status"] if selected_row["status"] in ["En attente", "Acceptée", "Refusée", "À rappeler"] else "En attente"
                )
            )

            new_date_rappel = st.text_input("Date rappel YYYY-MM-DD", str(selected_row.get("date_rappel", "")))
            new_raison_refus = st.text_input("Raison refus", str(selected_row.get("raison_refus", "")))
            new_prix_final = st.text_input("Prix final vendu", str(selected_row.get("prix_final_vendu", "")))
            new_depot = st.selectbox(
                "Dépôt reçu",
                ["", "Non", "Oui"],
                index=0
            )
            new_fournisseur = st.text_input("Fournisseur choisi", str(selected_row.get("fournisseur_choisi", "")))
            new_note_interne = st.text_area("Note interne", str(selected_row.get("note_interne", "")))
            new_note_commande = st.text_area("Note commande", str(selected_row.get("note_commande", "")))

            if st.button("Mettre à jour l'offre"):
                updates = {
                    "status": new_status,
                    "date_rappel": new_date_rappel,
                    "raison_refus": new_raison_refus,
                    "prix_final_vendu": new_prix_final,
                    "depot_recu": new_depot,
                    "fournisseur_choisi": new_fournisseur,
                    "note_interne": new_note_interne,
                    "note_commande": new_note_commande
                }

                update_offer(selected_index, updates)
                st.success("Offre mise à jour.")


# ============================================================
# TAB 4 - STATISTIQUES
# ============================================================

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
        callback = len(offers[offers["status"] == "À rappeler"])

        close_rate = accepted / total * 100 if total > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("Offres total", total)
        c2.metric("Acceptées", accepted)
        c3.metric("Refusées", refused)
        c4.metric("En attente", waiting)
        c5.metric("Taux fermeture", percent_format(close_rate))

        st.divider()

        st.subheader("Raisons de refus")

        refus = offers[offers["status"] == "Refusée"]

        if len(refus) > 0:
            reason_counts = refus["raison_refus"].fillna("").astype(str)
            reason_counts = reason_counts[reason_counts.str.strip() != ""].value_counts()
            st.dataframe(reason_counts.reset_index().rename(columns={"index": "raison", "count": "nombre"}))
        else:
            st.info("Aucun refus enregistré.")

        st.divider()

        st.subheader("Offres par moteur")

        motor_counts = offers["vehicule_moteur"].fillna("").astype(str).value_counts()
        st.dataframe(motor_counts.reset_index().rename(columns={"index": "moteur", "count": "nombre"}))


# ============================================================
# TAB 5 - MESSAGES
# ============================================================

with tabs[4]:
    st.subheader("Messages rapides")

    nom = st.text_input("Nom client pour message", value=client)
    moteur_msg = st.text_input("Moteur pour message", value=vehicule_moteur_manuel)

    msg_type = st.selectbox(
        "Type de message",
        [
            "Relance simple",
            "Client hésitant",
            "Meilleur deal",
            "Demande de dépôt",
            "Refus poli"
        ]
    )

    if msg_type == "Relance simple":
        msg = f"""Bonjour {nom},

Je voulais simplement faire un suivi avec vous concernant le moteur {moteur_msg}.

J’ai encore des options disponibles présentement. Vous pouvez me revenir quand vous êtes prêt et je vais vérifier le meilleur deal disponible.
"""
    elif msg_type == "Client hésitant":
        msg = f"""Bonjour {nom},

Je comprends que vous voulez prendre le temps de comparer.

De mon côté, je regarde surtout le meilleur équilibre entre le prix, le kilométrage, la garantie et la provenance du moteur. Le moins cher n’est pas toujours le meilleur deal si le kilométrage ou la provenance ne sont pas intéressants.
"""
    elif msg_type == "Meilleur deal":
        msg = f"""Bonjour {nom},

J’ai vérifié les options disponibles et je vous propose le meilleur deal que j’ai trouvé selon le prix, le kilométrage, la distance et la provenance.

C’est l’option que je prioriserais présentement si vous voulez un bon équilibre qualité/prix.
"""
    elif msg_type == "Demande de dépôt":
        msg = f"""Bonjour {nom},

Pour sécuriser le moteur, il faudrait laisser un dépôt.

Une fois le dépôt reçu, on peut bloquer l’option et avancer avec la commande.
"""
    else:
        msg = f"""Bonjour {nom},

Aucun problème, je comprends votre décision.

Si jamais vous avez besoin d’une autre vérification ou d’une autre option plus tard, vous pouvez me réécrire et je vais regarder ce qui est disponible.
"""

    st.text_area("Message prêt à envoyer", msg, height=220)


# ============================================================
# TAB 6 - ANALYSES SAUVEGARDÉES
# ============================================================

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


# ============================================================
# TAB 7 - MÉMOIRE
# ============================================================

with tabs[6]:
    st.subheader("Mémoire moteur / client")

    if st.button("Reconstruire la mémoire"):
        refresh_memory_files()
        st.success("Mémoire reconstruite.")

    mem_tabs = st.tabs(["Mémoire moteurs", "Mémoire clients"])

    with mem_tabs[0]:
        motors = load_motor_memory()

        if len(motors) == 0:
            st.info("Aucune mémoire moteur.")
        else:
            search_motor = st.text_input("Recherche moteur mémoire")

            if search_motor.strip():
                motors_display = motors[
                    motors.apply(
                        lambda row: search_motor.lower() in " ".join(row.astype(str)).lower(),
                        axis=1
                    )
                ]
            else:
                motors_display = motors

            st.dataframe(motors_display, use_container_width=True)

    with mem_tabs[1]:
        clients_memory = load_client_memory()

        if len(clients_memory) == 0:
            st.info("Aucune mémoire client.")
        else:
            search_client = st.text_input("Recherche client mémoire")

            if search_client.strip():
                clients_display = clients_memory[
                    clients_memory.apply(
                        lambda row: search_client.lower() in " ".join(row.astype(str)).lower(),
                        axis=1
                    )
                ]
            else:
                clients_display = clients_memory

            st.dataframe(clients_display, use_container_width=True)