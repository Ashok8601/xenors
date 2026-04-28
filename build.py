import shutil
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'


def read_file(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_between(text, start, end):
    try:
        return text.split(start)[1].split(end)[0].strip()
    except:
        return ""


def extract_head(raw):
    """Extract full head content"""
    match = re.search(r'<head[^>]*>(.*?)</head>', raw, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_body(raw):
    """Extract body content only"""
    match = re.search(r'<body[^>]*>(.*?)</body>', raw, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else raw


def clean_placeholders(html):
    return re.sub(r"{{.*?}}", "", html)


def build_site():

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    layout = read_file(BASE_DIR / "layout.html")

    head_common = read_file(COMPONENTS_DIR / "head_common.html")
    header = read_file(COMPONENTS_DIR / "header.html")
    footer = read_file(COMPONENTS_DIR / "footer.html")
    read_also = read_file(COMPONENTS_DIR / "read-also.html")

    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '__pycache__'}
    SKIP_FILES = {'build.py', 'layout.html'}

    for item in BASE_DIR.rglob('*'):

        if any(part in SKIP_DIRS for part in item.parts):
            continue

        if item.name in SKIP_FILES:
            continue

        dest_path = DIST_DIR / item.relative_to(BASE_DIR)

        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # ===== HTML BUILD =====
        if item.suffix == '.html':

            raw = read_file(item)

            # 🔥 Extract FULL HEAD
            page_head = extract_head(raw)

            # 🔥 Remove unwanted tags from head
            page_head = re.sub(r'<head[^>]*>|</head>', '', page_head, flags=re.IGNORECASE)
            page_head = re.sub(r'<html.*?>|</html>', '', page_head, flags=re.IGNORECASE)
            page_head = re.sub(r'<!DOCTYPE.*?>', '', page_head, flags=re.IGNORECASE)

            # 🔥 Extract BODY
            body_content = extract_body(raw)

            # Remove header/footer from body (important)
            body_content = re.sub(r'<header.*?>.*?</header>', '', body_content, flags=re.DOTALL)
            body_content = re.sub(r'<footer.*?>.*?</footer>', '', body_content, flags=re.DOTALL)

            # Inject Read Also
            body_content += read_also

            # 🔥 Build final
            final = layout
            final = final.replace("{{HEAD_COMMON}}", head_common)
            final = final.replace("{{PAGE_HEAD}}", page_head)
            final = final.replace("{{HEADER}}", header)
            final = final.replace("{{FOOTER}}", footer)
            final = final.replace("{{CONTENT}}", body_content)

            final = clean_placeholders(final)

            dest_path.write_text(final, encoding="utf-8")
            print(f"🔥 Built: {item}")

        else:
            shutil.copy2(item, dest_path)

    print("\n🚀 Build Complete — Perfect Output!")


if __name__ == "__main__":
    build_site()
