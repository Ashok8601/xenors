(() => {
  "use strict";

  const article = document.querySelector(".article-content");
  const readingTime = document.getElementById("reading-time");

  // Dynamic reading time
  if (article && readingTime) {
    const words = (article.innerText.match(/\S+/g) || []).length;
    const minutes = Math.max(1, Math.ceil(words / 220));
    readingTime.textContent = `${minutes} min read`;
  }

  // Table-of-contents active state
  const tocLinks = [...document.querySelectorAll(".toc-card a[href^='#']")];
  const sections = tocLinks
    .map(link => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter(entry => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (!visible) return;

      tocLinks.forEach(link => {
        const active = link.getAttribute("href") === `#${visible.target.id}`;
        link.classList.toggle("active", active);
        if (active) link.setAttribute("aria-current", "true");
        else link.removeAttribute("aria-current");
      });
    }, {
      rootMargin: "-20% 0px -65% 0px",
      threshold: [0.01, 0.25, 0.5]
    });

    sections.forEach(section => observer.observe(section));
  }

  // Share links
  const pageUrl = window.location.href;
  const pageTitle = document.title;

  const xLink = document.querySelector('[data-share="x"]');
  const linkedinLink = document.querySelector('[data-share="linkedin"]');
  const copyButton = document.querySelector('[data-share="copy"]');

  if (xLink) {
    xLink.href = `https://twitter.com/intent/tweet?url=${encodeURIComponent(pageUrl)}&text=${encodeURIComponent(pageTitle)}`;
  }

  if (linkedinLink) {
    linkedinLink.href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(pageUrl)}`;
  }

  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      const original = copyButton.textContent;

      try {
        await navigator.clipboard.writeText(pageUrl);
        copyButton.textContent = "Copied";
      } catch {
        const helper = document.createElement("textarea");
        helper.value = pageUrl;
        helper.setAttribute("readonly", "");
        helper.style.position = "fixed";
        helper.style.opacity = "0";
        document.body.appendChild(helper);
        helper.select();
        document.execCommand("copy");
        helper.remove();
        copyButton.textContent = "Copied";
      }

      window.setTimeout(() => {
        copyButton.textContent = original;
      }, 1600);
    });
  }

  // Add safe attributes to external links inside the article
  document.querySelectorAll('.article-content a[href^="http"]').forEach(link => {
    try {
      const url = new URL(link.href);
      if (url.hostname !== window.location.hostname) {
        link.setAttribute("rel", "noopener noreferrer");
      }
    } catch (_) {}
  });
})();
