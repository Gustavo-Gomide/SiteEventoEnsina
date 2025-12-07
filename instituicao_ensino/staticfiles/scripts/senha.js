document.addEventListener("DOMContentLoaded", function() {
    const toggles = document.querySelectorAll('.toggle-senha');
    toggles.forEach(toggle => {
        const targetId = toggle.dataset.target;
        let input = null;
        if (targetId) input = document.getElementById(targetId);
        if (!input) {
            const container = toggle.closest('.senha-container');
            if (container) input = container.querySelector('input');
        }

        const iconShow = toggle.querySelector('.icon-show');
        const iconHide = toggle.querySelector('.icon-hide');
        if (!input) return;

        toggle.addEventListener('click', () => {
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            if (iconShow && iconHide) {
                iconShow.classList.toggle('active');
                iconHide.classList.toggle('active');
            }
        });
    });
});
