import os
import sys
import re
import subprocess
from datetime import datetime, date

import pandas as pd
import streamlit as st

APP_NAME = "VendorCompagnon V9 - Moteur cible"
BASE_DIR = os.path.join(os.getcwd(), "carpart_app")
HIST_DIR = os.path.join(BASE_DIR, "historiques")
RESULTS_FILE = os.path.join(BASE_DIR, "resultats.csv")
OFFERS_FILE = os.path.join(HIST_DIR, "offres_clients.csv")
SCRAPER_FILE = "carpart_scraper.py"
MAX_DISTANCE_KM = 1000

for folder in [BASE_DIR, HIST_DIR]:
    os.makedirs(folder, exist_ok=True)

st.set_page_config(page_title=APP_NAME, page_icon="🚗", layout="wide")

TRUSTED_SUPPLIERS = [
    "lkq", "pieces d'autos fernand begin", "pièces d'autos fernand begin",
    "fernand begin", "fernand bégin"
]

BAD_WORDS = [
    "reman", "remanufactured", "re-man", "re man", "rebuilt", "rebuild",
    "new rebuild", "new reman", "long block", "short block", "crate engine",
    "brand new", "core", "running core", "need core", "needs core",
    "parts only", "for parts", "part only", "as is", "as-is",
    "no start", "non running", "does not run", "not tested", "needs test",
    "untested", "to be tested", "no keys", "bad", "nfg", "defective",
    "damaged", "problem", "problems", "issue", "issues", "needs repair",
    "repair needed", "burnt", "burned", "fire", "fire damage", "flood",
    "water damage", "water damaged", "cracked", "broken", "hole", "damage",
    "collision damage", "broken part", "broken parts", "damaged component",
    "brisé", "brisee", "brisée", "cassé", "cassée", "endommagé",
    "piece brisee", "pièce brisée", "pièce cassée", "pieces brisees",
    "missing", "missing parts", "head gone", "no head", "head removed",
    "no intake", "no manifold", "no accessories", "bare", "bare engine",
    "manquant", "pièce manquante", "pièces manquantes", "moteur incomplet",
    "misfire", "knock", "knocking", "low compression", "no compression",
    "bad compression", "seized", "locked up", "overheated", "oil leak",
    "coolant leak", "smokes", "smoking", "timing issue", "timing problem",
    "timing chain", "needs timing chain", "chain noise", "chain rattle",
    "chaines a faire", "chaînes à faire", "chaine a faire", "chaîne à faire",
    "chaine brisee", "chaîne brisée", "chaine etiree", "chaîne étirée",
    "tendeur de chaine", "tendeur de chaîne", "guide de chaine", "guide de chaîne",
    "do not sell", "do not use", "needs new head", "needs head",
    "needs timing", "needs rebuild", "needs rebuilt", "a reparer", "à réparer"
]
BAD_WORDS_EXACT = ["ns"]

OFFER_COLUMNS = [
    "date", "client", "type_client", "vehicule_moteur", "prix_cible_client",
    "prix_minimum_cible", "cout_achat_max_cible", "marge_souhaitee",
    "marge_minimale", "status", "date_rappel", "raison_refus", "note_interne",
    "nb_total", "nb_valides", "nb_exclus", "prix_median_marche",
    "cible_prix_fournisseur", "cible_km", "cible_distance", "cible_garantie",
    "cible_grade", "cible_score", "cible_fournisseur_confiance"
]

def normalize_text(text):
    text = str(text).lower()
    for old, new in {"é":"e","è":"e","ê":"e","à":"a","â":"a","î":"i","ï":"i","ô":"o","û":"u","ç":"c"}.items():
        text = text.replace(old, new)
    return text

def money(value):
    try:
        if pd.isna(value): return "-"
        return f"{float(value):,.0f} $".replace(",", " ")
    except Exception:
        return "-"

def km_format(value):
    try:
        if pd.isna(value): return "-"
        return f"{float(value):,.0f} km".replace(",", " ")
    except Exception:
        return "-"

def clean_numeric(value):
    try:
        if pd.isna(value): return None
        text = str(value).replace("$", "").replace(",", "").replace("km", "")
        text = text.replace("KM", "").replace("K", "").replace(" ", "").strip()
        if text == "" or text.lower() == "call": return None
        return float(text)
    except Exception:
        return None

def round_to_5(value):
    try: return int(round(float(value) / 5) * 5)
    except Exception: return 0

def is_trusted_supplier(raw):
    clean = normalize_text(raw)
    return any(normalize_text(s) in clean for s in TRUSTED_SUPPLIERS)

def supplier_name(raw):
    clean = normalize_text(raw)
    if "lkq" in clean: return "LKQ"
    if "fernand" in clean and "begin" in clean: return "Pieces d'autos Fernand Begin"
    return ""

def has_bad_word(raw):
    clean = normalize_text(raw)
    if any(normalize_text(w) in clean for w in BAD_WORDS): return True
    for w in BAD_WORDS_EXACT:
        if re.search(r"\b" + re.escape(normalize_text(w)) + r"\b", clean): return True
    return False

def bad_word_list(raw):
    clean = normalize_text(raw); found = []
    for w in BAD_WORDS:
        if normalize_text(w) in clean: found.append(w)
    for w in BAD_WORDS_EXACT:
        if re.search(r"\b" + re.escape(normalize_text(w)) + r"\b", clean): found.append(w.upper())
    return ", ".join(found[:6])

def valid_warranty(value):
    text = str(value).strip().lower()
    return text not in ["", "nan", "none", "null", "n/a", "na", "no warranty", "no warr", "as is", "as-is", "0", "-"]

def distance_fee(distance, trusted=False):
    if trusted: return 0
    try:
        if pd.isna(distance): return 250
        d = float(distance)
        if d <= 40: return 50
        if d <= 150: return round_to_5(d)
        if d <= 400: return 250
        if d <= MAX_DISTANCE_KM: return 500
        return None
    except Exception:
        return 250

def normalize_columns(df):
    df = df.copy()
    for col in ["page", "price", "km", "distance", "grade", "warranty", "raw", "search_title", "selected_model", "vehicule_moteur_auto"]:
        if col not in df.columns: df[col] = ""
    df["price"] = df["price"].apply(clean_numeric)
    df["km"] = df["km"].apply(clean_numeric)
    df["distance"] = df["distance"].apply(clean_numeric)
    df["raw"] = df["raw"].fillna("").astype(str)
    df["warranty"] = df["warranty"].fillna("").astype(str)
    df["grade"] = df["grade"].fillna("").astype(str)
    df = df[df["price"].notna()].copy()
    df = df[df["price"] > 0].copy()
    return df

def filter_reason(row):
    reasons = []
    raw = str(row.get("raw", "")).strip()
    try:
        km = float(row.get("km", 0))
        if pd.isna(km) or km <= 0 or km > 500000: reasons.append("kilométrage inconnu ou invalide")
    except Exception:
        reasons.append("kilométrage inconnu ou invalide")
    if len(raw) < 40: reasons.append("description absente ou trop courte")
    if not valid_warranty(row.get("warranty", "")): reasons.append("garantie absente")
    if has_bad_word(raw): reasons.append("terme négatif : " + bad_word_list(raw))
    trusted = is_trusted_supplier(raw)
    if distance_fee(row.get("distance"), trusted) is None: reasons.append(f"distance trop élevée : plus de {MAX_DISTANCE_KM} km")
    return " | ".join(reasons)

def prepare_data(df):
    df = normalize_columns(df)
    df["fournisseur_confiance"] = df["raw"].apply(is_trusted_supplier)
    df["fournisseur_detecte"] = df["raw"].apply(supplier_name)
    df["raison_exclusion"] = df.apply(filter_reason, axis=1)
    df["excluded"] = df["raison_exclusion"].astype(str).str.strip() != ""
    valid = df[df["excluded"] == False].copy()
    excluded = df[df["excluded"] == True].copy()
    valid["livraison"] = valid.apply(lambda r: distance_fee(r.get("distance"), r.get("fournisseur_confiance", False)), axis=1)
    valid["cout_reel"] = valid["price"] + valid["livraison"]
    return valid, excluded, df

def apply_market_coherence_filter(valid):
    valid = valid.copy(); valid["excluded_coherence"] = False; valid["raison_coherence"] = ""
    trusted_prices = valid[valid["fournisseur_confiance"] == True]["price"].dropna().astype(float)
    info = {"trusted_market_used": False, "trusted_median": None, "market_low": None, "market_high": None}
    if len(trusted_prices) < 2: return valid, info
    med = trusted_prices.median(); mn = trusted_prices.min(); mx = trusted_prices.max()
    info["trusted_median"] = med
    if med <= 0 or mn / med < 0.80 or mx / med > 1.20: return valid, info
    low = med * 0.80; high = med * 1.40
    info.update({"trusted_market_used": True, "market_low": low, "market_high": high})
    for idx, row in valid.iterrows():
        price = float(row.get("price", 0))
        if price < low:
            valid.at[idx, "excluded_coherence"] = True
            valid.at[idx, "raison_coherence"] = f"prix incohérent trop bas vs fournisseurs fiables (base {money(med)})"
        elif price > high:
            valid.at[idx, "excluded_coherence"] = True
            valid.at[idx, "raison_coherence"] = f"prix incohérent trop haut vs fournisseurs fiables (base {money(med)})"
    return valid, info

def score_inverse(value, min_value, max_value, points):
    try:
        if max_value == min_value: return points
        score = (float(max_value) - float(value)) / (float(max_value) - float(min_value)) * points
        return max(0, min(points, score))
    except Exception:
        return 0

def calculate_scores(valid):
    valid = valid.copy()
    if len(valid) == 0: return valid
    pmin, pmax = valid["price"].min(), valid["price"].max()
    kmin, kmax = valid["km"].min(), valid["km"].max()
    dvals = valid["distance"].dropna().astype(float)
    dmin, dmax = (0, MAX_DISTANCE_KM) if len(dvals) == 0 else (dvals.min(), dvals.max())
    valid["score_prix"] = valid["price"].apply(lambda x: round(score_inverse(x, pmin, pmax, 45), 1))
    valid["score_km"] = valid["km"].apply(lambda x: round(score_inverse(x, kmin, kmax, 35), 1))
    valid["score_distance"] = valid["distance"].apply(lambda x: round(7.5 if pd.isna(x) else score_inverse(x, dmin, dmax, 15), 1))
    valid["score_confiance"] = valid["fournisseur_confiance"].apply(lambda x: 5 if x else 0)
    valid["score_total"] = valid["score_prix"] + valid["score_km"] + valid["score_distance"] + valid["score_confiance"]
    valid = valid.sort_values(by=["score_total", "fournisseur_confiance", "km", "price"], ascending=[False, False, True, True]).copy()
    valid["decision"] = ["MOTEUR CIBLE" if i == 0 else f"Alternative #{i}" if i < 3 else "Autre option" for i in range(len(valid))]
    return valid

def target_prices(target, marge_souhaitee, marge_minimale):
    cout = float(target.get("price", 0)) + float(target.get("livraison", 0))
    return {"cout_reel": round_to_5(cout), "prix_client": round_to_5(cout + marge_souhaitee), "prix_minimum": round_to_5(cout + marge_minimale), "cout_achat_max": round_to_5(cout)}

def explain_target(t):
    reasons = []
    if t.get("score_prix", 0) >= 31.5: reasons.append("prix fournisseur intéressant")
    if t.get("score_km", 0) >= 21: reasons.append("kilométrage compétitif")
    if t.get("score_distance", 0) >= 9: reasons.append("distance raisonnable")
    if t.get("fournisseur_confiance", False): reasons.append("fournisseur de confiance")
    return ", ".join(reasons) if reasons else "meilleur équilibre global parmi les moteurs valides"

def load_offers():
    if not os.path.exists(OFFERS_FILE): return pd.DataFrame(columns=OFFER_COLUMNS)
    try:
        df = pd.read_csv(OFFERS_FILE)
        for c in OFFER_COLUMNS:
            if c not in df.columns: df[c] = ""
        return df[OFFER_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=OFFER_COLUMNS)

def save_offer(row):
    df = load_offers()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    safe_to_csv(df, OFFERS_FILE)

def get_vehicle_auto(df):
    for col in ["vehicule_moteur_auto", "selected_model", "search_title"]:
        if col in df.columns:
            vals = df[col].dropna().astype(str); vals = vals[vals.str.strip() != ""]
            if len(vals) > 0: return vals.iloc[0].strip()
    return ""

def run_scraper():
    if not os.path.exists(SCRAPER_FILE):
        st.error(f"Fichier introuvable : {SCRAPER_FILE}"); return False
    r = subprocess.run([sys.executable, SCRAPER_FILE], capture_output=True, text=True)
    if r.returncode != 0:
        st.error("Erreur pendant l’analyse Car-Part."); st.code(r.stderr); return False
    return True

st.title("🚗 VendorCompagnon")
st.caption("Version 9 — Moteur cible avec score automatique.")

with st.sidebar:
    st.header("Nouvelle offre")
    client = st.text_input("Nom du client")
    type_client = st.selectbox("Type de client", ["Particulier", "Garage", "Dealer", "Recyclage", "Client régulier"])
    vehicule_moteur_manuel = st.text_input("Véhicule / moteur recherché")
    marge_souhaitee = st.number_input("Marge souhaitée", min_value=0, max_value=10000, value=700, step=50)
    marge_minimale = st.number_input("Marge minimale acceptable", min_value=0, max_value=10000, value=400, step=50)
    status = st.selectbox("Statut", ["En attente", "Acceptée", "Refusée", "À rappeler"])
    date_rappel_value = st.date_input("Date de rappel", value=date.today()).strftime("%Y-%m-%d") if status == "À rappeler" else ""
    raison_refus = st.text_input("Raison du refus") if status == "Refusée" else ""
    note_interne = st.text_area("Note interne")
    st.divider()
    run_button = st.button("🔎 Analyser Car-Part", use_container_width=True)
    uploaded_file = st.file_uploader("Ou importer un CSV", type=["csv"])

tabs = st.tabs(["Nouvelle offre", "Historique", "Moteurs exclus", "Messages"])

if run_button:
    with st.spinner("Ouverture de Car-Part Pro..."):
        if run_scraper(): st.success("Analyse terminée.")

with tabs[0]:
    df_source = pd.read_csv(uploaded_file) if uploaded_file is not None else (pd.read_csv(RESULTS_FILE) if os.path.exists(RESULTS_FILE) else None)
    if df_source is None:
        st.info("Clique sur Analyser Car-Part ou importe un CSV.")
    else:
        valid_pre, excluded_strict, full_df = prepare_data(df_source)
        checked, info = apply_market_coherence_filter(valid_pre)
        valid = checked[checked["excluded_coherence"] == False].copy()
        excluded_coherence = checked[checked["excluded_coherence"] == True].copy()
        if len(excluded_coherence) > 0: excluded_coherence["raison_exclusion"] = excluded_coherence["raison_coherence"]
        excluded = pd.concat([excluded_strict, excluded_coherence], ignore_index=True)
        vehicle = vehicule_moteur_manuel.strip() or get_vehicle_auto(full_df) or "Moteur non identifié"

        st.subheader("Résumé du marché")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Résultats total", len(full_df)); c2.metric("Utilisés après filtres", len(valid)); c3.metric("Exclus", len(excluded)); c4.metric("Prix médian fournisseur", money(valid["price"].median() if len(valid) else None))
        st.info(f"Modèle utilisé : **{vehicle}**")
        if info.get("trusted_market_used"):
            st.success(f"Base fournisseurs fiables active : {money(info.get('trusted_median'))}. Range {money(info.get('market_low'))} à {money(info.get('market_high'))}.")
        else:
            st.warning("Base fournisseurs fiables non utilisée.")
        if len(valid) == 0:
            st.error("Aucun moteur valide après les filtres.")
        else:
            scored = calculate_scores(valid)
            target = scored.iloc[0]
            prices = target_prices(target, marge_souhaitee, marge_minimale)
            st.divider(); st.subheader("🎯 Moteur cible recommandé")
            t1, t2, t3, t4, t5 = st.columns(5)
            t1.metric("Score", f"{target.get('score_total', 0):.1f}/100"); t2.metric("Prix fournisseur", money(target.get("price"))); t3.metric("Kilométrage", km_format(target.get("km"))); t4.metric("Distance", km_format(target.get("distance"))); t5.metric("Prix client conseillé", money(prices.get("prix_client")))
            i1, i2, i3, i4 = st.columns(4)
            i1.write(f"Garantie : {str(target.get('warranty', ''))}"); i2.write(f"Grade : {str(target.get('grade', ''))}"); i3.write(f"Fournisseur fiable : {'Oui' if target.get('fournisseur_confiance', False) else 'Non'}"); i4.write(f"Fournisseur détecté : {str(target.get('fournisseur_detecte', ''))}")
            st.write("Pourquoi ce moteur :", explain_target(target))
            z1, z2, z3 = st.columns(3); z1.metric("Prix client conseillé", money(prices.get("prix_client"))); z2.metric("Prix minimum vendeur", money(prices.get("prix_minimum"))); z3.metric("Coût achat max interne", money(prices.get("cout_achat_max")))
            st.subheader("Alternatives classées par score")
            cols = [c for c in ["decision", "score_total", "score_prix", "score_km", "score_distance", "score_confiance", "price", "livraison", "cout_reel", "km", "distance", "warranty", "grade", "fournisseur_confiance", "fournisseur_detecte", "raw"] if c in scored.columns]
            st.dataframe(scored[cols].head(20), use_container_width=True)
            msg = f"""Bonjour {client if client else ""},

J’ai vérifié les disponibilités pour votre moteur.

Le meilleur deal que j’ai trouvé présentement serait autour de {money(prices.get("prix_client"))}.

Ce choix est basé sur le meilleur équilibre entre le prix fournisseur, le kilométrage, la distance et la fiabilité de la provenance.

Kilométrage du moteur ciblé : {km_format(target.get("km"))}
Garantie indiquée : {str(target.get("warranty", ""))}
Grade : {str(target.get("grade", ""))}
"""
            st.text_area("Message client", msg, height=220)
            if st.button("💾 Sauvegarder l'offre", use_container_width=True):
                save_offer({"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "client": client, "type_client": type_client, "vehicule_moteur": vehicle, "prix_cible_client": prices.get("prix_client"), "prix_minimum_cible": prices.get("prix_minimum"), "cout_achat_max_cible": prices.get("cout_achat_max"), "marge_souhaitee": marge_souhaitee, "marge_minimale": marge_minimale, "status": status, "date_rappel": date_rappel_value, "raison_refus": raison_refus, "note_interne": note_interne, "nb_total": len(full_df), "nb_valides": len(valid), "nb_exclus": len(excluded), "prix_median_marche": valid["price"].median(), "cible_prix_fournisseur": target.get("price"), "cible_km": target.get("km"), "cible_distance": target.get("distance"), "cible_garantie": target.get("warranty"), "cible_grade": target.get("grade"), "cible_score": target.get("score_total"), "cible_fournisseur_confiance": "Oui" if target.get("fournisseur_confiance", False) else "Non"})
                st.success("Offre sauvegardée.")

with tabs[1]:
    st.subheader("Historique")
    offers = load_offers()
    st.dataframe(offers, use_container_width=True) if len(offers) else st.info("Aucune offre sauvegardée.")

with tabs[2]:
    st.subheader("Moteurs exclus")
    df_source = pd.read_csv(uploaded_file) if uploaded_file is not None else (pd.read_csv(RESULTS_FILE) if os.path.exists(RESULTS_FILE) else None)
    if df_source is None: st.info("Aucun résultat chargé.")
    else:
        valid_pre, excluded_strict, full_df = prepare_data(df_source)
        checked, info = apply_market_coherence_filter(valid_pre)
        excluded_coherence = checked[checked["excluded_coherence"] == True].copy()
        if len(excluded_coherence) > 0: excluded_coherence["raison_exclusion"] = excluded_coherence["raison_coherence"]
        excluded = pd.concat([excluded_strict, excluded_coherence], ignore_index=True)
        st.dataframe(excluded[[c for c in ["price", "km", "distance", "warranty", "grade", "raison_exclusion", "raw"] if c in excluded.columns]], use_container_width=True)

with tabs[3]:
    st.subheader("Messages rapides")
    nom = st.text_input("Nom client message", value=client)
    msg_type = st.selectbox("Type", ["Relance", "Client trouve trop cher", "Demander comparaison", "Dépôt"])
    if msg_type == "Relance": msg = f"Bonjour {nom},\n\nJe fais un petit suivi concernant le moteur. Je peux revérifier les disponibilités aujourd’hui si vous voulez avancer."
    elif msg_type == "Client trouve trop cher": msg = f"Bonjour {nom},\n\nJe comprends votre point. Il y a moins cher, mais souvent avec plus de kilométrage, moins bonne garantie ou des notes moins intéressantes."
    elif msg_type == "Demander comparaison": msg = f"Bonjour {nom},\n\nEnvoyez-moi le prix, le kilométrage et la garantie de l’autre option, et je vais comparer correctement pour voir si je peux faire mieux."
    else: msg = f"Bonjour {nom},\n\nPour réserver le moteur, il faudrait laisser un dépôt. Une fois reçu, je peux bloquer l’option et avancer avec la commande."
    st.text_area("Message", msg, height=220)
