import os
import json

# Carpetas
symbols_layer_name = "SymbolBase"  # Nombre del layer base en SYMBOLS
ref_folder = "nonland"
output_jsx = "duplicate_symbols.jsx"

# Cargar symbol_rules.jsx como diccionario Python
symbol_rules = {}
with open("symbol_rules.jsx", "r", encoding="utf-8") as f:
    content = f.read()
    # Extraemos el diccionario JS (entre { ... })
    dict_text = content.split("{",1)[1].rsplit("}",1)[0]
    # Convertimos a Python: quitar comas finales y keyrune entre ""
    lines = [line.strip().rstrip(",") for line in dict_text.splitlines() if line.strip()]
    for line in lines:
        if ":" in line:
            key, val = line.split(":",1)
            key = key.strip().strip('"')
            # Extraer keyrune del val
            val = val.strip()
            if "keyrune" in val:
                kr = val.split('"')[1]
                symbol_rules[key] = kr

# Lista de imágenes de referencia
ref_images = [f for f in os.listdir(ref_folder) if f.lower().endswith((".png",".jpg"))]

# Generar JSX
with open(output_jsx, "w", encoding="utf-8") as f:
    f.write('// Script auto-generado para duplicar símbolo por set\n')
    f.write('var doc = app.activeDocument;\n')
    f.write(f'var baseLayer = doc.artLayers.getByName("{symbols_layer_name}");\n\n')

    for img in ref_images:
        set_name = os.path.splitext(img)[0]  # quitar extensión
        keyrune = symbol_rules.get(set_name, "?")
        f.write(f'// {set_name}\n')
        f.write(f'var dup = baseLayer.duplicate();\n')
        f.write(f'dup.name = "{set_name}";\n')
        f.write(f'dup.textItem.contents = "{keyrune}";\n\n')

print(f"JSX generado: {output_jsx}")
