from PIL import Image

def remove_bg(input_path, output_ico_path):
    print(f"Opening {input_path}...")
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    # 黒除去の閾値 (0-255)
    # 真っ黒(0,0,0)だけでなく、圧縮ノイズ等の暗いグレーも除去するために少し幅を持たせる
    threshold = 40
    
    print("Processing pixels...")
    for item in datas:
        # RGB値がすべて閾値以下なら透明にする
        if item[0] <= threshold and item[1] <= threshold and item[2] <= threshold:
            new_data.append((0, 0, 0, 0)) # 完全透明
        else:
            new_data.append(item)

    img.putdata(new_data)
    
    # 境界のガタつきを軽減したければ縮小が有効だが、今回はそのままICO化
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(output_ico_path, format='ICO', sizes=icon_sizes)
    print(f"Successfully created transparent icon: {output_ico_path}")

try:
    src = r"g:\CODE\Antigravity\Py_FILE\112.png"
    dst = r"g:\CODE\Antigravity\Py_FILE\ChainFlowFiler_v11\app_icon.ico"
    remove_bg(src, dst)
except Exception as e:
    print(f"Error: {e}")
