import json
import os
import re
import sys
import urllib.request

# -----------------------------------
# Config
# -----------------------------------

BULK_JSON = "scryfall-bulk.json"
OUTPUT_ROOT = "art"

INVALID_CHARS = r'[\\/:*?"<>|]'

# -----------------------------------
# Utils
# -----------------------------------

def safe_filename(name):
    """
    Solo reemplaza caracteres inválidos para Windows.
    NO normaliza acentos ni unicode.
    """
    return re.sub(INVALID_CHARS, "_", name).strip()


def is_integer_collector(value):
    """
    True solo si collector_number es entero puro.
    """
    if not value:
        return False
    return value.isdigit()


def download_image(url, out_path):
    try:
        urllib.request.urlretrieve(url, out_path)
        return True
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
        return False


# -----------------------------------
# Main
# -----------------------------------

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Uso: python crops.py <set_code>")
        sys.exit(1)

    TARGET_SET = sys.argv[1].lower()

    print(f"📦 Set objetivo: {TARGET_SET}")

    if not os.path.exists(BULK_JSON):
        print(f"❌ No existe {BULK_JSON}")
        sys.exit(1)

    # Output dir
    out_dir = os.path.join(OUTPUT_ROOT, TARGET_SET.upper())
    os.makedirs(out_dir, exist_ok=True)

    # Load bulk
    print("📖 Cargando bulk...")
    with open(BULK_JSON, "r", encoding="utf-8") as f:
        bulk = json.load(f)

    total = 0
    downloaded = 0
    skipped = 0
    ignored = 0
    duplicated = 0

    seen_nonlands = set()

    print("🔍 Procesando cartas...\n")

    for card in bulk:

        total += 1

        # --- filtro por set ---
        if card.get("set", "").lower() != TARGET_SET:
            continue

        name = card.get("name", "").strip()
        collector = card.get("collector_number", "").strip()

        # --- collector debe ser entero puro ---
        if not is_integer_collector(collector):
            ignored += 1
            continue

        # --- imagen ---
        image_uris = card.get("image_uris")
        if not image_uris or "art_crop" not in image_uris:
            ignored += 1
            continue

        url = image_uris["art_crop"]

        # --- detectar basic land ---
        type_line = card.get("type_line", "").lower()
        is_basic_land = "basic land" in type_line

        safe_name = safe_filename(name)

        # -----------------------------------
        # Nombre de archivo
        # -----------------------------------

        if is_basic_land:
            # Siempre incluir collector
            filename = f"{safe_name} {collector}.jpg"

        else:
            # Una sola imagen por nombre
            key = safe_name.lower()
            if key in seen_nonlands:
                duplicated += 1
                continue

            seen_nonlands.add(key)
            filename = f"{safe_name}.jpg"

        out_path = os.path.join(out_dir, filename)

        # --- ya existe ---
        if os.path.exists(out_path):
            skipped += 1
            continue

        # --- descargar ---
        ok = download_image(url, out_path)
        if ok:
            downloaded += 1
            print(f"⬇ {filename}")
        else:
            skipped += 1

    print("\n----------------------------------")
    print("✅ Descarga finalizada")
    print(f"Total bulk leídos: {total}")
    print(f"Descargadas:       {downloaded}")
    print(f"Saltadas:          {skipped}")
    print(f"Ignoradas:         {ignored}")
    print(f"Duplicadas:        {duplicated}")
    print(f"Carpeta:           {out_dir}")
    print("----------------------------------\n")
