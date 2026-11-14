
document.addEventListener("DOMContentLoaded", function () {
    const botao = document.getElementById("alternar-contraste");

    if (!botao) return;

    // Recupera a preferência salva pelo usuário
    const contrasteAtivo =
        localStorage.getItem("altoContraste") === "true";

    function atualizarContraste(ativado) {
        document.body.classList.toggle("alto-contraste", ativado);

        botao.setAttribute("aria-pressed", String(ativado));

        botao.setAttribute(
            "aria-label",
            ativado
                ? "Desativar modo de alto contraste"
                : "Ativar modo de alto contraste"
        );

        botao.textContent = ativado
            ? "Desativar contraste"
            : "Alto contraste";
    }

    atualizarContraste(contrasteAtivo);

    botao.addEventListener("click", function () {
        const ativado =
            !document.body.classList.contains("alto-contraste");

        atualizarContraste(ativado);

        localStorage.setItem("altoContraste", String(ativado));
    });
});
