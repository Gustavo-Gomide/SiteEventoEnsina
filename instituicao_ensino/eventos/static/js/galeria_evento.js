document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('mobileLightbox');
    const carouselEl = document.getElementById('carouselMobile');
    const carousel = bootstrap.Carousel.getOrCreateInstance(carouselEl);

    modal.addEventListener('show.bs.modal', function (event) {
        const trigger = event.relatedTarget;
        const index = parseInt(trigger.getAttribute('data-bs-slide-to'));
        carousel.to(index);
    });
});