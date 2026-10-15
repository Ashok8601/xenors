document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    const formStatus = document.getElementById('formStatus');

    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Simple UX: Show loading state
        const btn = document.querySelector('.submit-btn');
        btn.innerText = "Sending...";
        btn.disabled = true;

        // Form Data
        const name = document.getElementById('userName').value;
        const email = document.getElementById('userEmail').value;

        // Simulation (Aap yahan real API call kar sakte hain)
        setTimeout(() => {
            formStatus.innerHTML = `Thanks ${name}! Your message has been sent successfully.`;
            formStatus.style.color = "green";
            
            // Reset Form
            contactForm.reset();
            btn.innerText = "Send Message";
            btn.disabled = false;
        }, 1500);
    });
});
