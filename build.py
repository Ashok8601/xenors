import os
import shutil

# Root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Settings
DIST_DIR = os.path.join(BASE_DIR, 'dist')
COMPONENTS_DIR = os.path.join(BASE_DIR, 'components')

def build_site():
    print(f"📂 BASE_DIR: {BASE_DIR}")

    # 1. Dist folder setup
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)

    # 2. Header/Footer Load
    header_path = os.path.join(COMPONENTS_DIR, 'header.html')
    footer_path = os.path.join(COMPONENTS_DIR, 'footer.html')

    with open(header_path, 'r', encoding='utf-8') as f:
        header = f.read()
    with open(footer_path, 'r', encoding='utf-8') as f:
        footer = f.read()

    # 3. Walk through Root
    SKIP_DIRS = ['dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__']
    SKIP_FILES = ['build.py', 'requirements.txt', 'README.md', '.gitignore']

    for root, dirs, files in os.walk(BASE_DIR):
        # Skip folders logic
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        # Use os.path.relpath instead of os.relpath
        rel_path = os.path.path.relpath(root, BASE_DIR) if hasattr(os, 'path') else os.path.relpath(root, BASE_DIR)
        # Simplified version that is more robust:
        try:
            rel_path = os.path.path.relpath(root, BASE_DIR)
        except AttributeError:
            # Absolute fallback for some environments
            import os.path
            rel_path = os.path.path.relpath(root, BASE_DIR)
        
        dest_path = os.path.join(DIST_DIR, rel_path) if rel_path != "." else DIST_DIR

        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for file in files:
            if file in SKIP_FILES or file.startswith('.'):
                continue
            
            src_file = os.path.join(root, file)
            dist_file = os.path.join(dest_path, file)

            if file.endswith('.html'):
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(dist_file, 'w', encoding='utf-8') as f:
                    f.write(header + content + footer)
                print(f"✔️ Merged: {file}")
            else:
                shutil.copy2(src_file, dist_file)
                print(f"📁 Copied: {file}")

if __name__ == "__main__":
    build_site()
    print("\n🚀 Build Complete!")
        
