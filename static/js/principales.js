document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.carousel-image');
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    let currentIndex = 0;
    let intervalId;

    // Función para mostrar la imagen actual
    function showImage(index) {
        images.forEach((img, i) => {
            img.classList.toggle('active', i === index);
        });

        indicators.forEach((indicator, i) => {
            indicator.classList.toggle('active', i === index);
        });
    }

    // Función para avanzar al siguiente slide
    function nextSlide() {
        currentIndex = (currentIndex + 1) % images.length;
        showImage(currentIndex);
    }

    // Función para retroceder al slide anterior
    function prevSlide() {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        showImage(currentIndex);
    }

    // Event listeners para los botones
    nextBtn.addEventListener('click', () => {
        nextSlide();
        resetInterval();
    });

    prevBtn.addEventListener('click', () => {
        prevSlide();
        resetInterval();
    });

    // Event listeners para los indicadores
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => {
            currentIndex = index;
            showImage(currentIndex);
            resetInterval();
        });
    });

    // Función para reiniciar el intervalo automático
    function resetInterval() {
        clearInterval(intervalId);
        startInterval();
    }

    // Función para iniciar el intervalo automático
    function startInterval() {
        intervalId = setInterval(nextSlide, 5000);
    }

    // Iniciar el carrusel
    showImage(currentIndex);
    startInterval();
});