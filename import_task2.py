# import_task2_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhynotEnglish.settings')
django.setup()

from spoken_ai.models import TaskCategory, Task2Model

# 数据根目录
DATA_ROOT = os.path.join(os.path.dirname(__file__), 'data', 'task2')

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
    category, _ = TaskCategory.objects.get_or_create(
        name="task2_tasks"
    )
    print(f"📁 使用类别: {category.name}")

    for i in range(55, 76):
        folder_name = f"TPO{i}"
        folder_path = os.path.join(DATA_ROOT, folder_name)

        if not os.path.exists(folder_path):
            print(f"⚠️  文件夹不存在: {folder_path}")
            continue

        # 构造任务名（保持与之前一致）
        task_id = i - 54
        task_name = f"TPO{task_id} 口语 Task2"

        # 检查是否已存在（避免重复创建）
        existing_task = Task2Model.objects.filter(name=task_name).first()
        if existing_task:
            print(f"⏭️  跳过已存在任务: {task_name}")
            continue

        # 读取文本
        reading_text = read_file_safe(os.path.join(folder_path, "Reading.txt"))
        listening_text = read_file_safe(os.path.join(folder_path, "listening.txt"))
        question_text = read_file_safe(os.path.join(folder_path, "question.txt"))
        answertext1 = read_file_safe(os.path.join(folder_path, "answer1.txt"))
        answertext2 = read_file_safe(os.path.join(folder_path, "answer2.txt"))
        reasontext = read_file_safe(os.path.join(folder_path, "reasoning.txt"))

        # 查找音频文件（支持 .m4a 或 .mp3）
        audio_path, ext = find_audio_file(folder_path)
        if not audio_path:
            print(f"❌ 未找到 audio.m4a 或 audio.mp3: {folder_path}")
            continue

        # 创建新任务
        obj = Task2Model(
            name=task_name,
            readingtext=reading_text,
            listeningtext=listening_text,
            questiontext=question_text,
            answertext1=answertext1,
            answertext2=answertext2,
            reasontext=reasontext,
            category=category
        )
        obj.save()  # 先保存，才能上传文件

        # 上传音频
        with open(audio_path, 'rb') as audio_file:
            obj.audio.save(f'tpo{i}_audio{ext}', audio_file, save=True)

        print(f"✅ 已导入: {task_name} ({ext})")

    print("\n🎉 Task2 数据导入完成！")

if __name__ == '__main__':
    import_tasks()