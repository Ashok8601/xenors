document.addEventListener('DOMContentLoaded', () => {
    console.log("About page loaded successfully.");

    // Simple fade-in effect for the content boxes
    const boxes = document.querySelectorAll('.content-box');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    boxes.forEach(box => {
        box.style.opacity = 0;
        box.style.transform = 'translateY(20px)';
        box.style.transition = 'all 0.6s ease-out';
        observer.observe(box);
    });
});
