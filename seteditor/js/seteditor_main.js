// seteditor/js/seteditor_main.js

// Referencias a elementos del DOM
const btnLoad = document.getElementById("btn-load");
const btnSave = document.getElementById("btn-save");
const setList = document.getElementById("set-list");
const cardList = document.getElementById("card-list");
const cardListLabel = document.getElementById("card-list-label");
const preview1Img = document.getElementById("preview1-img");
const templateLabel = document.getElementById("template-label");
const preview2Panel = document.getElementById("preview2-panel");

// Filtros
const colorFilterSelect = document.getElementById("filter-color");
const typeFilterSelect = document.getElementById("filter-type");
const collectorFilterSelect = document.getElementById("filter-collector");

// Idioma
const languageFilterSelect = document.getElementById("filter-language");

// Estado actual
let currentSetKey = null;
let currentCards = [];
let filteredCards = [];
let selectedCardId = null;

// Buffers por template
let templateBuffers = {};

// ----------------------------
// Helper idioma (SIN FALLBACK)
// ----------------------------
function getLangField(card, baseField) {
    const lang = languageFilterSelect?.value || "en";

    if (lang === "es") {
        return card[baseField + "_es"];
    }

    return card[baseField];
}

// ----------------------------
// Funciones auxiliares
// ----------------------------
function clearList(listElement) {
    listElement.innerHTML = "";
}

// Versión corregida: recibe el contenedor padre
function createListItem(text, parentList, onClick) {
    const li = document.createElement("li");
    li.textContent = text;
    li.addEventListener("click", () => {
        Array.from(parentList.children).forEach(el => el.classList.remove("active"));
        li.classList.add("active");
        onClick();
    });
    return li;
}

// ----------------------------
// Inicializar buffer de un template
// ----------------------------
function initTemplateBuffer(templateName) {
    if (!templateName) return;
    if (templateBuffers[templateName]) return;

    templateBuffers[templateName] = {};

    currentCards.forEach(card => {
        const cardId = card.Collector;

        if (window[templateName]?.createEmptyData) {
            templateBuffers[templateName][cardId] =
                window[templateName].createEmptyData(card);
        } else {
            templateBuffers[templateName][cardId] = {};
        }
    });
}

// ----------------------------
// Cargar template dinámicamente
// ----------------------------
function loadTemplate(templateName, callback) {
    if (!templateName) return;

    // Ya cargado
    if (window[templateName]) {
        callback();
        return;
    }

    const scriptSrc = `templates/${templateName}.js`;

    // Evitar cargar dos veces
    if (document.querySelector(`script[src="${scriptSrc}"]`)) {
        const wait = setInterval(() => {
            if (window[templateName]) {
                clearInterval(wait);
                callback();
            }
        }, 50);
        return;
    }

    const script = document.createElement("script");
    script.src = scriptSrc;
    script.onload = callback;
    script.onerror = () => {
        console.error("No se pudo cargar el template:", scriptSrc);
    };

    document.body.appendChild(script);
}


// ----------------------------
// Cargar sets en la lista
// ----------------------------
function loadSets() {
    clearList(setList);

    for (const setKey in EXPANSIONS) {
        const set = EXPANSIONS[setKey];
        const li = createListItem(`${set.symbol} ${set.name}`, setList, () => {
            selectSet(setKey);
        });
        setList.appendChild(li);
    }
}

// ----------------------------
// Seleccionar un set
// ----------------------------
function selectSet(setKey) {
    currentSetKey = setKey;
    clearList(cardList);
    preview1Img.src = "";
    preview2Panel.innerHTML = "";
    templateBuffers = {};
    templateLabel.textContent = "";

    const scriptSrc = `data/${setKey.toUpperCase()}.js`;

    const loadCards = () => {

		// Mapeo explícito setKey → variable JS
		const SET_VAR_MAP = {
			"2ed": "ED2",
			"3ed": "ED3",
			"4ed": "ED4",
			"5ed": "ED5",
			"6ed": "ED6",
			"7ed": "ED7",
			"8ed": "ED8",
			"9ed": "ED9",
			"10e": "E10",
			// agregás acá otros sets numéricos si aparecen
		};

		const cardsVarName =
			SET_VAR_MAP[setKey] || setKey.toUpperCase();

		currentCards = window[cardsVarName] || [];

		applyFiltersAndPopulate();

		if (currentCards.length > 0) {
			selectCard(0);
			cardList.children[0]?.classList.add("active");
		}
	};


    if (!document.querySelector(`script[src='${scriptSrc}']`)) {
        const script = document.createElement("script");
        script.src = scriptSrc;
        script.onload = loadCards;
        document.body.appendChild(script);
    } else {
        loadCards();
    }
}

// ----------------------------
// Aplicar filtros y renderizar lista
// ----------------------------
function applyFiltersAndPopulate() {
    filteredCards = [...currentCards];

    // Color
    const colorFilter = colorFilterSelect?.value || "None";
    filteredCards = filteredCards.filter(card => {
        const colors = card.color_identity || [];
        if (colorFilter === "None") return true;
        if (colorFilter === "Gld") return colors.length > 3;
        return colors.includes(colorFilter);
    });

    // Tipo
    const typeFilter = typeFilterSelect?.value || "None";
    if (typeFilter !== "None") {
        filteredCards = filteredCards.filter(card => {
            const typeLine = card.Type_Line || "";
            if (typeFilter === "Land") return /Land/i.test(typeLine);
            if (typeFilter === "Artifact") return /Artifact/i.test(typeLine);
            if (typeFilter === "Nonland") return !(/Land|Artifact/i.test(typeLine));
            return true;
        });
    }

    // Orden
    const collectorFilter = collectorFilterSelect?.value || "None";
    if (collectorFilter === "Asc") {
        filteredCards.sort((a, b) => (a.Collector ?? 0) - (b.Collector ?? 0));
    } else if (collectorFilter === "Desc") {
        filteredCards.sort((a, b) => (b.Collector ?? 0) - (a.Collector ?? 0));
    } else {
        filteredCards.sort((a, b) =>
            getLangField(a, "Name").localeCompare(getLangField(b, "Name"))
        );
    }

    populateCardList();
    if (filteredCards.length > 0) selectCard(0);
}

// ----------------------------
// Llenar lista de cartas
// ----------------------------
function populateCardList() {
    clearList(cardList);

    filteredCards.forEach((card, index) => {
        const displayName = getLangField(card, "Name");
        const li = createListItem(`${displayName} (${card.Collector})`, cardList, () => {
            selectCard(index);
        });
        cardList.appendChild(li);
    });

    // 👉 ACTUALIZAR LABEL "Cartas (visibles / total)"
    if (cardListLabel) {
        const visible = filteredCards.length;
        const total = currentCards.length;
        cardListLabel.textContent = `Cartas (${visible} / ${total})`;
    }
}


// ----------------------------
// Mostrar carta seleccionada Y REFRESCAR TOOLBAR
// ----------------------------
// ----------------------------
// Mostrar carta seleccionada Y REFRESCAR TOOLBAR
// ----------------------------
function selectCard(index) {
    const card = filteredCards[index];
    if (!card) return;

    selectedCardId = card.Collector;
    preview1Img.src = card.image_uris?.normal || "";

    const templateName = card.template_set || card.Template_Set;


    if (templateLabel) {
         templateLabel.textContent = templateName || "N/D";
    }

    const toolbar = document.getElementById("template-toolbar");
    if (toolbar) toolbar.innerHTML = "";

    if (!templateName) {
        console.warn("La carta no tiene Template_Set");
        return;
    }

    loadTemplate(templateName, () => {
        if (!window[templateName]) {
            console.warn("Template no disponible:", templateName);
            return;
        }

        initTemplateBuffer(templateName);
        const buffer = templateBuffers[templateName][selectedCardId];

        window[templateName].render({
            card,
            buffer,
            cardId: selectedCardId,
            container: preview2Panel
        });
    });
}


// ----------------------------
// Eventos filtros
// ----------------------------
colorFilterSelect?.addEventListener("change", applyFiltersAndPopulate);
typeFilterSelect?.addEventListener("change", applyFiltersAndPopulate);
collectorFilterSelect?.addEventListener("change", applyFiltersAndPopulate);
languageFilterSelect?.addEventListener("change", () => {
    templateBuffers = {};
    applyFiltersAndPopulate();
});

// ----------------------------
// Evento LOAD
// ----------------------------
btnLoad.addEventListener("click", () => {
    loadSets();
});

// ----------------------------
// Evento SAVE SET
// ----------------------------
btnSave.addEventListener("click", () => {
    if (!currentSetKey || !currentCards.length) {
        alert("No hay set cargado para guardar.");
        return;
    }

    const confirmed = confirm("¿Está seguro que quiere guardar los cambios en el set?");
    if (!confirmed) return;

    const lang = languageFilterSelect?.value || "en";
    const setVarName = currentSetKey.toUpperCase();
    const editedCards = [];

    currentCards.forEach(card => {
        const cardId = card.Collector;
        const templateName = card.Template_Set;
        const buffer = templateBuffers[templateName]?.[cardId] || {};

        const finalCard = { ...card };

        if (lang === "es") {
            if (buffer.name != null) finalCard.Name_es = buffer.name;
            if (buffer.typeline != null) finalCard.Type_Line_es = buffer.typeline;
            if (buffer.text != null) finalCard.Original_Text_es = buffer.text;
            if (buffer.flavor != null) finalCard.Flavor_Text_es = buffer.flavor;
        } else {
            if (buffer.name != null) finalCard.Name = buffer.name;
            if (buffer.typeline != null) finalCard.Type_Line = buffer.typeline;
            if (buffer.text != null) finalCard.Original_Text = buffer.text;
            if (buffer.flavor != null) finalCard.Flavor_Text = buffer.flavor;
        }

        finalCard.Size = buffer.textSize ?? finalCard.Size;
        finalCard.Tracking = buffer.tracking ?? finalCard.Tracking;
        finalCard.Leading = buffer.leading ?? finalCard.Leading;
        finalCard.TextFlavor_Lead = buffer.flavorLead ?? finalCard.TextFlavor_Lead;
        finalCard.OffsetX = buffer.offsetX ?? finalCard.OffsetX;
        finalCard.OffsetY = buffer.offsetY ?? finalCard.OffsetY;
        finalCard.BoxWidthAdjust = buffer.boxWidthAdjust ?? finalCard.BoxWidthAdjust;
        finalCard.Justification = buffer.justification ?? finalCard.Justification;

        editedCards.push(finalCard);
    });

    const fileContent = `var ${setVarName} = ${JSON.stringify(editedCards, null, 2)};`;

    const blob = new Blob([fileContent], { type: "text/javascript" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${setVarName}_edited.js`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert("Set guardado correctamente como " + setVarName + "_edited.js");
});
