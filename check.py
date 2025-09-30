import os
import matplotlib.font_manager as fm

def find_chinese_fonts():
    """查找系统中可用的中文字体"""
    chinese_fonts = []
    
    # Windows 字体路径
    windows_path = "C:/Windows/Fonts/"
    
    # macOS 字体路径
    mac_paths = [
        "/System/Library/Fonts/",
        "/Library/Fonts/",
        os.path.expanduser("~/Library/Fonts/")
    ]
    
    # Linux 字体路径
    linux_paths = [
        "/usr/share/fonts/",
        "/usr/local/share/fonts/",
        os.path.expanduser("~/.fonts/")
    ]
    
    # 根据系统选择路径
    if os.name == 'nt':  # Windows
        search_paths = [windows_path]
    elif os.name == 'posix':  # macOS/Linux
        if os.uname().sysname == 'Darwin':  # macOS
            search_paths = mac_paths
        else:  # Linux
            search_paths = linux_paths
    else:
        search_paths = []
    
    # 常见的中文字体文件名
    chinese_font_patterns = [
        'simhei', 'simsun', 'simkai', 'simfang',  # Windows 中文
        'pingfang', 'stheit', 'stsong',  # macOS 中文
        'noto', 'droid', 'wqy', 'sourcehansans',  # Linux 中文
        'msyh', 'microsoftyahei',  # 微软雅黑
        'arialuni',  # Arial Unicode MS
    ]
    
    # 搜索字体文件
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_lower = file.lower()
                    # 检查是否是字体文件且包含中文字体特征
                    if (file_lower.endswith(('.ttf', '.ttc', '.otf')) and
                        any(pattern in file_lower for pattern in chinese_font_patterns)):
                        full_path = os.path.join(root, file)
                        chinese_fonts.append({
                            'name': file,
                            'path': full_path,
                            'size': os.path.getsize(full_path)
                        })
    
    return chinese_fonts

# 使用示例
fonts = find_chinese_fonts()
if fonts:
    print("找到的中文字体:")
    for font in fonts:
        print(f"名称: {font['name']}, 路径: {font['path']}")
else:
    print("未找到中文字体")