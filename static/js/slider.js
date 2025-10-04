// Simple automatic slider for EXIM Ghana M&E landing page
class SimpleSlider {
    constructor(container) {
        this.container = container;
        this.wrapper = container.querySelector('.slider-content-wrapper');
        this.slides = container.querySelectorAll('.slider-content__item');
        this.currentSlide = 0;
        this.slideCount = this.slides.length;
        this.autoSlideInterval = null;
        
        this.init();
    }
    
    init() {
        if (this.slideCount <= 1) return;
        
        // Start automatic sliding
        this.startAutoSlide();
        
        // Pause on hover
        this.container.addEventListener('mouseenter', () => this.pauseAutoSlide());
        this.container.addEventListener('mouseleave', () => this.startAutoSlide());
        
        // Handle visibility change (pause when tab is not visible)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoSlide();
            } else {
                this.startAutoSlide();
            }
        });
    }
    
    goToSlide(index) {
        if (index < 0 || index >= this.slideCount) return;
        
        this.currentSlide = index;
        const translateX = -100 * this.currentSlide;
        this.wrapper.style.transform = `translateX(${translateX}%)`;
    }
    
    nextSlide() {
        const next = (this.currentSlide + 1) % this.slideCount;
        this.goToSlide(next);
    }
    
    prevSlide() {
        const prev = (this.currentSlide - 1 + this.slideCount) % this.slideCount;
        this.goToSlide(prev);
    }
    
    startAutoSlide() {
        this.pauseAutoSlide(); // Clear any existing interval
        this.autoSlideInterval = setInterval(() => {
            this.nextSlide();
        }, 5000); // Change slide every 5 seconds
    }
    
    pauseAutoSlide() {
        if (this.autoSlideInterval) {
            clearInterval(this.autoSlideInterval);
            this.autoSlideInterval = null;
        }
    }
}

// Initialize slider when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const sliderContainer = document.querySelector('#slider');
    if (sliderContainer) {
        new SimpleSlider(sliderContainer);
    }
});