/* ==========================================================================
   EBF PIBVP — Interações de interface
   - Mostrar/ocultar senha
   - Alternância de tema claro/escuro (persistida em localStorage)
   - Destaque do link de navegação ativo
   ========================================================================== */
(function () {
    "use strict";

    /* ---- Mostrar / ocultar senha --------------------------------------- */
    document.querySelectorAll(".js-toggle-password").forEach(function (button) {
        button.addEventListener("click", function () {
            var input = document.getElementById(button.dataset.target);
            var icon = button.querySelector("i");
            if (!input) return;

            var mostrar = input.type === "password";
            input.type = mostrar ? "text" : "password";
            button.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Visualizar senha");
            if (icon) icon.className = mostrar ? "bi bi-eye-slash" : "bi bi-eye";
        });
    });

    /* ---- Tema claro / escuro ------------------------------------------- */
    var STORAGE_KEY = "ebf-theme";
    var root = document.documentElement;

    // Resolve um tema concreto ("light" ou "dark") a partir da escolha salva
    // ou da preferência do sistema operacional.
    function resolveTheme() {
        var saved = localStorage.getItem(STORAGE_KEY);
        if (saved === "light" || saved === "dark") return saved;
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        root.setAttribute("data-bs-theme", theme); // Bootstrap em sintonia
        var icon = document.querySelector(".theme-toggle i");
        if (icon) icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    }

    // Aplica no carregamento (o script inline do <head> já evitou o "flash").
    applyTheme(resolveTheme());

    var toggle = document.querySelector(".theme-toggle");
    if (toggle) {
        toggle.addEventListener("click", function () {
            var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        });
    }

    /* ---- Menu hambúrguer: rótulo acessível conforme abre/fecha --------- */
    var navCollapse = document.getElementById("navbarNav");
    var burger = document.querySelector(".navbar-toggler.ebf-burger");
    if (navCollapse && burger) {
        navCollapse.addEventListener("show.bs.collapse", function () {
            burger.setAttribute("aria-label", "Fechar menu de navegação");
        });
        navCollapse.addEventListener("hide.bs.collapse", function () {
            burger.setAttribute("aria-label", "Abrir menu de navegação");
        });
    }

    /* ---- Link ativo na navbar ------------------------------------------ */
    var path = window.location.pathname;
    document.querySelectorAll(".app-navbar .nav-link[href]").forEach(function (link) {
        var href = link.getAttribute("href");
        if (href && href !== "/" && path.indexOf(href) === 0) {
            link.classList.add("active");
        }
    });
})();
