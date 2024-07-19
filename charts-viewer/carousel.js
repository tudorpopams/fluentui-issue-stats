class ImageCarousel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });

    this.shadowRoot.innerHTML = `
            <div class="carousel-container">
                <div class="carousel">
                    ${this.innerHTML}
                </div>
            </div>
            <div class="controls">
                <button id="prevButton">Previous</button>
                <button id="nextButton">Next</button>
            </div>
            <div class="slider-container">
                <input type="range" class="slider" min="0" value="0" step="1">
            </div>
            <style>
                .carousel-container {
                    position: relative;
                    width: 80%;
                    max-width: 800px;
                    overflow: hidden;
                    border: 1px solid #ddd;
                    background-color: #fff;
                    margin-bottom: 20px;
                }
                .carousel {
                    display: flex;
                }
                .carousel img {
                    width: 100%;
                    object-fit: cover;
                }
                .controls {
                    display: flex;
                    justify-content: space-between;
                    width: 100%;
                    margin-top: 10px;
                }
                .controls button {
                    padding: 10px 20px;
                    border: none;
                    background-color: #007bff;
                    color: #fff;
                    cursor: pointer;
                }
                .controls button:disabled {
                    background-color: #ccc;
                    cursor: not-allowed;
                }
                .slider-container {
                    width: 100%;
                    display: flex;
                    justify-content: center;
                    margin-top: 10px;
                }
                .slider {
                    width: 80%;
                }
            </style>
        `;

    this.carousel = this.shadowRoot.querySelector(".carousel");
    this.slider = this.shadowRoot.querySelector(".slider");
    this.prevButton = this.shadowRoot.querySelector("#prevButton");
    this.nextButton = this.shadowRoot.querySelector("#nextButton");

    this.images = this.carousel.querySelectorAll("img");
    this.slider.max = this.images.length - 1;

    this.slider.addEventListener("input", () =>
      this.slideImages(this.slider.value)
    );
    this.prevButton.addEventListener("click", () => this.navigate(-1));
    this.nextButton.addEventListener("click", () => this.navigate(1));

    this.updateButtons(this.slider.value);
  }

  slideImages(value) {
    const width = this.shadowRoot.querySelector(
      ".carousel-container"
    ).clientWidth;
    this.carousel.style.transform = `translateX(-${value * width}px)`;
    this.updateButtons(value);
  }

  navigate(direction) {
    let newValue = parseInt(this.slider.value) + direction;
    this.slider.value = newValue;
    this.slideImages(newValue);
  }

  updateButtons(value) {
    this.prevButton.disabled = value <= 0;
    this.nextButton.disabled = value >= this.slider.max;
  }
}

customElements.define("image-carousel", ImageCarousel);
