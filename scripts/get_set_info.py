import sys
import json
import os
from urllib import request, parse

# Ruta absoluta al directorio del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARD_JSON_PATH = os.path.join(BASE_DIR, "card.json")


def get_printed_size(set_code):
    url = f"https://api.scryfall.com/sets/{parse.quote(set_code)}"
    with request.urlopen(url) as r:
        data = json.loads(r.read())
    return data.get("printed_size")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("ERROR: Falta set_code (ej: usg)")
        sys.exit(1)

    set_code = sys.argv[1]   # ej: usg

    printed_size = get_printed_size(set_code)

    if printed_size is None:
        print("No se pudo obtener printed_size")
        sys.exit(1)

    # -----------------------------------
    # Abrir card.json existente (YA es dict)
    # -----------------------------------
    with open(CARD_JSON_PATH, "r", encoding="utf-8") as f:
        card_json = json.load(f)

    # -----------------------------------
    # Inyectar el dato nuevo
    # -----------------------------------
    card_json["set_total_count"] = printed_size

    # -----------------------------------
    # Guardar nuevamente card.json (JSON real)
    # -----------------------------------
    with open(CARD_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(card_json, f, ensure_ascii=False, indent=2)

    print(f"OK - printed_size = {printed_size}")

