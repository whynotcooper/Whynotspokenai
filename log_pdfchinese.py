import os

# 获取项目根目录（即 manage.py 所在目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_font_registered = False

def _register_chinese_font():
    global _font_registered
    if _font_registered:
        print("[DEBUG] 字体已注册，跳过")
        return

    print("[DEBUG] 正在注册中文字体和样式...")
    font_path = os.path.join(PROJECT_ROOT, 'WhynotEnglish', 'font', 'NotoSansSC-Regular.ttf')
    print(f"[DEBUG] 字体路径: {font_path}")

    if not os.path.exists(font_path):
        print("[ERROR] 字体文件不存在！")
        return

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('NotoSansSC', font_path))

    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    
    # 添加样式
    styles.add(ParagraphStyle(name='chinesenormal', fontName='NotoSansSC', fontSize=11, leading=16, spaceAfter=6))
    styles.add(ParagraphStyle(name='chineseheading', fontName='NotoSansSC', fontSize=14, leading=18, spaceAfter=12, spaceBefore=12))
    
    _font_registered = True
    print("[DEBUG] chinesenormal 和 chineseheading 已添加！")
def test_font_and_styles():
    _register_chinese_font()
    
    # 打印已注册的字体
    from reportlab.pdfbase.pdfmetrics import _fonts
    print("✅ 已注册的字体:")
    for name in sorted(_fonts.keys()):
        print(f"  - {name}")
    
    # 打印可用的样式
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    print("\n✅ 可用的样式:")
    for name in sorted(styles.byName.keys()):
        print(f"  - {name}")

    
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    
    # ✅ 直接尝试获取，而不是看 keys()
    try:
        normal = styles['chinesenormal']
        print(f"✅ 成功获取 chinesenormal，字体: {normal.fontName}")
    except KeyError as e:
        print(f"❌ 获取 chinesenormal 失败: {e}")

    try:
        heading = styles['chineseheading']
        print(f"✅ 成功获取 chineseheading，字体: {heading.fontName}")
    except KeyError as e:
        print(f"❌ 获取 chineseheading 失败: {e}")

    # 顺便打印 byName 看看（可能还是不显示）
    print("\n[INFO] byName.keys() 内容（可能不完整）:")
    print(list(styles.byName.keys()))
test_font_and_styles()
