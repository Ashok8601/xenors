function toggleMenu() {
    const nav = document.getElementById('nav');
    nav.classList.toggle('active');
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('#nav a').forEach(link => {
        link.onclick = () => {
            document.getElementById('nav').classList.remove('active');
        };
    });
});
