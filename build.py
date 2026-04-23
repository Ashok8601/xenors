import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'

def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # 1. Clean dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load core template
    layout = (BASE_DIR / "layout.html").read_text(encoding="utf-8")

    # 3. Load components
    head_common = (COMPONENTS_DIR / "head_common.html").read_text(encoding="utf-8") \
        if (COMPONENTS_DIR / "head_common.html").exists() else ""

    header = (COMPONENTS_DIR / "header.html").read_text(encoding="utf-8") \
        if (COMPONENTS_DIR / "header.html").exists() else ""

    footer = (COMPONENTS_DIR / "footer.html").read_text(encoding="utf-8") \
        if (COMPONENTS_DIR / "footer.html").exists() else ""

    read_also = (COMPONENTS_DIR / "read-also.html").read_text(encoding="utf-8") \
        if (COMPONENTS_DIR / "read-also.html").exists() else ""

    # 4. Skip config
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    SKIP_FILES = {'build.py', 'layout.html', 'README.md', '.gitignore'}

    # 5. Traverse
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

        # ✅ PROCESS HTML
        if item.suffix == '.html':

            raw = item.read_text(encoding='utf-8')

            # 🔥 Extract SEO dynamically
            def extract(tag, default=""):
                import re
                match = re.search(tag, raw, re.IGNORECASE)
                return match.group(1) if match else default

            title = extract(r'<title>(.*?)</title>', "Xenors")
            description = extract(r'<meta name="description" content="(.*?)"', "")
            keywords = extract(r'<meta name="keywords" content="(.*?)"', "")

            # 🔥 Extract BODY content only
            import re
            body_match = re.search(r'<body.*?>(.*?)</body>', raw, re.DOTALL | re.IGNORECASE)
            body_content = body_match.group(1) if body_match else raw

            # Inject read also
            body_content += read_also

            # 🔥 Build final page
            final = layout
            final = final.replace("{{HEAD_COMMON}}", head_common)
            final = final.replace("{{TITLE}}", title)
            final = final.replace("{{DESCRIPTION}}", description)
            final = final.replace("{{KEYWORDS}}", keywords)
            final = final.replace("{{HEADER}}", header)
            final = final.replace("{{FOOTER}}", footer)
            final = final.replace("{{CONTENT}}", body_content)
            final = final.replace("{{HEAD_EXTRA}}", "")

            dest_path.write_text(final, encoding="utf-8")

            print(f"🔥 Built: {relative_path}")

        else:
            shutil.copy2(item, dest_path)
            print(f"📁 Copied: {relative_path}")

    print("\n🚀 Build Complete (No duplicate head / SEO clean)")

if __name__ == "__main__":
    build_site()
