from django.shortcuts import render
# views.py
# spoken/views.py
import os, uuid, json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from spoken_ai.utils import VoiceProcessingPipeline  # 你已有的逻辑
import subprocess
def index(request):
    return render(request, "index.html")

# 上传目录
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'audio')
os.makedirs(UPLOAD_DIR, exist_ok=True)
pipeline = VoiceProcessingPipeline()

@csrf_exempt
# views.py


def process_audio(request):
    """
    接收前端录音 → 转码 → 调用 pipeline → 返回 {transcription}
    支持任意浏览器录音格式（webm/m4a/mp3...）
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio uploaded'}, status=400)

    # 原始文件（保留扩展名）
    original_ext = os.path.splitext(audio_file.name)[1] or '.webm'
    tmp_name = f"{uuid.uuid4().hex}{original_ext}"
    tmp_path = os.path.join(UPLOAD_DIR, tmp_name)

    # 转码后的固定 WAV 名
    wav_name = f"{uuid.uuid4().hex}.wav"
    wav_path = os.path.join(UPLOAD_DIR, wav_name)

    try:
        # 1. 保存上传文件
        with open(tmp_path, 'wb+') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        # 2. 统一转码：16 kHz、单声道、16-bit PCM
        subprocess.run([
            'ffmpeg', '-y',
            '-i', tmp_path,
            '-ar', '16000',
            '-ac', '1',
            '-sample_fmt', 's16',
            wav_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 3. 调用业务逻辑（用转码后的 WAV）
        transcription = pipeline.process_audio_pipeline(wav_path)

        return JsonResponse({'transcription': transcription})

    except subprocess.CalledProcessError as e:
        # ffmpeg 转码失败
        return JsonResponse({'error': f'FFmpeg error: {e.stderr.decode()}'}, status=500)
    except Exception as e:
        # 其他异常
        return JsonResponse({'error': str(e)}, status=500)

    finally:
        # 4. 清理两个临时文件
        print('111')
def spoken_ai(request):
    return render(request, "spoken_ai.html")
# spoken/views.py
from datetime import datetime
from reportlab.pdfgen import canvas   # pip install reportlab

