"""
生成 LoArchive 应用图标
简洁风格：书籍图标
"""

from PIL import Image, ImageDraw
import os

def create_loarchive_icon(size):
    """创建 LoArchive 图标 - 书籍风格"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 渐变背景（青蓝色）
    for y in range(size):
        ratio = y / size
        g = int(188 * (1 - ratio) + 155 * ratio)
        b = int(212 * (1 - ratio) + 185 * ratio)
        draw.line([(0, y), (size, y)], fill=(0, g, b, 255))
    
    white = (255, 255, 255, 255)
    
    # 参数
    pad = size * 0.22
    
    # 书籍区域
    book_left = pad
    book_top = pad * 0.75
    book_right = size - pad
    book_bottom = size - pad * 0.75
    book_w = book_right - book_left
    book_h = book_bottom - book_top
    
    # 书脊宽度
    spine = book_w * 0.15
    
    # 绘制书籍（填充）
    # 书脊（左侧圆角矩形）
    spine_radius = spine * 0.6
    draw.rounded_rectangle(
        [book_left, book_top, book_left + spine * 1.5, book_bottom],
        radius=spine_radius,
        fill=white
    )
    
    # 书页（右侧矩形）
    draw.rectangle(
        [book_left + spine, book_top, book_right, book_bottom],
        fill=white
    )
    
    # 书页分隔线（浅色）
    line_color = (0, 170, 195, 255)
    page_gap = book_h * 0.12
    
    # 顶部页线
    draw.rectangle(
        [book_left + spine + book_w * 0.08, book_bottom - page_gap * 2,
         book_right - book_w * 0.08, book_bottom - page_gap * 1.7],
        fill=line_color
    )
    
    # 底部页线
    draw.rectangle(
        [book_left + spine + book_w * 0.08, book_bottom - page_gap,
         book_right - book_w * 0.08, book_bottom - page_gap * 0.7],
        fill=line_color
    )
    
    return img


def generate_all_icons():
    """生成所有图标"""
    icons_dir = 'src-tauri/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    sizes = {
        '32x32.png': 32,
        '128x128.png': 128,
        '128x128@2x.png': 256,
        '256x256.png': 256,
        '256x256@2x.png': 512,
        '512x512.png': 512,
        'icon.png': 512,
        'Square30x30Logo.png': 30,
        'Square44x44Logo.png': 44,
        'Square71x71Logo.png': 71,
        'Square89x89Logo.png': 89,
        'Square107x107Logo.png': 107,
        'Square142x142Logo.png': 142,
        'Square150x150Logo.png': 150,
        'Square284x284Logo.png': 284,
        'Square310x310Logo.png': 310,
        'StoreLogo.png': 50,
    }
    
    for filename, size in sizes.items():
        icon = create_loarchive_icon(size)
        filepath = os.path.join(icons_dir, filename)
        icon.save(filepath, 'PNG')
        print(f'✅ {filepath}')
    
    # ICO
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_images = [create_loarchive_icon(s) for s in ico_sizes]
    ico_path = os.path.join(icons_dir, 'icon.ico')
    ico_images[0].save(ico_path, format='ICO', 
                       sizes=[(s, s) for s in ico_sizes],
                       append_images=ico_images[1:])
    print(f'✅ {ico_path}')
    
    # ICNS
    icns_path = os.path.join(icons_dir, 'icon.icns')
    create_loarchive_icon(512).save(icns_path, format='ICNS')
    print(f'✅ {icns_path}')
    
    # Static
    static_dir = 'static'
    os.makedirs(static_dir, exist_ok=True)
    
    create_loarchive_icon(256).save(os.path.join(static_dir, 'favicon.png'))
    print(f'✅ {static_dir}/favicon.png')
    
    fav_sizes = [16, 32, 48]
    fav_images = [create_loarchive_icon(s) for s in fav_sizes]
    fav_images[0].save(os.path.join(static_dir, 'favicon.ico'), format='ICO',
                       sizes=[(s, s) for s in fav_sizes],
                       append_images=fav_images[1:])
    print(f'✅ {static_dir}/favicon.ico')
    
    print('\n🎉 图标生成完成！')


if __name__ == '__main__':
    generate_all_icons()
