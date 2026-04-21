import os
import shutil

# Create folders
os.makedirs("collector", exist_ok=True)
os.makedirs("analysis", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Create __init__.py files
open("collector/__init__.py", "a").close()
open("analysis/__init__.py", "a").close()

# Move files (if they exist)
moves = {
    "data_loader.py": "analysis/data_loader.py"   # ✅ ADD THIS
}


for src, dst in moves.items():
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {src} → {dst}")

print("✅ Project structure created successfully")