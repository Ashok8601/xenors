import shutil
import re
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'


def inject_header(content, header):
    # Regex jo <header...>...</header> aur <site-header...>...</site-header> dono ko target karega
    # re.DOTALL se ye multi-line headers ko bhi select kar lega
    header_pattern = re.compile(r'<(header|site-header).*?>.*?</\1>', re.DOTALL)
    
    # Agar pehle se koi header exists karta hai, toh use remove (blank) kar do
    if header_pattern.search(content):
        print("♻️ Old header found! Replacing it with the new component.")
        content = header_pattern.sub('', content)

    # Naya header inject karne ke liye <body> tag dhundhein
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
        print("⚠ No <body> tag found. Injecting header at the very top.")
        content = header + "\n" + content

    return content


def inject_footer(content, read_also, footer):
    # Safe Footer & Read Also Injection
    # Agar pehle se class="read-also" ya <footer> hai toh use clean ya replace kar sakte hain
    
    # Purane footer ko remove karne ka pattern
    footer_pattern = re.compile(r'<footer.*?>.*?</footer>', re.DOTALL)
    if footer_pattern.search(content):
        print("♻️ Old footer found! Replacing it.")
        content = footer_pattern.sub('', content)
        
    read_also_pattern = re.compile(r'<section class=["\']read-also["\'].*?>.*?</section>', re.DOTALL)
    if read_also_pattern.search(content):
        print("♻️ Old read-also section found! Replacing it.")
        content = read_also_pattern.sub('', content)

    inject_block = "\n" + read_also + "\n" + footer

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
    
