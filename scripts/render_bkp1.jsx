#include "json2.js";
#include "layouts.jsx";
#include "templates.jsx";
#include "constants.jsx";
#include "../settings.jsx";

/* =========================================================
   STRING UTILS (ExtendScript compatible)
========================================================= */

function trim_str(s) {
    return s.replace(/^\s+|\s+$/g, "");
}

/* =========================================================
   CSV UTILS
========================================================= */

function read_csv(file) {
    if (!file.exists) {
        throw new Error("CSV no existe: " + file.fsName);
    }

    file.open("r");
    var content = file.read();
    file.close();

    var lines = content.split(/\r?\n/);
    var rows = [];

    for (var i = 0; i < lines.length; i++) {
        var line = trim_str(lines[i]);
        if (line === "") continue;

        var cols = line.split(",");

        rows.push({
            name: cols[0] ? trim_str(cols[0]) : "",
            set: cols[1] ? trim_str(cols[1]).toLowerCase() : "",
            template: cols[2] ? trim_str(cols[2]) : "",
            collector: cols[3] ? trim_str(cols[3]) : ""
        });
    }

    return rows;
}

/* =========================================================
   PATH RESOLUTION
========================================================= */

function build_art_path(file_path, set_code, card_name, collector) {
    var base = file_path + "/art/" + set_code.toUpperCase() + "/";
    var filename = card_name;

    if (collector && collector !== "") {
        filename += " " + collector;
    }

    return new File(base + filename + ".jpg");
}

/* =========================================================
   PYTHON BRIDGE
========================================================= */

function call_python(card_arg, file_path) {
    /**
     * Calls the Python script which queries Scryfall for card info and saves the resulting JSON dump to disk in \scripts.
     */

    var scryfall_info_command =
        python_command +
        " \"" + file_path + "/scripts/get_card_info.py\" \"" +
        card_arg + "\"";

    app.system(scryfall_info_command);

    var json_file = new File(file_path + json_file_path);
    json_file.open('r');
    var json_string = json_file.read();
    json_file.close();

    if (json_string === "") {
        throw new Error(
            "\n\ncard.json does not exist - the system failed to successfully run get_card_info.py.\n" +
            "Command:\n\n" + scryfall_info_command
        );
    }

    // ✅ Ahora el JSON ya es real, no string dentro de string
    return JSON.parse(json_string);
}


/* =========================================================
   TEMPLATE SELECTION
========================================================= */

function select_template(layout, file, file_path, forced_template_name) {
    /**
     * Instantiate a template object based on the card layout and CSV template override.
     */

    var class_template_map = {};
    class_template_map[normal_class] = {
        default_: NormalTemplate,
        other: [
            NormalClassicTemplate,
			OldClassicTemplate,   // 👈 AQUI
            NormalExtendedTemplate,
            WomensDayTemplate,
            StargazingTemplate,
            MasterpieceTemplate,
            ExpeditionTemplate,
        ],
    };
    class_template_map[transform_front_class] = {
        default_: TransformFrontTemplate,
        other: [],
    };
    class_template_map[transform_back_class] = {
        default_: TransformBackTemplate,
        other: [],
    };
    class_template_map[ixalan_class] = {
        default_: IxalanTemplate,
        other: [],
    };
    class_template_map[mdfc_front_class] = {
        default_: MDFCFrontTemplate,
        other: [],
    };
    class_template_map[mdfc_back_class] = {
        default_: MDFCBackTemplate,
        other: [],
    };
    class_template_map[mutate_class] = {
        default_: MutateTemplate,
        other: [],
    };
    class_template_map[adventure_class] = {
        default_: AdventureTemplate,
        other: [],
    };
    class_template_map[leveler_class] = {
        default_: LevelerTemplate,
        other: [],
    };
    class_template_map[saga_class] = {
        default_: SagaTemplate,
        other: [],
    };
    class_template_map[miracle_class] = {
        default_: MiracleTemplate,
        other: [],
    };
    class_template_map[planeswalker_class] = {
        default_: PlaneswalkerTemplate,
        other: [
            PlaneswalkerExtendedTemplate,
        ],
    };
    class_template_map[snow_class] = {
        default_: SnowTemplate,
        other: [],
    };
    class_template_map[basic_class] = {
        default_: BasicLandTemplate,
        other: [
            BasicLandClassicTemplate,
            BasicLandTherosTemplate,
            BasicLandUnstableTemplate,
        ],
    };
    class_template_map[planar_class] = {
        default_: PlanarTemplate,
        other: [],
    };
    class_template_map[token_class] = {
        default_: TokenTemplate,
        other: [],
    };

    var template_class = class_template_map[layout.card_class];
    var template = template_class.default_;

    // CSV override
    if (forced_template_name && forced_template_name !== "") {
        try {
            var forced = eval(forced_template_name);
            if (in_array(template_class.other, forced) || template === forced) {
                template = forced;
            }
        } catch (e) {
            alert("Template inválido en CSV: " + forced_template_name);
        }
    }

    return new template(layout, file, file_path);
}

/* =========================================================
   MAIN RENDER
========================================================= */

function render(csv_file) {
    var file_path = File($.fileName).parent.parent.fsName;

    if (!csv_file || !csv_file.exists) {
        throw new Error("CSV inválido o no existe.");
    }

    //alert("Cargando lista: " + csv_file.fsName);

    var rows = read_csv(csv_file);
    //alert("Cartas a procesar: " + rows.length);

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];

        if (!row.name || !row.set) {
            alert("Fila inválida en CSV (name / set vacíos)");
            continue;
        }

        var card_name = row.name;
        var set_code = row.set;
        var collector = row.collector;
        var forced_template = row.template;

        // -----------------------------------
        // Resolver imagen
        // -----------------------------------
        var art_file = build_art_path(
            file_path,
            set_code,
            card_name,
            collector
        );

        if (!art_file.exists) {
            alert("Imagen no encontrada:\n" + art_file.fsName);
            continue;
        }

        // -----------------------------------
        // Armar argumento para Python
        // name$set$collector (collector opcional)
        // -----------------------------------

        var card_arg = card_name + "$" + set_code;

        if (collector && collector !== "") {
            card_arg += "$" + collector;
        }

        // -----------------------------------
        // Obtener datos Scryfall
        // -----------------------------------
        var scryfall = call_python(card_arg, file_path);

        // --- get_set_info.py ---
		// Solo ejecutar si NO es OldClassicTemplate
		if (forced_template !== "OldClassicTemplate") {

			var set_info_command =
				python_command +
				" \"" + file_path + "/scripts/get_set_info.py\" \"" +
				scryfall.set + "\"";

			app.system(set_info_command);

			var json_file = new File(file_path + json_file_path);
			json_file.open('r');
			var json_string = json_file.read();
			json_file.close();

			// ✅ card.json ahora es JSON válido directo
			scryfall = JSON.parse(json_string);
		}

        // ----------------------------------------------------

        var layout_name = scryfall.layout;
        var layout;

        if (layout_name in layout_map) {
            layout = new layout_map[layout_name](scryfall, card_name);
        } else {
            alert("Layout no soportado: " + layout_name);
            continue;
        }

        // -----------------------------------
        // Seleccionar template
        // -----------------------------------
        var renderer = select_template(
            layout,
            art_file,
            file_path,
            forced_template
        );

        // -----------------------------------
        // Ejecutar render
        // -----------------------------------
        var file_name = renderer.execute();

        // Guardar y cerrar como el pipeline original
        // save_and_close(file_name, file_path);
    }

    // alert("Render finalizado ✔");
}
