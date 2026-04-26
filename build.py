import shutil
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'


def read_file(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract(pattern, text, default=""):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default


def extract_body(raw):
    """Safe body extractor"""
    if "<body" in raw.lower():
        match = re.search(r'<body[^>]*>(.*?)</body>', raw, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
    return raw


def clean_placeholders(html):
    """Remove any leftover {{ }}"""
    return re.sub(r"{{.*?}}", "", html)


def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # 1. Clean dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load layout
    layout = read_file(BASE_DIR / "layout.html")

    # 3. Load components
    head_common = read_file(COMPONENTS_DIR / "head_common.html")
    header = read_file(COMPONENTS_DIR / "header.html")
    footer = read_file(COMPONENTS_DIR / "footer.html")
    read_also = read_file(COMPONENTS_DIR / "read-also.html")

    # 4. Skip config
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    SKIP_FILES = {'build.py', 'layout.html', 'README.md', '.gitignore'}

    # 5. Traverse files
    for item in BASE_DIR.rglob('*'):

        if any(part in SKIP_DIRS for part in item.parts):
            continue

        if item.name in SKIP_FILES or item.name.startswith('.'):
            continue

        relative_path = item.relative_to(BASE_DIR)
        dest_path = DIST_DIR / relative_path

        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # ================= HTML PROCESS =================
        if item.suffix == '.html':

            raw = read_file(item)

            # 🔥 SEO extraction
            title = extract(r'<title>(.*?)</title>', raw, "Xenors")
            description = extract(r'<meta name="description" content="(.*?)"', raw)
            keywords = extract(r'<meta name="keywords" content="(.*?)"', raw)

            # 🔥 Body extraction (safe)
            body_content = extract_body(raw)

            # Inject Read Also
            body_content += read_also

            # 🔥 Build final page
            final = layout
            final = final.replace("{{HEAD_COMMON}}", head_common)
            final = final.replace("{{HEAD_EXTRA}}", "")
            final = final.replace("{{TITLE}}", title)
            final = final.replace("{{DESCRIPTION}}", description)
            final = final.replace("{{KEYWORDS}}", keywords)
            final = final.replace("{{HEADER}}", header)
            final = final.replace("{{FOOTER}}", footer)
            final = final.replace("{{CONTENT}}", body_content)

            # 💣 Remove leftover placeholders
            final = clean_placeholders(final)

            # Write output
            dest_path.write_text(final, encoding="utf-8")

            print(f"🔥 Built: {relative_path}")

        # ================= STATIC FILES =================
        else:
            shutil.copy2(item, dest_path)
            print(f"📁 Copied: {relative_path}")

    print("\n🚀 Build Complete — Clean, SEO-ready, No bugs!")


if __name__ == "__main__":
    build_site()
