"""生成 Tauri 所需的各种尺寸图标"""
from PIL import Image, ImageDraw
import math
import os

def create_sakura_icon(size=256):
    """创建樱花图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size // 2, size // 2
    
    # 樱花颜色
    petal_color = (232, 154, 190, 255)
    petal_dark = (212, 122, 158, 255)
    center_color = (255, 220, 100, 255)
    
    petal_length = size * 0.38
    petal_width = size * 0.28
    
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        px = center_x + math.cos(angle) * petal_length * 0.45
        py = center_y + math.sin(angle) * petal_length * 0.45
        
        points = []
        for j in range(36):
            a = math.radians(j * 10)
            ex = (petal_width / 2) * math.cos(a)
            ey = (petal_length / 2) * math.sin(a)
            rx = ex * math.cos(angle) - ey * math.sin(angle)
            ry = ex * math.sin(angle) + ey * math.cos(angle)
            points.append((px + rx, py + ry))
        
        draw.polygon(points, fill=petal_color, outline=petal_dark)
        
        notch_depth = petal_length * 0.15
        notch_x = center_x + math.cos(angle) * (petal_length * 0.85)
        notch_y = center_y + math.sin(angle) * (petal_length * 0.85)
        
        v_size = size * 0.06
        perp_angle = angle + math.pi / 2
        v_points = [
            (notch_x + math.cos(perp_angle) * v_size, notch_y + math.sin(perp_angle) * v_size),
            (notch_x + math.cos(angle) * v_size * 1.5, notch_y + math.sin(angle) * v_size * 1.5),
            (notch_x - math.cos(perp_angle) * v_size, notch_y - math.sin(perp_angle) * v_size),
        ]
        draw.polygon(v_points, fill=(0, 0, 0, 0))
    
    center_radius = size * 0.12
    draw.ellipse([
        center_x - center_radius,
        center_y - center_radius,
        center_x + center_radius,
        center_y + center_radius
    ], fill=center_color, outline=(255, 200, 80, 255))
    
    for i in range(5):
        angle = math.radians(i * 72 + 36)
        dot_x = center_x + math.cos(angle) * center_radius * 0.5
        dot_y = center_y + math.sin(angle) * center_radius * 0.5
        dot_r = size * 0.02
        draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], 
                     fill=(255, 180, 60, 255))
    
    return img

def main():
    # 创建图标目录
    icons_dir = 'src-tauri/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # 生成高清源图标
    icon_source = create_sakura_icon(1024)
    
    # Tauri 需要的图标尺寸
    # Windows: icon.ico (多尺寸)
    # macOS: icon.icns (通过 png 生成)
    # Linux: 各种 png 尺寸
    
    sizes = [32, 128, 256, 512]
    icons = []
    
    for size in sizes:
        resized = icon_source.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'{icons_dir}/{size}x{size}.png', format='PNG')
        icons.append(resized)
        print(f"✅ 已生成: {size}x{size}.png")
    
    # 生成额外的 @2x 版本 (macOS)
    for size in [128, 256]:
        resized = icon_source.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'{icons_dir}/{size}x{size}@2x.png', format='PNG')
        print(f"✅ 已生成: {size}x{size}@2x.png")
    
    # 生成 Windows ico
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = [icon_source.resize(s, Image.Resampling.LANCZOS) for s in ico_sizes]
    ico_images[0].save(f'{icons_dir}/icon.ico', format='ICO', 
                       sizes=ico_sizes, append_images=ico_images[1:])
    print(f"✅ 已生成: icon.ico")
    
    # 生成通用图标 (用于 Linux 等)
    icon_source.resize((512, 512), Image.Resampling.LANCZOS).save(f'{icons_dir}/icon.png', format='PNG')
    print(f"✅ 已生成: icon.png")
    
    # 生成 Square 图标 (Windows Store)
    for size in [30, 44, 71, 89, 107, 142, 150, 284, 310]:
        resized = icon_source.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'{icons_dir}/Square{size}x{size}Logo.png', format='PNG')
    print(f"✅ 已生成: Square*Logo.png (Windows Store)")
    
    # 生成 StoreLogo
    icon_source.resize((50, 50), Image.Resampling.LANCZOS).save(f'{icons_dir}/StoreLogo.png', format='PNG')
    print(f"✅ 已生成: StoreLogo.png")
    
    print(f"\n🎉 所有图标已生成到 {icons_dir}/ 目录")

if __name__ == '__main__':
    main()

