from PIL import Image
import os

src = r"d:\CODE\Antigravity\Py_FILE\111.png"
dst = r"d:\CODE\Antigravity\Py_FILE\ChainFlowFiler_v11\app_icon.ico"

try:
    img = Image.open(src)
    # create sizes for ico
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(dst, format='ICO', sizes=icon_sizes)
    print(f"Successfully converted {src} to {dst}")
except Exception as e:
    print(f"Error: {e}")
