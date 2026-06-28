/* ==========================================================================
   EBF PIBVP — Interações de interface
   - Mostrar/ocultar senha
   - Alternância de tema claro/escuro (persistida em localStorage)
   - Destaque do link de navegação ativo
   ========================================================================== */
(function () {
    "use strict";

    /* ---- Anti duplo-envio: spinner no botão ao enviar formulário -------- */
    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            // Respeita cancelamentos (ex.: confirm() retornou "Cancelar")
            if (e.defaultPrevented) return;
            // Formulário pode optar por sair: <form data-no-loading>
            if (form.hasAttribute("data-no-loading")) return;
            // Já está enviando? bloqueia novo envio (ex.: tecla Enter repetida)
            if (form.dataset.loading === "1") { e.preventDefault(); return; }

            var btn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!btn) return;

            form.dataset.loading = "1";
            // Fixa a largura para o botão não "encolher" ao trocar o conteúdo
            btn.style.minWidth = btn.offsetWidth + "px";

            // Desabilita só no próximo tick, garantindo que o valor do botão
            // ainda seja enviado junto com o formulário.
            setTimeout(function () {
                btn.disabled = true;
                btn.setAttribute("aria-busy", "true");
                btn.innerHTML =
                    '<span class="spinner-border spinner-border-sm align-middle" role="status" aria-hidden="true"></span>' +
                    ' <span class="align-middle">Aguarde...</span>';
            }, 0);
        });
    });

    /* ---- Máscara de telefone: (11) 99999-9999 -------------------------- */
    function formatarTelefone(valor) {
        var d = (valor || "").replace(/\D/g, "").slice(0, 11);   // só dígitos, máx 11
        if (!d) return "";
        if (d.length <= 2) return "(" + d;
        var ddd = "(" + d.slice(0, 2) + ") ";
        var resto = d.slice(2);
        if (resto.length <= 4) return ddd + resto;
        if (resto.length <= 8) return ddd + resto.slice(0, resto.length - 4) + "-" + resto.slice(resto.length - 4);
        return ddd + resto.slice(0, 5) + "-" + resto.slice(5);     // celular (11 dígitos)
    }
    document.querySelectorAll(".js-telefone").forEach(function (input) {
        var aplicar = function () { input.value = formatarTelefone(input.value); };
        input.addEventListener("input", aplicar);
        aplicar();   // formata o valor inicial (ex.: vindo do banco)
    });

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

    /* ---- Checklist de requisitos de senha (cadastro e troca de senha) --- */
    function initPasswordChecklist(opts) {
        var senhaInput = document.getElementById(opts.senha1);
        var reqTamanho = document.getElementById(opts.reqTamanho);
        if (!senhaInput || !reqTamanho) return;

        var reqSimilar = document.getElementById(opts.reqSimilar);
        var reqNumerico = document.getElementById(opts.reqNumerico);
        var reqIguais = document.getElementById(opts.reqIguais);
        var reqComum = document.getElementById(opts.reqComum);
        var nomeInput = document.getElementById(opts.nome);
        var emailInput = document.getElementById(opts.email);
        var senha2Input = document.getElementById(opts.senha2);

        var marcar = function (li, ok) {
            var icon = li.querySelector("i");
            li.classList.toggle("ok", ok);
            if (icon) icon.className = ok ? "bi bi-check-circle-fill" : "bi bi-circle";
        };

        // Reproduz o cálculo do UserAttributeSimilarityValidator do Django:
        // SequenceMatcher(a, b).quick_ratio() >= 0.7 é considerado "parecido".
        // quick_ratio = 2 * (soma das contagens mínimas de cada caractere
        // em comum) / (tamanho de a + tamanho de b).
        var quickRatio = function (a, b) {
            if (!a.length || !b.length) return 0;
            var contagemA = {};
            for (var i = 0; i < a.length; i++) contagemA[a[i]] = (contagemA[a[i]] || 0) + 1;
            var contagemB = {};
            for (var j = 0; j < b.length; j++) contagemB[b[j]] = (contagemB[b[j]] || 0) + 1;
            var matches = 0;
            for (var c in contagemA) {
                if (contagemB[c]) matches += Math.min(contagemA[c], contagemB[c]);
            }
            return (2 * matches) / (a.length + b.length);
        };

        // Django também testa cada "pedaço" do valor (split por re.split(r'\W+', ...)),
        // além do valor inteiro — ex.: e-mail "ana@gmail.com" gera "ana", "gmail", "com".
        // \W no Python (Unicode) trata letras acentuadas como parte da palavra,
        // então usamos \p{L}\p{N}_ aqui para não fragmentar nomes como "João".
        var partesDe = function (valor) {
            if (!valor) return [];
            var partes = valor.split(/[^\p{L}\p{N}_]+/u).filter(Boolean);
            partes.push(valor);
            return partes;
        };

        // Mesma otimização do Django: ignora pedaços muito menores que a senha,
        // pois matematicamente nunca atingiriam o limiar de similaridade.
        var excedeRazaoDeTamanho = function (senha, valuePart) {
            var pwdLen = senha.length;
            var limiteSimilaridade = (0.7 / 2) * pwdLen;
            var valueLen = valuePart.length;
            return pwdLen >= 10 * valueLen && valueLen < limiteSimilaridade;
        };

        var pareceComDado = function (senha, dado) {
            senha = senha.toLowerCase();
            var partes = partesDe(dado);
            for (var i = 0; i < partes.length; i++) {
                var parte = partes[i].toLowerCase();
                if (excedeRazaoDeTamanho(senha, parte)) continue;
                if (quickRatio(senha, parte) >= 0.7) return true;
            }
            return false;
        };

        var validar = function () {
            var senha = senhaInput.value;
            marcar(reqTamanho, senha.length >= 8);
            marcar(reqNumerico, senha.length > 0 && !/^\d+$/.test(senha));

            // Mesma lista usada pelo Django (CommonPasswordValidator), carregada
            // via static/js/common-passwords.js.
            if (reqComum) {
                var lista = window.EBF_COMMON_PASSWORDS;
                var comum = !!lista && lista.has(senha.toLowerCase());
                marcar(reqComum, senha.length > 0 && !comum);
            }

            var nome = nomeInput ? nomeInput.value : "";
            var nomeParts = nome.trim().split(/\s+/);
            var email = emailInput ? emailInput.value : "";

            var similar = senha.length === 0 ||
                pareceComDado(senha, email) ||
                nomeParts.some(function (parte) { return pareceComDado(senha, parte); });
            marcar(reqSimilar, senha.length > 0 && !similar);

            if (reqIguais) marcar(reqIguais, senha2Input.value.length > 0 && senha === senha2Input.value);
        };

        senhaInput.addEventListener("input", validar);
        if (nomeInput) nomeInput.addEventListener("input", validar);
        if (emailInput) emailInput.addEventListener("input", validar);
        if (senha2Input) senha2Input.addEventListener("input", validar);
    }

    var checklistIds = {
        reqTamanho: "req-tamanho",
        reqSimilar: "req-similar",
        reqNumerico: "req-numerico",
        reqIguais: "req-iguais",
        reqComum: "req-comum",
    };
    // Cadastro de responsável (página de registro)
    initPasswordChecklist(Object.assign({}, checklistIds, {
        senha1: "id_password1", senha2: "id_password2", nome: "id_nome_completo", email: "id_email",
    }));
    // Troca de senha (perfil do usuário já autenticado)
    initPasswordChecklist(Object.assign({}, checklistIds, {
        senha1: "id_new_password1", senha2: "id_new_password2", nome: "id_nome_atual", email: "id_email_atual",
    }));

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
