
import os
import shutil

# Settings
SRC_DIR = 'src'
DIST_DIR = 'dist'
COMPONENTS_DIR = 'components'

def build_site():
    # 1. Purana dist folder saaf karo
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)

    # 2. Header aur Footer load karo
    with open(f'{COMPONENTS_DIR}/header.html', 'r', encoding='utf-8') as f:
        header = f.read()
    with open(f'{COMPONENTS_DIR}/footer.html', 'r', encoding='utf-8') as f:
        footer = f.read()

    # 3. Saari files ko scan karo
    for root, dirs, files in os.walk(SRC_DIR):
        # Path maintain rakho (Blog/ai/ etc.)
        relative_path = os.relpath(root, SRC_DIR)
        dest_path = os.path.join(DIST_DIR, relative_path)
        
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for file in files:
            src_file = os.path.join(root, file)
            dist_file = os.path.join(dest_path, file)

            if file.endswith('.html'):
                # Header + Content + Footer merge karo
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                with open(dist_file, 'w', encoding='utf-8') as f:
                    f.write(header + content + footer)
                print(f"✔️ Merged: {src_file}")
            else:
                # Baki files (CSS, JS, Images) ko bas copy karo
                shutil.copy2(src_file, dist_file)

if __name__ == "__main__":
    build_site()
    print("\n🚀 Build Complete! Now deploy the 'dist' folder.")
  
