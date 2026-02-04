import time
import sys
import json
import os
import re
import unicodedata
from urllib import request, parse, error

# -----------------------------------
# LOG
# -----------------------------------

LOG_FILE = os.path.join(os.path.dirname(__file__), "debug_log.txt")

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except:
        pass


# -----------------------------------
# Utils
# -----------------------------------

def normalize_text(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s)
    return s


def add_meld_info(card_json):
    if card_json.get("layout") == "meld":
        for i in range(0, 3):
            time.sleep(0.1)
            uri = card_json["all_parts"][i]["uri"]
            part = json.loads(request.urlopen(uri).read())
            card_json["all_parts"][i]["info"] = part
    return card_json


def load_js_database(template, set_code):
    """
    Carga data/<template>/<set>.js
    Soporta JS tipo:
    var XXX = [ {...}, {...} ];
    Limpia comas finales inválidas.
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(BASE_DIR, "data", template, f"{set_code}.js")

    log(f"📂 Buscando base JS: {path}")

    if not os.path.exists(path):
        log("⚠ No existe base JS.")
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    try:
        # ----------------------------
        # Extraer solo el array [...]
        # ----------------------------
        start = raw.find("[")
        end   = raw.rfind("]")

        if start == -1 or end == -1:
            log("❌ No se encontró array en el JS.")
            return []

        content = raw[start:end+1]

        # ----------------------------
        # Limpiar comas finales inválidas
        # ----------------------------
        # },]  -> }]
        content = re.sub(r",\s*([\]}])", r"\1", content)

        # ----------------------------
        # Parsear JSON
        # ----------------------------
        data = json.loads(content)
        log(f"✔ Base JS cargada: {len(data)} registros")
        return data

    except Exception as e:
        log("❌ Error parseando JS:")
        log(e)
        return []


def find_card_override(db, card_name):
    target = normalize_text(card_name)
    log(f"🔍 Buscando override para: '{target}'")

    for row in db:
        row_name = normalize_text(row.get("Name", ""))
        if row_name == target:
            log(f"✅ Match encontrado: '{row.get('Name')}'")
            return row

    log("❌ No se encontró override")
    return None


def apply_override(card_json, override, lang):

    if not override:
        return

    is_es = (lang == "es")
    log(f"🎯 Aplicando override (lang={lang})")

    # ---------------- TEXTOS ----------------

    if is_es:
        if override.get("Original_Text_es") is not None:
            card_json["oracle_text"] = override["Original_Text_es"]

        if override.get("Flavor_Text_es") is not None:
            card_json["flavor_text"] = override["Flavor_Text_es"]

        if override.get("Type_Line_es") is not None:
            card_json["type_line"] = override["Type_Line_es"]

        # 👉 FORZAR nombre en español
        if override.get("Name_es"):
            log(f"✎ Reemplazando name → {override['Name_es']}")
            card_json["name"] = override["Name_es"]

    else:
        if override.get("Original_Text") is not None:
            card_json["oracle_text"] = override["Original_Text"]

        if override.get("Flavor_Text") is not None:
            card_json["flavor_text"] = override["Flavor_Text"]

        if override.get("Type_Line") is not None:
            card_json["type_line"] = override["Type_Line"]

    # ---------------- ESTILOS (SIEMPRE CREAR) ----------------

    def safe(v):
        if v is None:
            return ""
        return v

    text_style = {
        "justification": safe(override.get("Justification")),
        "size": safe(override.get("Size")),
        "tracking": safe(override.get("Tracking")),
        "leading": safe(override.get("Leading")),
        "offsetx": safe(override.get("OffsetX")),
        "offsety": safe(override.get("OffsetY")),
        "boxwidthadjust": safe(override.get("BoxWidthAdjust")),
        "text_flavor_lead": safe(override.get("TextFlavor_Lead")),
    }

    card_json["text_style"] = text_style
    log(f"✎ text_style aplicado: {text_style}")


# -----------------------------------
# Main
# -----------------------------------

if __name__ == "__main__":
    time.sleep(0.1)

    # Limpiar log al inicio
    try:
        open(LOG_FILE, "w").close()
    except:
        pass

    if len(sys.argv) < 2:
        log("❌ Falta argumento.")
        sys.exit(1)

    raw_arg = sys.argv[1]
    parts = raw_arg.split("$")

    # -----------------------------------
    # Parse argumentos
    # -----------------------------------

    card_name      = parts[0].strip()
    card_set       = parts[1].strip().lower() if len(parts) >= 2 else None
    lang           = parts[2].strip().lower() if len(parts) >= 3 else "en"
    template       = parts[3].strip() if len(parts) >= 4 else None
    card_collector = parts[4].strip() if len(parts) >= 5 and parts[4] else None

    log("▶ Params:")
    log(f"  Name      : {card_name}")
    log(f"  Set       : {card_set}")
    log(f"  Language  : {lang}")
    log(f"  Template  : {template}")
    log(f"  Collector : {card_collector}")

    # -----------------------------------
    # Descargar desde Scryfall
    # -----------------------------------

    try:
        if card_set and card_collector:
            url = f"https://api.scryfall.com/cards/{parse.quote(card_set)}/{parse.quote(card_collector)}"
        elif card_set:
            url = (
                "https://api.scryfall.com/cards/named?"
                f"fuzzy={parse.quote(card_name)}&set={parse.quote(card_set)}"
            )
        else:
            url = f"https://api.scryfall.com/cards/named?fuzzy={parse.quote(card_name)}"

        log(f"🌐 URL Scryfall: {url}")
        card = request.urlopen(url).read()

    except error.HTTPError as e:
        log("❌ Error consultando Scryfall:")
        log(e)
        sys.exit(1)

    card_json = add_meld_info(json.loads(card))
    base_name = card_json.get("name", "")

    log(f"📝 Nombre base Scryfall: {base_name}")

    # -----------------------------------
    # Override desde JS
    # -----------------------------------

    if not template:
        log("❌ No se recibió template.")
        sys.exit(1)

    set_code = card_json.get("set", "").lower()
    log(f"📦 Set detectado: {set_code}")

    db = load_js_database(template, set_code)
    override = find_card_override(db, base_name)

    if override:
        log("✔ Override encontrado")
        apply_override(card_json, override, lang)
    else:
        log("• Usando datos originales de Scryfall")

        # 👉 Aunque no haya override, crear text_style vacío
        card_json["text_style"] = {
            "justification": "",
            "size": "",
            "tracking": "",
            "leading": "",
            "offsetx": "",
            "offsety": "",
            "boxwidthadjust": "",
            "text_flavor_lead": "",
        }

    # -----------------------------------
    # Guardar card.json
    # -----------------------------------

    output_path = os.path.join(sys.path[0], "card.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(card_json, f, ensure_ascii=False, indent=2)

    log(f"✔ card.json generado: {output_path}")
