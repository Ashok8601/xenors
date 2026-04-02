import shutil
from pathlib import Path

# Base Directory (Jahan build.py hai)
BASE_DIR = Path(__file__).resolve().parent

# Settings
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'

def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # 1. Dist folder setup
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🧹 Cleaned and created {DIST_DIR}")

    # 2. Header/Footer Load
    header_file = COMPONENTS_DIR / 'header.html'
    footer_file = COMPONENTS_DIR / 'footer.html'

    if not header_file.exists() or not footer_file.exists():
        print(f"❌ Error: Header/Footer missing at {COMPONENTS_DIR}")
        return

    header = header_file.read_text(encoding='utf-8')
    footer = footer_file.read_text(encoding='utf-8')

    # 3. Directories to skip
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    SKIP_FILES = {'build.py', 'requirements.txt', 'README.md', '.gitignore'}

    # 4. Walk through files
    # Hum saari files iterate karenge jo BASE_DIR mein hain
    for item in BASE_DIR.rglob('*'):
        # Skip if item is inside any of the SKIP_DIRS
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        
        # Skip specific files
        if item.name in SKIP_FILES or item.name.startswith('.'):
            continue

        # Target path in dist folder
        relative_path = item.relative_to(BASE_DIR)
        dest_path = DIST_DIR / relative_path

        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if item.suffix == '.html':
                # Merge logic
                content = item.read_text(encoding='utf-8')
                dest_path.write_text(header + content + footer, encoding='utf-8')
                print(f"✔️ Merged: {relative_path}")
            else:
                # Copy other files (images, css, etc.)
                shutil.copy2(item, dest_path)
                print(f"📁 Copied: {relative_path}")

if __name__ == "__main__":
    try:
        build_site()
        print("\n🚀 Build Complete! Site is ready in 'dist' folder.")
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        
