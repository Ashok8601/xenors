// ==========================
// NAVBAR TOGGLE
// ==========================
const nav = document.getElementById('nav');
const menuToggle = document.querySelector('.menu-toggle');

function toggleMenu() {
    if (nav) nav.classList.toggle('active');
}

// Close menu on link click
document.querySelectorAll('#nav a').forEach(link => {
    link.addEventListener('click', () => {
        if (nav) nav.classList.remove('active');
    });
});

// Close menu on outside click
document.addEventListener('click', function (event) {
    if (!nav || !menuToggle) return;

    if (nav.classList.contains('active')) {
        if (!nav.contains(event.target) && !menuToggle.contains(event.target)) {
            nav.classList.remove('active');
        }
    }
});


// ==========================
// HEADER SCROLL EFFECT
// ==========================
const header = document.querySelector('header');

window.addEventListener('scroll', () => {
    if (!header) return;

    if (window.scrollY > 50) {
        header.style.padding = "0.7rem 10%";
    } else {
        header.style.padding = "1rem 10%";
    }
});


// ==========================
// SEARCH FORM REDIRECT
// ==========================
const searchForm = document.getElementById('searchForm');

if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const input = document.getElementById('searchInput');
        if (!input) return;

        const query = input.value.trim();

        if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    });
}


// ==========================
// AUTO SCROLL POSTS (OPTIMIZED)
// ==========================
const container = document.getElementById("postContainer");
let scrollInterval;

function startAutoScroll() {
    if (!container) return;

    scrollInterval = setInterval(() => {
        container.scrollBy({
            left: 300,
            behavior: "smooth"
        });

        // Reset scroll
        if (container.scrollLeft + container.clientWidth >= container.scrollWidth) {
            container.scrollTo({ left: 0, behavior: "smooth" });
        }
    }, 3000);
}

function stopAutoScroll() {
    clearInterval(scrollInterval);
}

// Pause when tab inactive
document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        stopAutoScroll();
    } else {
        startAutoScroll();
    }
});

if (container) {
    startAutoScroll();
}


// ==========================
// POSTS DATA (FUTURE: JSON FETCH)
// ==========================
const posts = [
    { title: "AI in Stock Market", link: "/blog/ai-stock-market" },
    { title: "Flask Backend Guide", link: "/blog/flask-backend" },
    { title: "Top AI Tools 2026", link: "/blog/ai-tools" },
    { title: "Beginner Finance Tips", link: "/blog/finance-tips" }
];


// ==========================
// LIVE SEARCH (DEBOUNCED + SAFE)
// ==========================
const searchBox = document.getElementById("searchBox");
const results = document.getElementById("results");

let debounceTimeout;

if (searchBox && results) {
    searchBox.addEventListener("keyup", () => {
        clearTimeout(debounceTimeout);

        debounceTimeout = setTimeout(() => {
            const query = searchBox.value.toLowerCase().trim();
            results.innerHTML = "";

            if (!query) return;

            const filtered = posts.filter(post =>
                post.title.toLowerCase().includes(query)
            );

            filtered.forEach(post => {
                const div = document.createElement("div");
                const link = document.createElement("a");

                link.href = post.link;
                link.textContent = post.title;

                div.appendChild(link);
                results.appendChild(div);
            });
        }, 300); // debounce delay
    });
}
