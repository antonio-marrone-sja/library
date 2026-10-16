// Piccole migliorie dell'interfaccia: l'app funziona anche senza JavaScript.

document.addEventListener("DOMContentLoaded", () => {
    setupNavToggle();
    setupFlashMessages();
    setupConfirmForms();
    setupSelectFilters();
    setupCoverImages();
    setupCoverPreview();
});

// Menu a scomparsa su schermi piccoli
function setupNavToggle() {
    const toggle = document.querySelector("[data-nav-toggle]");
    const nav = document.querySelector("[data-nav]");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", () => {
        const open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open);
    });
}

// Chiusura manuale dei messaggi e chiusura automatica di quelli di successo
function setupFlashMessages() {
    const hide = (flash) => {
        flash.classList.add("hiding");
        setTimeout(() => flash.remove(), 300);
    };

    document.querySelectorAll("[data-flash-close]").forEach((button) => {
        button.addEventListener("click", () => hide(button.closest(".flash")));
    });

    document.querySelectorAll(".flash-success").forEach((flash) => {
        setTimeout(() => hide(flash), 5000);
    });
}

// Chiede conferma prima di inviare i form con l'attributo data-confirm
function setupConfirmForms() {
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
}

// Filtra le opzioni di una <select> mentre si scrive nel campo collegato
function setupSelectFilters() {
    document.querySelectorAll("[data-filter-for]").forEach((input) => {
        const select = document.getElementById(input.dataset.filterFor);
        if (!select) return;

        input.addEventListener("input", () => {
            const text = input.value.trim().toLowerCase();
            for (const option of select.options) {
                option.hidden = !option.textContent.toLowerCase().includes(text);
            }
        });
    });
}

// Se una copertina non si carica, la nasconde e resta l'iniziale del titolo
function setupCoverImages() {
    document.querySelectorAll("img[data-cover]").forEach((img) => {
        img.addEventListener("error", () => img.remove());
        if (img.complete && img.naturalWidth === 0) img.remove();
    });
}

// Anteprima della copertina nel form "Nuovo libro"
function setupCoverPreview() {
    const input = document.querySelector("[data-cover-input]");
    const preview = document.querySelector("[data-cover-preview]");
    if (!input || !preview) return;

    const img = preview.querySelector("img");

    const update = () => {
        const url = input.value.trim();
        preview.hidden = !url;
        if (url) img.src = url;
    };

    img.addEventListener("error", () => { preview.hidden = true; });
    input.addEventListener("change", update);
    update();
}
