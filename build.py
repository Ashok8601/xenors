import shutil
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
DIST_DIR = BASE_DIR / 'dist'
COMPONENTS_DIR = BASE_DIR / 'components'

def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # 1. Clean dist folder
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load Components
    header_file = COMPONENTS_DIR / 'header.html'
    footer_file = COMPONENTS_DIR / 'footer.html'
    read_also_file = COMPONENTS_DIR / 'read-also.html'

    header = header_file.read_text(encoding='utf-8') if header_file.exists() else ""
    footer = footer_file.read_text(encoding='utf-8') if footer_file.exists() else ""
    read_also = read_also_file.read_text(encoding='utf-8') if read_also_file.exists() else ""

    # 3. Skip Config
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    STORY_DIRS = {'Web-Stories'}
    SKIP_FILES = {'build.py', 'requirements.txt', 'README.md', '.gitignore'}

    # 4. Traverse Files
    for item in BASE_DIR.rglob('*'):

        # Skip unwanted directories
        if any(part in SKIP_DIRS for part in item.parts):
            continue

        # Skip unwanted files
        if item.name in SKIP_FILES or item.name.startswith('.'):
            continue

        relative_path = item.relative_to(BASE_DIR)
        dest_path = DIST_DIR / relative_path

        # Create directories
        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        # Ensure parent exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Check Web Story
        is_web_story = any(part in STORY_DIRS for part in item.parts)

        # 5. HTML Processing
        if item.suffix == '.html' and not is_web_story:
            content = item.read_text(encoding='utf-8')

            # 👉 APPLY TO ALL HTML FILES
            final_content = header + content + read_also + footer

            print(f"🔥 Processed with Read Also: {relative_path}")

            dest_path.write_text(final_content, encoding='utf-8')

        else:
            # Copy assets & Web Stories
            shutil.copy2(item, dest_path)
            status = "📖 Story Copied" if is_web_story else "📁 Copied"
            print(f"{status}: {relative_path}")

    print("\n🚀 Build Complete! Read Also injected in ALL HTML files.")

# Run
if __name__ == "__main__":
    build_site()
