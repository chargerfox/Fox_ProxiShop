import re
import ast
import requests
import urllib.parse
import time
import json
import os
import unicodedata

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
INPUT_FILE = "data/LEA.js"
OUTPUT_FILE = "data/LEA_es.js"
LOG_FILE = "Current_translate_log.txt"
DELAY = 2.5
BLOCK_SIZE = 10  # cada cuántas cartas guardar

TRANSLATE_FLAGS = {
    "Name_es": True,
    "Type_Line_es": True,
    "Original_Text_es": True,
    "Flavor_Text_es": True
}

# -----------------------------
# Sets legacy que requieren corrección de typeline
# -----------------------------
LEGACY_TYPELINE_SETS = {
    "lea","leb","2ed","ced","cei","arn","atq","fbb","3ed","leg","sum","drk","fem",
    "pmei","4bb","4ed","ice","bchr","chr","ren","rin","hml","o90p","ptc","all",
    "mir","itp","vis","5ed","por","olep","wth","wc97","tmp","ptmp","sth","exo","p02",
    "tugl","ugl","wc98","usg","ath","ulg"
}

# Detectar set actual desde el nombre del archivo (LEA.js → lea)
RAW_NAME = os.path.splitext(os.path.basename(INPUT_FILE))[0].lower()
CURRENT_SET = RAW_NAME.split("_")[0]
IS_LEGACY_SET = CURRENT_SET in LEGACY_TYPELINE_SETS

print("Set detectado:", CURRENT_SET, "| Legacy:", IS_LEGACY_SET)

# -----------------------------
# Diccionario de caracteres especiales a preservar
# -----------------------------
SPECIAL_CHARS = {
    "“": "__OPEN_DOUBLE_QUOTE__",
    "”": "__CLOSE_DOUBLE_QUOTE__",
    "‘": "__OPEN_SINGLE_QUOTE__",
    "’": "__CLOSE_SINGLE_QUOTE__",
    "—": "__EM_DASH__"
}

# -----------------------------
# Diccionario de términos MTG oficiales (inglés → español)
# -----------------------------
MTG_TERMS = {
    "tap": "gira",
    "tapped": "giradas",
    "untap": "endereza",
    "untapped": "enderezadas",

    "wall": "muro",
    "walls": "muros",
    "land": "tierra",
    "lands": "tierras",
    "summon": "invocar",
    "summoned": "invocado",
    "discard": "descarta",
    "enchant": "encantar",
    
    "instant": "instantaneo",
    "interrupt": "interrupcion",
    "sorcery": "conjuro",
    
    "power": "ataque",
    "toughness": "resistencia",
    
    "target creature": "la criatura objetivo",
    "target land": "la tierra objetivo",
    "target opponent": "el oponente objetivo",
    "target player": "el jugador objetivo",
    "target enchantment": "el encantamiento objetivo",
    "target artifact": "el artefacto objetivo",
    "target planeswalker": "el planeswalker objetivo",
    "target spell": "el hechizo objetivo",
    "target ability": "la habilidad objetivo",
    "any target": "cualquier objetivo",

    "swampwalk": "Cruzapantanos",
    "mountainwalk": "Cruzamontañas",
    "islandwalk": "Cruzaislas",
    "plainswalk": "Cruzallanuras",
    "forestwalk": "Cruzabosques",
    
    "flying": "vuela",
    "bands": "agrupa",
    "band": "agrupa",
    "haunt": "acechar",
    "scry": "adivinar",
    "affinity for artifacts": "afinidad por artefactos",
    "reach": "alcance",
    "champion": "amparar",
    "amplify": "amplificar",
    "hexproof": "antimaleficio",
    "living weapon": "arma viviente",
    "totem armor": "armadura tótem",
    "trample": "arrollar",
    "bushido": "bushido",
    "channel": "canalizar",
    "changeling": "cambiaformas",
    "phasing": "cambia de fase",
    "cycling": "ciclo",
    "convoke": "convocar",
    "first strike": "dañar primero",
    "double strike": "dañar dos veces",
    "defender": "defensor",
    "madness": "demencia",
    "vanishing": "desmaterializarse",
    "shadow": "desvanecerse",
    "flash": "destello",
    "wither": "debilitar",
    "dredge": "dragar",
    "echo": "eco",
    "splice onto arcane": "empalmar con lo arcano",
    "clash": "enfrentar",
    "entwine": "entrelazar",
    "epic": "epico",
    "equip": "equipar",
    "sunburst": "estallido solar",
    "imprint": "estampa",
    "kicker": "estímulo",
    "evoke": "evocar",
    "split second": "fracción de segundo",
    "flanking": "flanquear",
    "battle cry": "grito de batalla",
    "kinship": "hermandad",
    "fateful hour": "hora fatídica",
    "horsemanship": "horsemanship",
    "unblockable": "imbloqueable",
    "rampage": "ímpetu",
    "infect": "infectar",
    "indestructible": "indestructible",
    "graft": "injertar",
    "fear": "inspirar temor",
    "intimidate": "intimidar",
    "radiance": "irradiar",
    "cumulative upkeep": "mantenimiento acumulativo",
    "metalcraft": "metalurgia",
    "morph": "metamorfosis",
    "soulshift": "migración de almas",
    "miracle": "milagro",
    "modular": "modular",
    "morbid": "necrario",
    "ninjutsu": "ninjutsu",
    "ripple": "ondear",
    "haste": "prisa",
    "fateseal": "predestinar",
    "forecast": "presagiar",
    "proliferate": "proliferar",
    "provoke": "provocar",
    "rebound": "rebote",
    "recover": "recobrar",
    "sweep": "recolectar",
    "buyback": "recuperar",
    "reinforce": "reforzar",
    "regenerate": "regenera",
    "replicate": "reproducir",
    "resilience": "resiliencia",
    "flashback": "retrospectiva",
    "prowl": "rondar",
    "bloodthirst": "sed de sangre",
    "level up": "subir de nivel",
    "deathtouch": "toque mortal",
    "storm": "tormenta",
    "hellbent": "temerario",
    "transform": "transformar",
    "transmute": "transmutar",
    "threshold": "umbral",
    "soulbond": "unir almas",
    "shroud": "velo",
    "vigilance": "vigilancia",
    "lifelink": "vínculo vital"
}

# -----------------------------
# Funciones auxiliares
# -----------------------------
def preserve_special_chars(text):
    for char, marker in SPECIAL_CHARS.items():
        text = text.replace(char, marker)
    return text

def restore_special_chars(text):
    for char, marker in SPECIAL_CHARS.items():
        text = text.replace(marker, char)
    return text

def apply_mtg_terms_before_translate(text):
    terms_sorted = sorted(MTG_TERMS.items(), key=lambda x: len(x[0]), reverse=True)

    for term, replacement in terms_sorted:
        pattern = re.compile(r'(?<!\w)' + re.escape(term) + r'(?!\w)', flags=re.IGNORECASE)

        def repl(match):
            word = match.group()
            if word[0].isupper():
                return replacement.capitalize()
            else:
                return replacement.lower()

        text = pattern.sub(repl, text)

    return text

def translate_text(text):
    if not text:
        return ""
    encoded_text = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q={encoded_text}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data[0][0][0]
    except Exception as e:
        print(f"Error traduciendo: {text}\n{e}")
        return text

def translate_text_segments(text):
    if not text:
        return ""

    segments = re.split(r'([,;.\n—])', text)
    translated_segments = []

    for seg in segments:
        seg_clean = seg.strip()
        if seg_clean and seg not in [',', ';', '.', '\n', '—']:
            seg_hibrido = apply_mtg_terms_before_translate(seg_clean)
            translated_seg = translate_text(seg_hibrido)
            translated_segments.append(translated_seg)
        else:
            translated_segments.append(seg)

    return ''.join(translated_segments)

def clean_translation(text):
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\s+([,.;])', r'\1', text)
    text = re.sub(r'([,;])([^\s])', r'\1 \2', text)
    return text.strip()

def convert_for_js(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    s = s.replace("None", "null").replace("True", "true").replace("False", "false")
    return s

# -----------------------------
# Forzar Title Case en "Encantar X"
# -----------------------------
def fix_enchant_typeline_caps(text):
    if not text:
        return text

    # Solo aplicar si empieza con "Encantar "
    if text.lower().startswith("encantar "):
        words = text.split(" ")
        words = [w.capitalize() for w in words]
        return " ".join(words)

    return text

# -----------------------------
# Title Case inteligente para nombres de cartas
# -----------------------------
def smart_title_case_name(text):
    if not text:
        return text

    lowercase_words = {
        "de", "del", "la", "las", "los", "y", "o", "a", "en", "por", "para", "con"
    }

    words = text.split(" ")
    fixed = []

    for i, w in enumerate(words):
        wl = w.lower()

        # Primera palabra siempre mayúscula
        if i == 0:
            fixed.append(w.capitalize())
            continue

        # Conectores en minúscula
        if wl in lowercase_words:
            fixed.append(wl)
        else:
            fixed.append(w.capitalize())

    return " ".join(fixed)

# -----------------------------
# NORMALIZACIÓN SOLO PARA Name_es (fuente sin acentos ni ñ)
# -----------------------------
def normalize_name_for_font(text):
    if not text:
        return text

    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))
    text = text.replace("ñ", "n").replace("Ñ", "N")

    return text

# -----------------------------
# Normalización legacy typeline
# -----------------------------
def normalize_legacy_typeline(type_line_en):
    if not type_line_en:
        return type_line_en, None, None

    text = type_line_en.strip()

    # -----------------------------
    # LAND legacy:
    # Land — X
    # Basic Land — X
    # → Land
    # -----------------------------
    if re.match(r'^(Basic\s+)?Land\s+—', text, re.IGNORECASE):
        return "Land", "land", None

    # Enchantment — Aura  → se completa luego usando Oracle_Text
    if re.match(r'^Enchantment\s+—\s+Aura$', text, re.IGNORECASE):
        return "Enchant", "enchant", None

    # Creature — Dragon → Summon Dragon
    m = re.match(r'^Creature\s+—\s+(.+)$', text, re.IGNORECASE)
    if m:
        subtype = m.group(1).strip()
        return f"Summon {subtype}", "summon", subtype

    return text, None, None


# -----------------------------
# NUEVO: extraer "Enchant X" desde Oracle_Text
# -----------------------------
def extract_enchant_from_oracle(oracle_text):
    """
    Toma las primeras dos palabras del Oracle_Text y las
    normaliza a: 'Enchant Land', 'Enchant Creature', etc.
    """
    if not oracle_text:
        return None

    # Cortar en espacios y saltos
    words = re.split(r'\s+', oracle_text.strip())
    if len(words) < 2:
        return None

    w1 = words[0].capitalize()
    w2 = words[1].capitalize()

    return f"{w1} {w2}"

# -----------------------------
# Leer archivo .js y extraer array
# -----------------------------
source_file = INPUT_FILE

# Si existe log y existe output, reanudar desde el archivo traducido
if os.path.exists(LOG_FILE) and os.path.exists(OUTPUT_FILE):
    print("Reanudando desde archivo traducido:", OUTPUT_FILE)
    source_file = OUTPUT_FILE
else:
    print("Usando archivo original:", INPUT_FILE)

with open(source_file, "r", encoding="utf-8") as f:
    js_text = f.read()


match = re.search(r'var\s+LEA\s*=\s*(\[.*\]);', js_text, re.DOTALL)
if not match:
    raise ValueError("No se pudo encontrar el array LEA en el JS")

json_text = match.group(1)
json_text = json_text.replace("null", "None").replace("true", "True").replace("false", "False")
cards = ast.literal_eval(json_text)

# -----------------------------
# Revisar si hay log para reanudar
# -----------------------------
start_idx = 1
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as logf:
        try:
            start_idx = int(logf.read().strip())
            print(f"Reanudando desde la carta {start_idx}")
        except:
            start_idx = 1

# -----------------------------
# Traducir cartas
# -----------------------------
for idx in range(start_idx - 1, len(cards)):
    card = cards[idx]
    print(f"Traduciendo carta {idx+1}/{len(cards)}: {card.get('Name')}")

    legacy_mode = None
    legacy_subtype = None

    # -----------------------------
    # Normalizar Type_Line legacy
    # -----------------------------
    if IS_LEGACY_SET and "Type_Line" in card:
        normalized_en, legacy_mode, legacy_subtype = normalize_legacy_typeline(card["Type_Line"])

        # 🔥 NUEVO: completar Enchant X usando Oracle_Text
        if legacy_mode == "enchant":
            oracle_text = card.get("Oracle_Text", "")
            enchant_from_oracle = extract_enchant_from_oracle(oracle_text)

            if enchant_from_oracle:
                card["Type_Line"] = enchant_from_oracle
            else:
                card["Type_Line"] = normalized_en

        else:
            card["Type_Line"] = normalized_en

    # -----------------------------
    # Traducción de campos
    # -----------------------------
    for field_es, flag in TRANSLATE_FLAGS.items():
        if not flag:
            continue

        field_orig = field_es.replace("_es", "")
        original_text = card.get(field_orig, "")
        text_to_translate = preserve_special_chars(original_text)

        # -----------------------------
        # Traducción especial typeline legacy (Summon)
        # -----------------------------
        if field_es == "Type_Line_es" and IS_LEGACY_SET and legacy_mode == "summon" and legacy_subtype:

            subtype_preserved = preserve_special_chars(legacy_subtype)
            subtype_hibrido = apply_mtg_terms_before_translate(subtype_preserved)
            subtype_translated = translate_text(subtype_hibrido)
            subtype_translated = restore_special_chars(subtype_translated)
            subtype_translated = clean_translation(subtype_translated)
            translated_text = f"Invocar {subtype_translated}"

        # -----------------------------
        # Traducción normal
        # -----------------------------
        else:
            if field_es in ["Flavor_Text_es", "Original_Text_es"]:
                translated_text = translate_text_segments(text_to_translate)
            else:
                text_hibrido = apply_mtg_terms_before_translate(text_to_translate)
                translated_text = translate_text(text_hibrido)

        translated_text = restore_special_chars(translated_text)
        translated_text = clean_translation(translated_text)

        # -----------------------------
        # FIX: Capitalización Enchant X en Type_Line_es
        # -----------------------------
        if field_es == "Type_Line_es":

            # LAND legacy → Tierra
            if IS_LEGACY_SET and legacy_mode == "land":
                translated_text = "Tierra"

            else:
                # Encantar X → Encantar X (Title Case)
                translated_text = fix_enchant_typeline_caps(translated_text)


        # -----------------------------
        # NORMALIZAR SOLO Name_es
        # -----------------------------
        if field_es == "Name_es":
            translated_text = smart_title_case_name(translated_text)
            translated_text = normalize_name_for_font(translated_text)

        card[field_es] = translated_text

    # -----------------------------
    # Guardado incremental
    # -----------------------------
    if (idx + 1) % BLOCK_SIZE == 0 or (idx + 1) == len(cards):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("var LEA = ")
            f.write(convert_for_js(cards))
            f.write(";")

        next_idx = idx + 2
        with open(LOG_FILE, "w", encoding="utf-8") as logf:
            logf.write(str(next_idx))

        print(f"Guardado automático: {idx+1} cartas traducidas, log actualizado a {next_idx}")

    time.sleep(DELAY)

# -----------------------------
# Al finalizar borrar log
# -----------------------------
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    print("Traducción completada. Log borrado.")

print(f"\n¡Traducción completada! Archivo guardado como {OUTPUT_FILE}")
