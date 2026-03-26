// Function to toggle the mobile menu
function toggleMenu() {
    const nav = document.getElementById('nav');
    nav.classList.toggle('active');
}

// Close menu when clicking on any link
document.querySelectorAll('#nav a').forEach(link => {
    link.addEventListener('click', () => {
        document.getElementById('nav').classList.remove('active');
    });
});

// Close menu when clicking outside the navbar
document.addEventListener('click', function(event) {
    const nav = document.getElementById('nav');
    const menuToggle = document.querySelector('.menu-toggle');
    
    // Check if the menu is open and the click was outside the nav and toggle button
    if (nav.classList.contains('active')) {
        if (!nav.contains(event.target) && !menuToggle.contains(event.target)) {
            nav.classList.remove('active');
        }
    }
});

// Adding a simple scroll effect for header (UX)
window.addEventListener('scroll', () => {
    const header = document.querySelector('header');
    if (window.scrollY > 50) {
        header.style.padding = "0.7rem 10%";
    } else {
        header.style.padding = "1rem 10%";
    }
});
