import re
import shutil
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
DIST_DIR = BASE_DIR / "dist"
COMPONENTS_DIR = BASE_DIR / "components"


def inject_header(content, header):
    # Remove old header/site-header if exists (Case-insensitive)
    header_pattern = re.compile(
        r"<(header|site-header).*?>.*?</\1>", re.DOTALL | re.IGNORECASE
    )

    if header_pattern.search(content):
        print("♻️ Old header found! Replacing it.")
        content = header_pattern.sub("", content)

    # Inject right after the opening <body> tag (handles attributes like <body class="...">)
    body_pattern = re.compile(r"(<body.*?>)", re.IGNORECASE)
    match = body_pattern.search(content)

    if match:
        end_pos = match.end()
        content = content[:end_pos] + "\n" + header + "\n" + content[end_pos:]
    else:
        print("⚠ No <body> tag found.")
        content = header + "\n" + content

    return content


def inject_footer(content, read_also, footer):
    # Remove old footer (Case-insensitive)
    footer_pattern = re.compile(r"<footer.*?>.*?</footer>", re.DOTALL | re.IGNORECASE)

    if footer_pattern.search(content):
        print("♻️ Old footer found! Replacing it.")
        content = footer_pattern.sub("", content)

    # Remove old Read Also (Case-insensitive)
    read_pattern = re.compile(
        r'<section class=["\']read-also["\'].*?>.*?</section>',
        re.DOTALL | re.IGNORECASE,
    )

    if read_pattern.search(content):
        print("♻️ Old read-also found! Replacing it.")
        content = read_pattern.sub("", content)

    inject_block = "\n" + read_also + "\n" + footer

    # Case-insensitive search for </body>
    body_close_pattern = re.compile(r"(</body>)", re.IGNORECASE)
    match = body_close_pattern.search(content)

    if match:
        start_pos = match.start()
        content = (
            content[:start_pos] + inject_block + "\n" + content[start_pos:]
        )
    else:
        content += inject_block

    return content


def inject_head_scripts(content):
    # 1. Strong Duplicate Check using Regex (Case-Insensitive)
    if re.search(
        r"googletagmanager\.com/gtag/js", content, re.IGNORECASE
    ) or re.search(
        r"pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js",
        content,
        re.IGNORECASE,
    ):
        return content

    # 2. Official GA4 Snippet + Admin (ignoreMe) Check Integrated
    head_scripts = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ZRZ11QPD5B"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

if (localStorage.getItem("ignoreMe") === "true") {
    console.log("Admin Mode: Google Analytics Disabled");
} else {
    gtag("config", "G-ZRZ11QPD5B", {
        page_title: document.title,
        page_location: window.location.href,
        page_path: window.location.pathname
    });
}
</script>

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7151523366810242" crossorigin="anonymous"></script>
"""

    # Head close tag ke pehle inject karna (Case-insensitive)
    head_close_pattern = re.compile(r"(</head>)", re.IGNORECASE)
    match = head_close_pattern.search(content)

    if match:
        start_pos = match.start()
        return content[:start_pos] + head_scripts + "\n" + content[start_pos:]

    return head_scripts + "\n" + content


def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # Config Dirs and Files to skip
    SKIP_DIRS = {
        "dist",
        "components",
        "scripts",
        "styles",
        ".git",
        ".github",
        "__pycache__",
    }
    STORY_DIRS = {"Web-Stories"}
    SKIP_FILES = {"build.py", "README.md", "requirements.txt", ".gitignore"}

    # Clean dist safely
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy component assets
    assets_to_copy = ["header.css", "footer.css", "header.js"]
    for asset in assets_to_copy:
        src = COMPONENTS_DIR / asset
        if src.exists():
            dst = DIST_DIR / "components" / asset
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"🎨 Asset Copied: components/{asset}")

    # Load Components
    header_file = COMPONENTS_DIR / "header.html"
    footer_file = COMPONENTS_DIR / "footer.html"
    read_also_file = COMPONENTS_DIR / "read-also.html"

    header = (
        header_file.read_text(encoding="utf-8") if header_file.exists() else ""
    )
    footer = (
        footer_file.read_text(encoding="utf-8") if footer_file.exists() else ""
    )
    read_also = (
        read_also_file.read_text(encoding="utf-8")
        if read_also_file.exists()
        else ""
    )

    # Traverse Files
    for item in BASE_DIR.rglob("*"):
        # Strict checking to skip unwanted directories and their children
        if any(part in SKIP_DIRS for part in item.parts):
            continue

        if item.name in SKIP_FILES or item.name.startswith("."):
            continue

        relative_path = item.relative_to(BASE_DIR)
        dest_path = DIST_DIR / relative_path

        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        is_web_story = any(part in STORY_DIRS for part in item.parts)

        # HTML Processing
        if item.suffix.lower() == ".html" and not is_web_story:
            content = item.read_text(encoding="utf-8")

            # Injections
            content = inject_head_scripts(content)
            content = inject_header(content, header)
            content = inject_footer(content, read_also, footer)

            dest_path.write_text(content, encoding="utf-8")
            print(f"🔥 Processed HTML: {relative_path}")
        else:
            shutil.copy2(item, dest_path)
            status = "📖 Story Copied" if is_web_story else "📁 Copied"
            print(f"{status}: {relative_path}")

    print("\n🚀 Build Complete!")
    print("✅ Header Injected")
    print("✅ Footer Injected")
    print("✅ Read Also Injected")
    print("✅ Google Analytics Injected")
    print("✅ Google AdSense Injected")


if __name__ == "__main__":
    build_site()
        
