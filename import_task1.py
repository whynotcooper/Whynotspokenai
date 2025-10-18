# import_task1_data.py
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhynotEnglish.settings')  # 👈 替换为你的项目名
django.setup()

from spoken_ai.models import TaskCategory, Task1Model  # 👈 替换为你的 app 名

# 数据根目录（根据你的路径调整）
DATA_ROOT = os.path.join(os.path.dirname(__file__), 'data', 'task1')

def read_file_safe(filepath):
    """安全读取文件内容，若文件不存在返回空字符串"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""

def import_tasks():
    # 1. 获取或创建类别
    category, created = TaskCategory.objects.get_or_create(
        name="task1_tasks"
    )
    print(f"📁 使用类别: {category.name} (ID: {category.id})")

    # 2. 遍历 TPO1 到 TPO75（你可以按实际范围调整）
    for i in range(55, 76):  # 1 ~ 75
        folder_name = f"TPO{i}"
        folder_path = os.path.join(DATA_ROOT, folder_name)

        if not os.path.exists(folder_path):
            print(f"⚠️  文件夹不存在: {folder_path}")
            continue

        # 读取四个文件
        reading_path = os.path.join(folder_path, "Reading.txt")
        answer1_path = os.path.join(folder_path, "answer1.txt")
        answer2_path = os.path.join(folder_path, "answer2.txt")
        reason_path = os.path.join(folder_path, "reasoning.txt")

        reading_text = read_file_safe(reading_path)
        answertext1 = read_file_safe(answer1_path)
        answertext2 = read_file_safe(answer2_path)
        reasontext = read_file_safe(reason_path)
        id=i-54
        # 构造任务名称
        task_name = f"TPO{id} 口语 Task1"
        print(f"📝 正在处理: {task_name}")

        # 创建或更新 Task1Model
        obj, created = Task1Model.objects.update_or_create(
            name=task_name,
            defaults={
                'readingtext': reading_text,
                'answertext1': answertext1,
                'answertext2': answertext2,
                'reasontext': reasontext,
                'category': category
            }
        )

        if created:
            print(f"✅ 已创建: {task_name}")
        else:
            print(f"🔄 已更新: {task_name}")

    print("\n🎉 导入完成！")

if __name__ == '__main__':
    import_tasks()