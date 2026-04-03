import shutil
from pathlib import Path

# Base Directory
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

    # 2. Header/Footer Load
    header_file = COMPONENTS_DIR / 'header.html'
    footer_file = COMPONENTS_DIR / 'footer.html'
    
    header = header_file.read_text(encoding='utf-8') if header_file.exists() else ""
    footer = footer_file.read_text(encoding='utf-8') if footer_file.exists() else ""

    # 3. Directories to completely SKIP (No copy, no merge)
    SKIP_DIRS = {'dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__'}
    
    # 4. Directories for Web Stories (Only Copy, NO Merge)
    STORY_DIRS = {'Web-Stories'}
    
    SKIP_FILES = {'build.py', 'requirements.txt', 'README.md', '.gitignore'}

    for item in BASE_DIR.rglob('*'):
        # Purely skip internal build folders
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        
        if item.name in SKIP_FILES or item.name.startswith('.'):
            continue

        relative_path = item.relative_to(BASE_DIR)
        dest_path = DIST_DIR / relative_path

        if item.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file is inside a Web-Stories folder
            is_web_story = any(part in STORY_DIRS for part in item.parts)

            if item.suffix == '.html' and not is_web_story:
                # Normal HTML: Merge Header + Content + Footer
                content = item.read_text(encoding='utf-8')
                dest_path.write_text(header + content + footer, encoding='utf-8')
                print(f"✔️ Merged: {relative_path}")
            else:
                # Web Stories OR Assets (Images/JS/CSS): Just Copy
                shutil.copy2(item, dest_path)
                status = "📖 Story Copied" if is_web_story else "📁 Copied"
                print(f"{status}: {relative_path}")

if __name__ == "__main__":
    build_site()
    print("\n🚀 Build Complete! Web Stories are preserved without Header/Footer.")
    
