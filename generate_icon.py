"""生成樱花风格的favicon.ico"""
from PIL import Image, ImageDraw
import math

def create_sakura_icon(size=256):
    """创建樱花图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size // 2, size // 2
    
    # 樱花颜色
    petal_color = (232, 154, 190, 255)  # 柔和粉色 #e89abe
    petal_dark = (212, 122, 158, 255)   # 深粉色 #d47a9e
    center_color = (255, 220, 100, 255)  # 花蕊黄色
    
    # 绘制5片花瓣
    petal_length = size * 0.38
    petal_width = size * 0.28
    
    for i in range(5):
        angle = math.radians(i * 72 - 90)  # 每片花瓣相隔72度
        
        # 花瓣中心点
        px = center_x + math.cos(angle) * petal_length * 0.45
        py = center_y + math.sin(angle) * petal_length * 0.45
        
        # 绘制花瓣（椭圆形）
        petal_bbox = [
            px - petal_width / 2,
            py - petal_length / 2,
            px + petal_width / 2,
            py + petal_length / 2
        ]
        
        # 旋转花瓣 - 使用多边形近似椭圆
        points = []
        for j in range(36):
            a = math.radians(j * 10)
            # 椭圆参数
            ex = (petal_width / 2) * math.cos(a)
            ey = (petal_length / 2) * math.sin(a)
            
            # 旋转
            rx = ex * math.cos(angle) - ey * math.sin(angle)
            ry = ex * math.sin(angle) + ey * math.cos(angle)
            
            points.append((px + rx, py + ry))
        
        draw.polygon(points, fill=petal_color, outline=petal_dark)
        
        # 花瓣上的V形缺口（樱花特征）
        notch_depth = petal_length * 0.15
        notch_x = center_x + math.cos(angle) * (petal_length * 0.85)
        notch_y = center_y + math.sin(angle) * (petal_length * 0.85)
        
        # V形缺口
        v_size = size * 0.06
        perp_angle = angle + math.pi / 2
        v_points = [
            (notch_x + math.cos(perp_angle) * v_size, notch_y + math.sin(perp_angle) * v_size),
            (notch_x + math.cos(angle) * v_size * 1.5, notch_y + math.sin(angle) * v_size * 1.5),
            (notch_x - math.cos(perp_angle) * v_size, notch_y - math.sin(perp_angle) * v_size),
        ]
        draw.polygon(v_points, fill=(0, 0, 0, 0))
    
    # 绘制花蕊（中心的小圆点）
    center_radius = size * 0.12
    draw.ellipse([
        center_x - center_radius,
        center_y - center_radius,
        center_x + center_radius,
        center_y + center_radius
    ], fill=center_color, outline=(255, 200, 80, 255))
    
    # 花蕊中的小点
    for i in range(5):
        angle = math.radians(i * 72 + 36)
        dot_x = center_x + math.cos(angle) * center_radius * 0.5
        dot_y = center_y + math.sin(angle) * center_radius * 0.5
        dot_r = size * 0.02
        draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], 
                     fill=(255, 180, 60, 255))
    
    return img

def main():
    # 生成高清图标
    icon_large = create_sakura_icon(256)
    
    # 生成多尺寸ico文件
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    
    for size in sizes:
        resized = icon_large.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # 保存为ico文件
    icon_path = 'static/favicon.ico'
    import os
    os.makedirs('static', exist_ok=True)
    
    icons[0].save(icon_path, format='ICO', sizes=[(s[0], s[1]) for s in sizes], 
                  append_images=icons[1:])
    
    # 同时保存PNG版本
    icon_large.save('static/favicon.png', format='PNG')
    
    print(f"✅ 图标已生成:")
    print(f"   - static/favicon.ico (多尺寸ICO)")
    print(f"   - static/favicon.png (256x256 PNG)")

if __name__ == '__main__':
    main()

