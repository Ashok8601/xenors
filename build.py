import os
import shutil

# Root directory nikalne ka sahi tarika
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Settings
DIST_DIR = os.path.join(BASE_DIR, 'dist')
COMPONENTS_DIR = os.path.join(BASE_DIR, 'components')

def build_site():
    print(f"📂 Starting build from: {BASE_DIR}")

    # 1. Purana dist folder saaf karo aur naya banao
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)

    # 2. Header aur Footer load karo
    header_path = os.path.join(COMPONENTS_DIR, 'header.html')
    footer_path = os.path.join(COMPONENTS_DIR, 'footer.html')

    if not os.path.exists(header_path):
        print(f"❌ Error: {header_path} nahi mili!")
        return

    with open(header_path, 'r', encoding='utf-8') as f:
        header = f.read()
    with open(footer_path, 'r', encoding='utf-8') as f:
        footer = f.read()

    # 3. Root ki saari files scan karo
    # Hum BASE_DIR ko hi scan karenge lekin kuch folders ko skip karenge
    SKIP_DIRS = ['dist', 'components', 'scripts', 'styles', '.git', '.github', '__pycache__']
    SKIP_FILES = ['build.py', 'requirements.txt', 'README.md', '.gitignore']

    for root, dirs, files in os.walk(BASE_DIR):
        # Skip unnecessary folders
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        # Current path relative to BASE_DIR
        relative_path = os.relpath(root, BASE_DIR)
        
        # Destination folder path
        if relative_path == ".":
            dest_path = DIST_DIR
        else:
            dest_path = os.path.join(DIST_DIR, relative_path)

        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for file in files:
            if file in SKIP_FILES or file.startswith('.'):
                continue
            
            src_file = os.path.join(root, file)
            dist_file = os.path.join(dest_path, file)

            if file.endswith('.html'):
                # Header + Content + Footer merge karo
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                with open(dist_file, 'w', encoding='utf-8') as f:
                    f.write(header + content + footer)
                print(f"✔️  Merged: {os.path.relpath(src_file, BASE_DIR)}")
            else:
                # Baaki files (images, favicon etc.) ko copy karo
                shutil.copy2(src_file, dist_file)
                print(f"📁 Copied: {os.path.relpath(src_file, BASE_DIR)}")

if __name__ == "__main__":
    build_site()
    print(f"\n🚀 Build Complete! Files are ready in the 'dist' folder.")
    
