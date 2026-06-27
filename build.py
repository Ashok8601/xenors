import shutil
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'


def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # ==========================================
    # 1. Clean dist folder
    # ==========================================
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # 2. Copy component CSS/JS assets
    # ==========================================
    assets_to_copy = ['header.css', 'footer.css', 'header.js']

    for asset in assets_to_copy:
        src = COMPONENTS_DIR / asset

        if src.exists():
            dst = DIST_DIR / 'components' / asset
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"🎨 Asset Copied: components/{asset}")

    # ==========================================
    # 3. Load HTML Components
    # ==========================================
    header_file = COMPONENTS_DIR / 'header.html'
    footer_file = COMPONENTS_DIR / 'footer.html'
    read_also_file = COMPONENTS_DIR / 'read-also.html'

    header = header_file.read_text(encoding='utf-8') if header_file.exists() else ""
    footer = footer_file.read_text(encoding='utf-8') if footer_file.exists() else ""
    read_also = read_also_file.read_text(encoding='utf-8') if read_also_file.exists() else ""

    # ==========================================
    # 4. Skip Config
    # ==========================================
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    STORY_DIRS = {'Web-Stories'}
    SKIP_FILES = {'build.py', 'requirements.txt', 'README.md', '.gitignore'}

    # ==========================================
    # 5. Traverse all files
    # ==========================================
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

        # ==========================================
        # 6. Process HTML
        # ==========================================
        if item.suffix == '.html' and not is_web_story:
            content = item.read_text(encoding='utf-8')

            # Inject header after <body>
            if "<body>" in content:
                content = content.replace("<body>", f"<body>\n{header}", 1)
            else:
                print(f"⚠ No <body> tag in {relative_path}")

            # Inject read_also + footer before </body>
            if "</body>" in content:
                content = content.replace(
                    "</body>",
                    f"\n{read_also}\n{footer}\n</body>",
                    1
                )
            else:
                content += f"\n{read_also}\n{footer}"

            dest_path.write_text(content, encoding='utf-8')
            print(f"🔥 Processed HTML: {relative_path}")

        else:
            shutil.copy2(item, dest_path)
            status = "📖 Story Copied" if is_web_story else "📁 Copied"
            print(f"{status}: {relative_path}")

    print("\n🚀 Build Complete!")


if __name__ == "__main__":
    build_site()
