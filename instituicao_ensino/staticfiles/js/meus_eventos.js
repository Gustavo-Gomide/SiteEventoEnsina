// =============================
// MEUS EVENTOS - Scripts
// =============================

// Troca de botão de inscrição (Inscrever / Cancelar) sem recarregar
document.addEventListener("DOMContentLoaded", function () {
    const listaEventos = document.querySelectorAll(".list-group-item");

    listaEventos.forEach(item => {
        item.addEventListener("click", function () {
            // Remove 'active' de todos
            listaEventos.forEach(i => i.classList.remove("active"));
            // Marca o clicado
            item.classList.add("active");
        });
    });
});
