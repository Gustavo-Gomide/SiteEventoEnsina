document.addEventListener("DOMContentLoaded", function() {
    const senhaInput = document.getElementById("id_senha");
    const toggle = document.getElementById("toggleSenha");
    const iconShow = document.getElementById("iconShow");
    const iconHide = document.getElementById("iconHide");

    toggle.addEventListener("click", () => {
        const isHidden = senhaInput.type === "password";
        senhaInput.type = isHidden ? "text" : "password";

        iconShow.classList.toggle("active");
        iconHide.classList.toggle("active");
    });
});
