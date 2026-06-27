import shutil
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'


def inject_header(content, header):
    has_header = "<header" in content or "<site-header" in content

    if has_header:
        print("⚠ Header already exists, skipping injection.")
        return content

    body_index = content.find("<body")

    if body_index != -1:
        body_tag_end = content.find(">", body_index) + 1

        content = (
            content[:body_tag_end]
            + "\n"
            + header
            + "\n"
            + content[body_tag_end:]
        )
    else:
        print("⚠ No <body> tag found.")

    return content


def inject_footer(content, read_also, footer):
    has_footer = "<footer" in content
    has_read_also = 'class="read-also"' in content

    inject_block = ""

    if not has_read_also:
        inject_block += "\n" + read_also

    if not has_footer:
        inject_block += "\n" + footer

    body_close = content.rfind("</body>")

    if body_close != -1:
        content = (
            content[:body_close]
            + inject_block
            + "\n"
            + content[body_close:]
        )
    else:
        content += inject_block

    return content


def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # Clean dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy assets
    assets_to_copy = ['header.css', 'footer.css', 'header.js']

    for asset in assets_to_copy:
        src = COMPONENTS_DIR / asset

        if src.exists():
            dst = DIST_DIR / 'components' / asset
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"🎨 Asset Copied: components/{asset}")

    # Load components
    header_file = COMPONENTS_DIR / 'header.html'
    footer_file = COMPONENTS_DIR / 'footer.html'
    read_also_file = COMPONENTS_DIR / 'read-also.html'

    header = header_file.read_text(encoding='utf-8') if header_file.exists() else ""
    footer = footer_file.read_text(encoding='utf-8') if footer_file.exists() else ""
    read_also = read_also_file.read_text(encoding='utf-8') if read_also_file.exists() else ""

    # Config
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    STORY_DIRS = {'Web-Stories'}
    SKIP_FILES = {'build.py', 'requirements.txt', 'README.md', '.gitignore'}

    # Traverse
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

        is_web_story = any(part in STORY_DIRS for part in item.parts)

        # Process HTML
        if item.suffix == '.html' and not is_web_story:
            content = item.read_text(encoding='utf-8')

            content = inject_header(content, header)
            content = inject_footer(content, read_also, footer)

            dest_path.write_text(content, encoding='utf-8')

            print(f"🔥 Processed HTML: {relative_path}")

        else:
            shutil.copy2(item, dest_path)

            status = "📖 Story Copied" if is_web_story else "📁 Copied"
            print(f"{status}: {relative_path}")

    print("\n🚀 Build Complete!")


if __name__ == "__main__":
    build_site()
