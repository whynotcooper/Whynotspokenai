import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# 全局标志
_font_registered = False
_chinese_styles = None

def _register_chinese_font():
    """注册中文字体（使用Windows黑体）"""
    global _font_registered, _chinese_styles
    
    if _font_registered:
        return _chinese_styles
    
    # Windows 系统字体路径
    windows_font_paths = [
        'C:/Windows/Fonts/simhei.ttf',      # 黑体
        'C:/Windows/Fonts/simsun.ttc',      # 宋体
        'C:/Windows/Fonts/simkai.ttf',      # 楷体
        'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
        'C:/Windows/Fonts/msyhbd.ttc',      # 微软雅黑粗体
    ]
    
    font_path = None
    font_name = 'SimHei'  # 字体名称
    
    # 查找可用的字体文件
    for path in windows_font_paths:
        if os.path.exists(path):
            font_path = path
            print(f"找到字体文件: {path}")
            break
    
    if not font_path:
        raise FileNotFoundError("未找到Windows系统中的中文字体文件")
    
    try:
        # 注册字体
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        print(f"成功注册字体: {font_name}")
    except Exception as e:
        raise Exception(f"字体注册失败: {e}")
    
    # 获取基础样式表
    styles = getSampleStyleSheet()
    
    # 创建中文样式
    chinese_styles = {
        'ChineseNormal': ParagraphStyle(
            name='ChineseNormal',
            fontName=font_name,
            fontSize=12,
            leading=18,  # 行高
            spaceAfter=8,
            firstLineIndent=24  # 首行缩进
        ),
        'ChineseHeading': ParagraphStyle(
            name='ChineseHeading',
            fontName=font_name,
            fontSize=16,
            leading=22,
            spaceAfter=12,
            spaceBefore=12,
            textColor='#333333'
        ),
        'ChineseTitle': ParagraphStyle(
            name='ChineseTitle',
            fontName=font_name,
            fontSize=20,
            leading=26,
            spaceAfter=18,
            spaceBefore=18,
            alignment=1,  # 居中
            textColor='#000000'
        ),
        'ChineseSmall': ParagraphStyle(
            name='ChineseSmall',
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
    }
    
    # 将样式添加到样式表
    for style_name, style in chinese_styles.items():
        styles.add(style)
    
    _font_registered = True
    _chinese_styles = chinese_styles
    
    print("中文字体样式注册完成!")
    return chinese_styles

def get_chinese_style(style_name='ChineseNormal'):
    """获取中文字体样式"""
    styles = _register_chinese_font()
    return styles.get(style_name, styles['ChineseNormal'])

def create_test_pdf():
    """创建测试PDF文档"""
    
    # 注册字体
    styles = _register_chinese_font()
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        "chinese_test.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # 内容列表
    story = []
    
    # 标题
    story.append(Paragraph("中文PDF测试文档", styles['ChineseTitle']))
    story.append(Spacer(1, 0.3*inch))
    
    # 副标题
    story.append(Paragraph("使用Windows黑体显示中文", styles['ChineseHeading']))
    story.append(Spacer(1, 0.2*inch))
    
    # 正常段落
    story.append(Paragraph("这是一个测试段落，用于验证中文字体在PDF中的显示效果。", styles['ChineseNormal']))
    story.append(Paragraph("如果一切正常，您应该能够清晰地看到这些中文字符。", styles['ChineseNormal']))
    story.append(Spacer(1, 0.1*inch))
    
    # 长文本测试
    long_text = """
    这是一段较长的中文文本，用于测试换行和段落显示效果。
    报告生成器应该能够正确处理中文的换行和排版。
    我们可以在这里添加更多的中文内容来测试显示效果，包括标点符号：，。！？等。
    """
    story.append(Paragraph(long_text, styles['ChineseNormal']))
    story.append(Spacer(1, 0.2*inch))
    
    # 特殊字符测试
    story.append(Paragraph("特殊字符测试：", styles['ChineseHeading']))
    special_chars = """
    数字：1234567890
    英文：ABCDEFG abcdefg
    标点：，。！？；："'（）【】《》
    混合：Hello 世界！123 ABC
    """
    story.append(Paragraph(special_chars, styles['ChineseNormal']))
    story.append(Spacer(1, 0.2*inch))
    
    # 不同样式测试
    story.append(Paragraph("小号字体测试", styles['ChineseSmall']))
    story.append(Paragraph("这是一段使用小号字体显示的中文文本。", styles['ChineseSmall']))
    
    # 构建PDF
    try:
        doc.build(story)
        print("PDF生成成功: chinese_test.pdf")
        return True
    except Exception as e:
        print(f"PDF生成失败: {e}")
        return False

def test_font_registration():
    """测试字体注册"""
    print("开始测试中文字体注册...")
    
    try:
        # 测试字体注册
        styles = _register_chinese_font()
        print("✓ 字体注册测试通过")
        
        # 测试样式获取
        normal_style = get_chinese_style('ChineseNormal')
        heading_style = get_chinese_style('ChineseHeading')
        print("✓ 样式获取测试通过")
        
        # 测试字体名称
        if normal_style.fontName == 'SimHei':
            print("✓ 字体名称测试通过")
        else:
            print("✗ 字体名称测试失败")
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("中文字体注册测试")
    print("=" * 50)
    
    # 运行测试
    if test_font_registration():
        print("\n开始生成测试PDF...")
        if create_test_pdf():
            print("\n所有测试完成！请查看生成的 chinese_test.pdf 文件。")
        else:
            print("\nPDF生成失败！")
    else:
        print("\n字体注册测试失败！")