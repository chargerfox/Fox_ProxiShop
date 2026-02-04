#include "scripts/render.jsx";

var f = File.openDialog("Seleccioná el CSV de render", "*.csv");

if (!f) {
    alert("No se seleccionó ningún archivo.");
} else {

    // Por seguridad: si viene como array, tomamos el primero
    if (f instanceof Array) {
        f = f[0];
    }

    render(f);
}
