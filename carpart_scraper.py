from playwright.sync_api import sync_playwright
from pathlib import Path
import csv
import re
import time

START_URL = "https://cpprohomeky.car-part.com/pro?"

OUTPUT_DIR = Path("carpart_app")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_FILE = OUTPUT_DIR / "resultats.csv"

BAD_WORDS = [
    "reman", "long block", "new reman", "rebuilt",
    "core", "running core", "need core",
    "no start", "parts only", "needs test", "not tested",
    "burnt", "cracked", "bad", "nfg", "head gone",
    "misfire", "needs new head", "do not sell"
]


def clean(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize(text):
    return clean(text).lower().replace(" ", "").replace("-", "").replace("_", "")


def extract_price(text):
    match = re.search(r"\$ ?([0-9]{3,5}(?:\.[0-9]{2})?)", text)
    if match:
        return float(match.group(1))
    return None


def extract_km(text):
    match = re.search(r"--km--\s*([0-9,]{2,9})", text)
    if match:
        try:
            return int(match.group(1).replace(",", ""))
        except:
            return None
    return None


def extract_grade(text):
    match = re.search(r"\b(A|B|C|X|AFT)\b", text)
    if match:
        return match.group(1)
    return ""


def extract_warranty(text):
    match = re.search(
        r"\b(30 Day|60 Day|90 Day|91 Day|100 Day|101 Day|120 Day|6 Month|1 Year)\b",
        text,
        re.I
    )
    if match:
        return match.group(1)
    return ""


def is_bad(text):
    low = text.lower()
    return any(word in low for word in BAD_WORDS)


def safe_int(text):
    text = clean(text)
    text = text.replace(",", "")
    text = re.sub(r"[^0-9]", "", text)

    if text == "":
        return None

    try:
        return int(text)
    except:
        return None


def is_distance_header(header):
    h = normalize(header)

    if "delivery" in h:
        return False

    if "deliver" in h:
        return False

    valid_headers = [
        "dist",
        "distkm",
        "distance",
        "distancekm"
    ]

    return h in valid_headers


def find_distance_column(page):
    rows = page.locator("table tr")
    max_rows = min(rows.count(), 12)

    for r in range(max_rows):
        try:
            row = rows.nth(r)
            cells = row.locator("th, td")
            cell_count = cells.count()

            headers = []

            for c in range(cell_count):
                headers.append(clean(cells.nth(c).inner_text()))

            for index, header in enumerate(headers):
                if is_distance_header(header):
                    print(f"VRAIE colonne distance détectée : index {index} / header '{header}'")
                    return index

        except:
            continue

    print("Aucune vraie colonne distance détectée. Utilisation du mode automatique par ligne.")
    return None


def get_cells_from_row(row):
    cells_text = []

    try:
        cells = row.locator("td")
        cell_count = cells.count()

        for c in range(cell_count):
            cells_text.append(clean(cells.nth(c).inner_text()))
    except:
        pass

    return cells_text


def extract_distance_by_column(cells_text, distance_index):
    if distance_index is None:
        return None

    if distance_index >= len(cells_text):
        return None

    value = safe_int(cells_text[distance_index])

    if value is None:
        return None

    if 0 <= value <= 5000:
        return value

    return None


def extract_distance_automatic(cells_text, raw_text):
    price = extract_price(raw_text)
    motor_km = extract_km(raw_text)

    candidates = []

    for index, cell in enumerate(cells_text):
        cell_clean = clean(cell)

        if cell_clean == "":
            continue

        if "$" in cell_clean:
            continue

        value = safe_int(cell_clean)

        if value is None:
            continue

        if 1980 <= value <= 2035:
            continue

        if motor_km is not None and abs(value - motor_km) < 5:
            continue

        if price is not None and abs(value - price) < 5:
            continue

        if 1 <= value <= 5000:
            candidates.append((index, value, cell_clean))

    if len(candidates) == 0:
        return None

    return candidates[0][1]


def capture_selected_model_info(page):
    """
    Capture le titre de recherche et le choix radio sélectionné sur la page Car-Part.
    Exemple :
    search_title = 2013 Hyundai Elantra Engine
    selected_model = (1.8L, VIN E, 8th digit), Cpe, California emissions (PZEV)
    vehicule_moteur_auto = 2013 Hyundai Elantra Engine - (1.8L, VIN E, 8th digit), Cpe, California emissions (PZEV)
    """

    try:
        info = page.evaluate(
            """
            () => {
                function cleanText(t) {
                    return (t || "").replace(/\\s+/g, " ").trim();
                }

                const bodyText = document.body ? document.body.innerText : "";
                const lines = bodyText
                    .split("\\n")
                    .map(x => cleanText(x))
                    .filter(x => x.length > 0);

                let vehicleLine = "";
                let partLine = "";

                for (let i = 0; i < lines.length; i++) {
                    if (/^\\d{4}\\s+/.test(lines[i])) {
                        vehicleLine = lines[i];

                        if (i + 1 < lines.length) {
                            partLine = lines[i + 1];
                        }

                        break;
                    }
                }

                let searchTitle = cleanText((vehicleLine + " " + partLine).trim());

                const checked = document.querySelector('input[type="radio"]:checked');

                let selectedModel = "";

                if (checked) {
                    let text = "";

                    let node = checked.nextSibling;

                    while (node && cleanText(text).length < 500) {
                        if (node.nodeType === Node.TEXT_NODE) {
                            text += " " + node.textContent;
                        } else if (node.innerText) {
                            text += " " + node.innerText;
                        }

                        if (cleanText(text).length > 5) {
                            break;
                        }

                        node = node.nextSibling;
                    }

                    selectedModel = cleanText(text);

                    if (!selectedModel && checked.parentElement) {
                        selectedModel = cleanText(checked.parentElement.innerText);
                    }
                }

                let vehiculeMoteurAuto = "";

                if (searchTitle && selectedModel) {
                    vehiculeMoteurAuto = searchTitle + " - " + selectedModel;
                } else if (searchTitle) {
                    vehiculeMoteurAuto = searchTitle;
                } else if (selectedModel) {
                    vehiculeMoteurAuto = selectedModel;
                }

                return {
                    search_title: searchTitle,
                    selected_model: selectedModel,
                    vehicule_moteur_auto: vehiculeMoteurAuto
                };
            }
            """
        )

        search_title = clean(info.get("search_title", ""))
        selected_model = clean(info.get("selected_model", ""))
        vehicule_moteur_auto = clean(info.get("vehicule_moteur_auto", ""))

        if search_title or selected_model or vehicule_moteur_auto:
            return {
                "search_title": search_title,
                "selected_model": selected_model,
                "vehicule_moteur_auto": vehicule_moteur_auto
            }

    except:
        pass

    return {
        "search_title": "",
        "selected_model": "",
        "vehicule_moteur_auto": ""
    }


def extract_rows_from_page(page, page_num, search_info):
    rows = []
    table_rows = page.locator("table tr")

    distance_index = find_distance_column(page)

    for i in range(table_rows.count()):
        try:
            row = table_rows.nth(i)
            raw = clean(row.inner_text())
        except:
            continue

        if "$" not in raw:
            continue

        price = extract_price(raw)

        if price is None:
            continue

        cells_text = get_cells_from_row(row)

        distance = extract_distance_by_column(cells_text, distance_index)

        if distance is None:
            distance = extract_distance_automatic(cells_text, raw)

        rows.append({
            "page": page_num,
            "price": price,
            "km": extract_km(raw),
            "distance": distance,
            "grade": extract_grade(raw),
            "warranty": extract_warranty(raw),
            "excluded": is_bad(raw),
            "search_title": search_info.get("search_title", ""),
            "selected_model": search_info.get("selected_model", ""),
            "vehicule_moteur_auto": search_info.get("vehicule_moteur_auto", ""),
            "raw": raw
        })

    return rows


def main():
    all_rows = []

    last_search_info = {
        "search_title": "",
        "selected_model": "",
        "vehicule_moteur_auto": ""
    }

    with sync_playwright() as p:
        user_data_dir = "carpart_chrome_profile"

        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1400, "height": 900}
        )

        page = context.pages[0] if context.pages else context.new_page()

        page.goto(START_URL)

        print("Connecte-toi à Car-Part Pro.")
        print("Fais ta recherche moteur.")
        print("Choisis le bon modèle/interchange si Car-Part te le demande.")
        print("Le robot va sauvegarder automatiquement le choix sélectionné.")
        print("Le robot attend la page de résultats...")

        while True:
            current_url = page.url.lower()
            body_text = ""

            try:
                body_text = page.locator("body").inner_text(timeout=2000)
            except:
                pass

            captured = capture_selected_model_info(page)

            if captured.get("vehicule_moteur_auto"):
                last_search_info = captured
                print(f"Choix Car-Part capturé : {last_search_info.get('vehicule_moteur_auto')}")

            if "prosearch.cgi" in current_url and "price" in body_text.lower():
                break

            time.sleep(1)

        if not last_search_info.get("vehicule_moteur_auto"):
            captured = capture_selected_model_info(page)

            if captured.get("vehicule_moteur_auto"):
                last_search_info = captured

        print(f"Titre recherche : {last_search_info.get('search_title')}")
        print(f"Modèle sélectionné : {last_search_info.get('selected_model')}")
        print(f"Véhicule/moteur auto : {last_search_info.get('vehicule_moteur_auto')}")

        page_num = 1

        while True:
            print(f"Extraction page {page_num}...")

            page.wait_for_timeout(1500)

            rows = extract_rows_from_page(page, page_num, last_search_info)
            all_rows.extend(rows)

            distances_valides = [
                r["distance"] for r in rows
                if r.get("distance") is not None
            ]

            print(f"{len(rows)} lignes trouvées sur la page {page_num}")
            print(f"{len(distances_valides)} distances trouvées sur la page {page_num}")

            if len(distances_valides) > 0:
                print(f"Exemples distances : {distances_valides[:10]}")

            next_link = page.locator("text=Next Page").first

            if next_link.count() == 0:
                print("Aucun Next Page trouvé. Fin.")
                break

            try:
                if not next_link.is_visible():
                    print("Next Page non visible. Fin.")
                    break

                next_link.click(timeout=5000)
                page.wait_for_timeout(2500)
                page_num += 1

            except Exception as e:
                print(f"Impossible de cliquer Next Page : {e}")
                break

        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "page",
                    "price",
                    "km",
                    "distance",
                    "grade",
                    "warranty",
                    "excluded",
                    "search_title",
                    "selected_model",
                    "vehicule_moteur_auto",
                    "raw"
                ]
            )
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"CSV créé : {CSV_FILE}")
        print(f"Total lignes extraites : {len(all_rows)}")

        total_distances = [
            r["distance"] for r in all_rows
            if r.get("distance") is not None
        ]

        print(f"Total distances extraites : {len(total_distances)}")

        if len(total_distances) > 0:
            print(f"Distances extraites exemple : {total_distances[:20]}")

        context.close()


if __name__ == "__main__":
    main()