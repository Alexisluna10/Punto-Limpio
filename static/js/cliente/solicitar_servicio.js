document.addEventListener("DOMContentLoaded", () => {
  const carousel = document.getElementById("serviciosCarousel");
  const radios = document.querySelectorAll('input[name="tipo_servicio"]');
  const direccionContainer = document.getElementById("direccion-container");
  const indicators = document.querySelectorAll(".indicator-dot");

  function scrollCarousel(direction) {
    const scrollAmount = 305;

    if (direction === "next") {
      carousel.scrollBy({ left: scrollAmount, behavior: "smooth" });
    } else {
      carousel.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    }
  }

  window.scrollCarousel = scrollCarousel;

  carousel.addEventListener("scroll", () => {
    const scrollPosition = carousel.scrollLeft;
    const itemWidth = 305;
    const currentIndex = Math.round(scrollPosition / itemWidth);

    indicators.forEach((dot, index) => {
      dot.classList.toggle("active", index === currentIndex);
    });
  });

  indicators.forEach((dot, index) => {
    dot.addEventListener("click", () => {
      const scrollAmount = index * 305;
      carousel.scrollTo({ left: scrollAmount, behavior: "smooth" });
    });
  });

  radios.forEach((radio) => {
    radio.addEventListener("change", () => {
      if (radio.value === "por_encargo" || radio.value === "a_domicilio") {
        direccionContainer.classList.remove("hidden-direccion");
        direccionContainer.classList.add("visible-direccion");
      } else {
        direccionContainer.classList.remove("visible-direccion");
        direccionContainer.classList.add("hidden-direccion");
      }
    });
  });

  window.continuar = function () {
    const seleccionado = document.querySelector(
      'input[name="tipo_servicio"]:checked'
    );

    if (!seleccionado) {
      alert("Por favor, selecciona un tipo de servicio");
      return;
    }

    if (
      seleccionado.value === "por_encargo" ||
      seleccionado.value === "a_domicilio"
    ) {
      const direccion = document.getElementById("direccion").value.trim();
      if (!direccion) {
        alert("Por favor, ingresa la dirección para el servicio");
        document.getElementById("direccion").focus();
        return;
      }
    }

    if (seleccionado.value === "autoservicio") {
      window.location.href = window.URL_AUTOSERVICIO;
    } else {
      window.location.href =
        window.URL_SERV_COSTO + "?tipo=" + seleccionado.value;
    }
  };

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") scrollCarousel("prev");
    if (e.key === "ArrowRight") scrollCarousel("next");
  });

  let touchStartX = 0;
  let touchEndX = 0;

  carousel.addEventListener("touchstart", (e) => {
    touchStartX = e.changedTouches[0].screenX;
  });

  carousel.addEventListener("touchend", (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  });

  function handleSwipe() {
    const swipeThreshold = 50;
    if (touchStartX - touchEndX > swipeThreshold) {
      scrollCarousel("next");
    } else if (touchEndX - touchStartX > swipeThreshold) {
      scrollCarousel("prev");
    }
  }
});
