from django.shortcuts import render
# views.py
# spoken/views.py
import os, uuid, json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from spoken_ai.utils import VoiceProcessingPipeline  # 你已有的逻辑
from model import SenseVoiceSmall


# 上传目录
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'audio')
os.makedirs(UPLOAD_DIR, exist_ok=True)
pipeline = VoiceProcessingPipeline()
name='test1.mp3'
path = os.path.join(UPLOAD_DIR, name)
    # 调用你的业务逻辑
transcription = pipeline.process_audio_pipeline(path)
print(transcription)


