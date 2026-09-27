function toggleMenu() {
    const nav = document.getElementById('nav');
    nav.classList.toggle('active');

    document.body.style.overflow =
        nav.classList.contains('active') ? 'hidden' : 'auto';
}

document.querySelectorAll('#nav a').forEach(link => {
    link.onclick = () => {
        document.getElementById('nav').classList.remove('active');
        document.body.style.overflow = 'auto';
    };
});
