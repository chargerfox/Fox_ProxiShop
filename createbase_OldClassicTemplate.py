import json
import sys
import ijson
import os
import re

# ---- CONFIG ----
bulk_file = "scryfall-bulk.json"   # bulk Scryfall
Template_Set = "RegularTemplate"

if len(sys.argv) < 2:
    print("Uso: python generate_js.py <SETCODE>")
    sys.exit(1)

set_code = sys.argv[1].lower()     # ej: lea

# Crear carpeta data si no existe
os.makedirs("data", exist_ok=True)

# Rutas
mtgjson_file = os.path.join("MTGJSON", f"{set_code}_pretty.json")
output_js_file = os.path.join("data", f"{set_code.upper()}.js")
nomatch_log_file = os.path.join("data", f"{set_code}_nomatch.txt")

array_name = set_code.upper()

# ---------------- CONTADORES ----------------
bulk_cards_found = 0
cards_written = 0
copied_from_mtgjson = 0
not_found_in_mtgjson = 0

nomatch_cards = []

# -------------------------------------------------------
# CARGAR MTGJSON EN MEMORIA (lookup por collector STRING)
# -------------------------------------------------------

print("📥 Cargando MTGJSON...")

with open(mtgjson_file, "r", encoding="utf-8") as f:
    mtgjson_data = json.load(f)

mtg_cards = mtgjson_data.get("data", {}).get("cards", [])

mtg_lookup = {}

for c in mtg_cards:
    collector = str(c.get("number", "")).strip().lower()

    # Acepta: 123, 123a–123h
    if not re.fullmatch(r"\d+[a-h]?", collector):
        continue

    mtg_lookup[collector] = c

print(f"✔ MTGJSON cartas indexadas: {len(mtg_lookup)}")

# -------------------------------------------------------
# GENERAR JS DESDE SCRYFALL + MTGJSON
# -------------------------------------------------------

print("📦 Procesando BULK Scryfall...")

with open(output_js_file, "w", encoding="utf-8") as out:
    out.write(f"var {array_name} = [\n")

    with open(bulk_file, "rb") as f:
        parser = ijson.items(f, "item")

        for card in parser:

            if card.get("set", "").lower() != set_code:
                continue

            bulk_cards_found += 1

            collector = str(card.get("collector_number", "")).strip().lower()

            # Acepta: 123, 123a–123h
            if not re.fullmatch(r"\d+[a-h]?", collector):
                continue

            # 🔎 Buscar carta en MTGJSON (MATCH EXACTO)
            mtg_card = mtg_lookup.get(collector)

            if mtg_card:
                copied_from_mtgjson += 1
            else:
                not_found_in_mtgjson += 1
                nomatch_cards.append({
                    "Collector": collector,
                    "Name": card.get("name", ""),
                    "Type": card.get("type_line", ""),
                    "Oracle_Text": (card.get("oracle_text") or "").replace("\r\n", " ")
                })

            # ------------------- Campos Spanish -------------------
            foreign = mtg_card.get("foreignData", []) if mtg_card else []
            spanish_entry = None

            for fdata in foreign:
                if fdata.get("language", "").lower() == "spanish":
                    spanish_entry = fdata
                    break

            name_es = spanish_entry.get("name") if spanish_entry and spanish_entry.get("name") else card.get("name", "")
            type_es = spanish_entry.get("type") if spanish_entry and spanish_entry.get("type") else card.get("type_line", "")

            original_text_es = (
                spanish_entry.get("text")
                if spanish_entry and spanish_entry.get("text")
                else (mtg_card.get("originalText") if mtg_card else card.get("oracle_text") or "")
            )

            flavor_text_es = (
                spanish_entry.get("flavorText")
                if spanish_entry and spanish_entry.get("flavorText")
                else (card.get("flavor_text") or "").replace("\r\n", "\n")
            )

            original_text = mtg_card.get("originalText") if mtg_card and mtg_card.get("originalText") else ""
            if original_text:
                original_text = original_text.replace("\r\n", "\n")

            # ------------------- NUEVOS CAMPOS -------------------
            types = mtg_card.get("types", []) if mtg_card else []
            subtypes = mtg_card.get("subtypes", []) if mtg_card else []
            borderColor = mtg_card.get("borderColor", "") if mtg_card else ""

            obj = {
                "Name": card.get("name", ""),
                "Name_es": name_es,
                "Type_Line": card.get("type_line", ""),
                "Type_Line_es": type_es,
                "Collector": collector,

                "Original_Text": original_text,
                "Original_Text_es": original_text_es,
                "Oracle_Text": (card.get("oracle_text") or "").replace("\r\n", "\n"),

                "Flavor_Text": (card.get("flavor_text") or "").replace("\r\n", "\n"),
                "Flavor_Text_es": flavor_text_es,

                "Justification": None,
                "Size": None,
                "Tracking": None,
                "Leading": None,
                "TextFlavor_Lead": None,
                "OffsetX": None,
                "OffsetY": None,
                "BoxWidthAdjust": None,

                "Template_Set": Template_Set,

                # Datos de juego
                "Mana_Cost": card.get("mana_cost", ""),
                "Power": card.get("power", ""),
                "Toughness": card.get("toughness", ""),
                "Artist": card.get("artist", ""),

                # extras
                "image_uris": card.get("image_uris", {}),
                "colors": card.get("colors", []),
                "color_identity": card.get("color_identity", []),
                "set": card.get("set", ""),
                "set_name": card.get("set_name", ""),
                "rarity": card.get("rarity", ""),

                # NUEVOS CAMPOS MTGJSON
                "types": types,
                "subtypes": subtypes,
                "borderColor": borderColor
            }

            out.write(json.dumps(obj, ensure_ascii=False, indent=2) + ",\n")
            cards_written += 1

    out.write("];\n")

# -------------------------------------------------------
# LOG NOMATCH
# -------------------------------------------------------

if nomatch_cards:
    print(f"📝 Generando log de NOMATCH: {nomatch_log_file}")

    with open(nomatch_log_file, "w", encoding="utf-8") as log:
        for c in nomatch_cards:
            log.write(
                f"Collector: {c['Collector']}\n"
                f"Name: {c['Name']}\n"
                f"Type: {c['Type']}\n"
                f"Oracle: {c['Oracle_Text']}\n"
                f"{'-'*50}\n"
            )

# -------------------------------------------------------
# REPORTE FINAL
# -------------------------------------------------------

print("--------------------------------------------------")
print(f"📦 Cartas encontradas en BULK ({set_code.upper()}): {bulk_cards_found}")
print(f"📘 Cartas indexadas en MTGJSON: {len(mtg_lookup)}")
print(f"✔ Cartas con Original_Text copiadas: {copied_from_mtgjson}")
print(f"⚠ Cartas sin match en MTGJSON: {not_found_in_mtgjson}")
print(f"📝 Cartas escritas en {output_js_file}: {cards_written}")
print("--------------------------------------------------")

if not_found_in_mtgjson > 0:
    print(f"👉 Revisar archivo: {nomatch_log_file}")
