// ==================================================
// MTG Utils (compartido por TODOS los templates)
// ==================================================

window.MTGUtils = window.MTGUtils || {};

// --------------------------------------------------
// Conversión PT -> PX (valores base por defecto)
// Cada template puede sobreescribir los factores
// --------------------------------------------------
MTGUtils.FONT_PT_TO_PX = 20 / 8.6;
MTGUtils.LEADING_PT_TO_PX = 29 / 13.2;

MTGUtils.ptToPx = function (pt, factor = MTGUtils.FONT_PT_TO_PX) {
    if (pt == null) return null;
    return pt * factor;
};

MTGUtils.leadingPtToPx = function (pt, factor = MTGUtils.LEADING_PT_TO_PX) {
    if (pt == null) return null;
    return pt * factor;
};

// --------------------------------------------------
// Mana icons render (para RULES / FLAVOR text)
// Usa mana-font (Andrew Gioia)
// --------------------------------------------------
MTGUtils.renderManaIcons = function (text, options = {}) {
    if (!text) return "";

    const {
        size = null,          // ej: "1em"
        valign = null,        // ej: "-0.1em"
        extraClass = ""       // clase extra por template
    } = options;

    const map = {
        "W": "ms-w",
        "U": "ms-u",
        "B": "ms-b",
        "R": "ms-r",
        "G": "ms-g",
        "T": "ms-tap",
        "Q": "ms-untap"
    };

    return text.replace(/\{([^}]+)\}/g, (match, symbol) => {
        const cls = map[symbol];
        if (!cls) return match;

        let style = "";
        if (size) style += `font-size:${size};`;
        if (valign) style += `vertical-align:${valign};`;

        return `<i class="ms ${cls} ${extraClass}"${style ? ` style="${style}"` : ""}></i>`;
    });
};

// --------------------------------------------------
// Build colored mana cost DOM (mana cost superior)
// Usa SVGs de Scryfall
// --------------------------------------------------
MTGUtils.buildManaCostNode = function (manaCost, options = {}) {
    if (!manaCost) return null;

    const tokens = manaCost.match(/\{[^}]+\}/g);
    if (!tokens) return null;

    const {
        size = 22,     // tamaño por defecto
        gap = 2        // espacio entre símbolos
    } = options;

    const wrapper = document.createElement("div");
    wrapper.style.display = "flex";
    wrapper.style.alignItems = "center";
    wrapper.style.gap = gap + "px";

    tokens.forEach(token => {
        const svgUrl = window.scrySymbols?.[token];
        if (!svgUrl) return;

        const img = document.createElement("img");
        img.src = svgUrl;
        img.style.width = size + "px";
        img.style.height = size + "px";
        img.style.pointerEvents = "none";
        img.style.userSelect = "none";
        img.draggable = false;

        wrapper.appendChild(img);
    });

    return wrapper;
};

// --------------------------------------------------
// PT converter por template (factory)
// --------------------------------------------------
MTGUtils.createPtConverter = function ({
    fontRatio,
    leadingRatio
}) {
    return {
        FONT_PT_TO_PX: fontRatio,
        LEADING_PT_TO_PX: leadingRatio,

        ptToPx(pt) {
            if (pt == null) return null;
            return pt * this.FONT_PT_TO_PX;
        },

        leadingPtToPx(pt) {
            if (pt == null) return null;
            return pt * this.LEADING_PT_TO_PX;
        }
    };
};
