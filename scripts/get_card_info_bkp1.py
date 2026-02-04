import time
import sys
import json
import csv
import os
from urllib import request, parse, error


# -----------------------------------
# Utils
# -----------------------------------

def add_meld_info(card_json):
    if card_json.get("layout") == "meld":
        for i in range(0, 3):
            time.sleep(0.1)
            uri = card_json["all_parts"][i]["uri"]
            part = json.loads(request.urlopen(uri).read())
            card_json["all_parts"][i]["info"] = part
    return card_json


def load_text_database(set_code):
    """
    Carga data/<set>.csv desde la raíz del proyecto.
    Devuelve lista de dicts.
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(BASE_DIR, "data", f"{set_code}.csv")

    if not os.path.exists(path):
        print(f"⚠ No existe base de texto: {path}")
        return []

    db = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.append(row)

    print(f"✔ Base de texto cargada: {len(db)} registros")
    return db



def find_text_override(db, name, collector):
    """
    Busca coincidencia:
    1) Name + Collector
    2) Name solamente (fallback)
    """
    name = name.strip().lower()
    collector = (collector or "").strip()

    exact_match = None
    name_match = None

    for row in db:
        row_name = row.get("Name", "").strip().lower()
        row_collector = row.get("Collector", "").strip()

        if row_name == name and row_collector == collector and collector:
            exact_match = row
            break

        if row_name == name and not row_collector:
            name_match = row

    return exact_match or name_match


# -----------------------------------
# Main
# -----------------------------------

if __name__ == "__main__":
    time.sleep(0.1)

    # -----------------------------------
    # Validar argumentos
    # -----------------------------------
    if len(sys.argv) < 2:
        print("❌ Falta argumento.")
        print("Uso:")
        print('  python get_card_info.py "Card Name$set$collector"')
        print('  Ejemplo: python get_card_info.py "Lightning Dragon$usg$202"')
        sys.exit(1)

    raw_arg = sys.argv[1]

    # -----------------------------------
    # Parse: name$set$collector (collector opcional)
    # -----------------------------------

    parts = raw_arg.split("$")

    card_name = parts[0].strip()
    card_set = parts[1].strip().lower() if len(parts) >= 2 else None
    card_collector = parts[2].strip() if len(parts) >= 3 else None

    card = None

    try:
        # -----------------------------------
        # Caso 1: hay collector → API directa
        # -----------------------------------
        if card_set and card_collector:
            print(
                f"Searching Scryfall for: {card_name}, set: {card_set}, collector: {card_collector}...",
                end="",
                flush=True
            )

            url = f"https://api.scryfall.com/cards/{parse.quote(card_set)}/{parse.quote(card_collector)}"
            card = request.urlopen(url).read()

        # -----------------------------------
        # Caso 2: sin collector → fuzzy + set
        # -----------------------------------
        elif card_set:
            print(
                f"Searching Scryfall for: {card_name}, set: {card_set}...",
                end="",
                flush=True
            )

            url = (
                "https://api.scryfall.com/cards/named?"
                f"fuzzy={parse.quote(card_name)}&set={parse.quote(card_set)}"
            )
            card = request.urlopen(url).read()

        # -----------------------------------
        # Caso 3: solo nombre → fuzzy global
        # -----------------------------------
        else:
            print(
                f"Searching Scryfall for: {card_name}...",
                end="",
                flush=True
            )

            url = f"https://api.scryfall.com/cards/named?fuzzy={parse.quote(card_name)}"
            card = request.urlopen(url).read()

    except error.HTTPError as e:
        print("\n❌ Error consultando Scryfall:", e)
        input("Press enter to exit.")
        sys.exit(1)

    print(" done! Processing JSON...", flush=True)

    card_json = add_meld_info(json.loads(card))

    # -----------------------------------
    # Buscar override de texto
    # -----------------------------------

    set_code = card_json.get("set", "").lower()
    collector = card_json.get("collector_number", "")
    name = card_json.get("name", "")

    text_db = load_text_database(set_code)
    override = find_text_override(text_db, name, collector)

    if override:
        print(f"✎ Texto personalizado encontrado para: {name} [{collector}]")

        if override.get("Oracle_Text"):
            card_json["oracle_text"] = override["Oracle_Text"]

        if override.get("Flavor_Text"):
            card_json["flavor_text"] = override["Flavor_Text"]

        # 🔹 NUEVO: inyectar type_line
        if override.get("Type_Line"):
            card_json["type_line"] = override["Type_Line"]

        # 🔹 NUEVO: inyectar estilos de texto
        text_style = {}

        # Justification (string)
        if override.get("Justification"):
            text_style["justification"] = override["Justification"].strip().upper()

        # Size (float)
        if override.get("Size"):
            try:
                text_style["size"] = float(override["Size"])
            except:
                print("⚠ Size inválido en CSV:", override.get("Size"))

        # Tracking (int)
        if override.get("Tracking"):
            try:
                text_style["tracking"] = int(float(override["Tracking"]))
            except:
                print("⚠ Tracking inválido en CSV:", override.get("Tracking"))

        # Leading / Interlineado (float)
        if override.get("Leading"):
            try:
                text_style["leading"] = float(override["Leading"])
            except:
                print("⚠ Leading inválido en CSV:", override.get("Leading"))

        # Offset X (float)
        if override.get("OffsetX"):
            try:
                text_style["offsetx"] = float(override["OffsetX"])
            except:
                print("⚠ OffsetX inválido en CSV:", override.get("OffsetX"))

        # Offset Y (float)
        if override.get("OffsetY"):
            try:
                text_style["offsety"] = float(override["OffsetY"])
            except:
                print("⚠ OffsetY inválido en CSV:", override.get("OffsetY"))

        # Box Width Adjust (float)
        if override.get("BoxWidthAdjust"):
            try:
                text_style["boxwidthadjust"] = float(override["BoxWidthAdjust"])
            except:
                print("⚠ BoxWidthAdjust inválido en CSV:", override.get("BoxWidthAdjust"))

        # Text Flavor Lead (float)  ✅ opcional, por si querés usarlo también desde CSV
        if override.get("TextFlavor_Lead"):
            try:
                text_style["text_flavor_lead"] = float(override["TextFlavor_Lead"])
            except:
                print("⚠ TextFlavor_Lead inválido en CSV:", override.get("TextFlavor_Lead"))

        if text_style:
            card_json["text_style"] = text_style

    else:
        print("• Usando texto original de Scryfall")


    # -----------------------------------
    # Guardar card.json (JSON válido para Photoshop)
    # -----------------------------------

    output_path = os.path.join(sys.path[0], "card.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(card_json, f, ensure_ascii=False, indent=2)

    print(f"✔ card.json generado correctamente en: {output_path}\n", flush=True)
