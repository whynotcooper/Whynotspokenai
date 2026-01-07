# import_task4_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhynotEnglish.settings')
django.setup()

from spoken_ai.models import TaskCategory, Task4Model  # 注意：改为 Task4Model


def read_file_safe(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""


def find_audio_file(folder_path):
    """查找 audio.m4a 或 audio.mp3，返回路径和扩展名"""
    for ext in ['.m4a', '.mp3']:
        audio_path = os.path.join(folder_path, f"audio{ext}")
        if os.path.exists(audio_path):
            return audio_path, ext
    return None, None


def import_tasks():
    # 类别名称改为 task4_tasks
    category, _ = TaskCategory.objects.get_or_create(
        name="task4_tasks"
    )
    print(f"📁 使用类别: {category.name}")

    # 假设 Task4 数据也在 TPO55–TPO75 范围内（按你的需求调整）
    for i in range(55, 76):
        folder_name = f"TPO{i}"
        folder_path = os.path.join(os.path.dirname(__file__), 'data', 'task4', folder_name)  # 注意：路径是 task4

        if not os.path.exists(folder_path):
            print(f"⚠️  文件夹不存在: {folder_path}")
            continue

        task_id = i - 54
        task_name = f"TPO{task_id} 口语 Task4"

        # 避免重复导入
        existing_task = Task4Model.objects.filter(name=task_name).first()
        if existing_task:
            print(f"⏭️  跳过已存在任务: {task_name}")
            continue

        # 读取文本文件（注意：没有 Reading.txt！）
        listening_text = read_file_safe(os.path.join(folder_path, "listening.txt"))
        question_text = read_file_safe(os.path.join(folder_path, "question.txt"))
        answertext1 = read_file_safe(os.path.join(folder_path, "answer1.txt"))
        answertext2 = read_file_safe(os.path.join(folder_path, "answer2.txt"))
        reasontext = read_file_safe(os.path.join(folder_path, "reasoning.txt"))

        # 查找音频
        audio_path, ext = find_audio_file(folder_path)
        if not audio_path:
            print(f"❌ 未找到 audio.m4a 或 audio.mp3: {folder_path}")
            continue

        # 创建 Task4 任务（无 readingtext）
        obj = Task4Model(
            name=task_name,
            listeningtext=listening_text,
            questiontext=question_text,
            answertext1=answertext1,
            answertext2=answertext2,
            reasontext=reasontext,
            category=category
        )
        obj.save()

        # 保存音频文件
        with open(audio_path, 'rb') as audio_file:
            obj.audio.save(f'tpo{i}_audio{ext}', audio_file, save=True)

        print(f"✅ 已导入: {task_name} ({ext})")

    print("\n🎉 Task4 数据导入完成！")


if __name__ == '__main__':
    import_tasks()