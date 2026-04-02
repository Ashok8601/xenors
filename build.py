import os
import shutil

# Ye line script ki current location (Root) nikal legi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ab saare paths absolute honge
SRC_DIR = os.path.join(BASE_DIR, 'src')
DIST_DIR = os.path.join(BASE_DIR, 'dist')
COMPONENTS_DIR = os.path.join(BASE_DIR, 'components')

def build_site():
    print(f"📂 Starting build from: {BASE_DIR}")

    # 1. Purana dist folder saaf karo aur naya banao
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)
    print(f"🧹 Cleaned and created {DIST_DIR}")

    # 2. Header aur Footer load karo (Absolute Path se)
    header_path = os.path.join(COMPONENTS_DIR, 'header.html')
    footer_path = os.path.join(COMPONENTS_DIR, 'footer.html')

    try:
        with open(header_path, 'r', encoding='utf-8') as f:
            header = f.read()
        with open(footer_path, 'r', encoding='utf-8') as f:
            footer = f.read()
    except FileNotFoundError as e:
        print(f"❌ Error: Header ya Footer file nahi mili! {e}")
        return

    # 3. SRC folder ki saari files scan karo
    if not os.path.exists(SRC_DIR):
        print(f"❌ Error: {SRC_DIR} folder hi nahi mila!")
        return

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
                print(f"✔️  Merged: {os.path.relpath(src_file, SRC_DIR)}")
            else:
                # Baki files (CSS, JS, Images) ko copy karo
                shutil.copy2(src_file, dist_file)
                print(f"📁 Copied: {os.path.relpath(src_file, SRC_DIR)}")

if __name__ == "__main__":
    build_site()
    print(f"\n🚀 Build Complete! Check your '{DIST_DIR}' folder.")
    
