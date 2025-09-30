from django.shortcuts import render
# views.py
# spoken/views.py
import os, uuid, json
from django.conf import settings

import subprocess
import json, os, tempfile, datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import  getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io


UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'audio')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_and_transcode(audio):
    """返回 (tmp_path, wav_path)"""
    if audio.size == 0:
        raise ValueError("上传的音频文件为空")

    ext = os.path.splitext(audio.name)[1] or ".webm"

    # 使用安全的临时文件
    with tempfile.NamedTemporaryFile(suffix=ext, dir=UPLOAD_DIR, delete=False) as tmp_f:
        for chunk in audio.chunks():
            tmp_f.write(chunk)
        tmp = tmp_f.name

    with tempfile.NamedTemporaryFile(suffix=".wav", dir=UPLOAD_DIR, delete=False) as wav_f:
        wav = wav_f.name

    # 调用 ffmpeg
    try:
        result = subprocess.run([
            "ffmpeg", "-y", "-i", tmp, "-vn", "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", wav
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("FFmpeg failed with stderr:")
            print(result.stderr)
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stderr)

    except FileNotFoundError:
        raise RuntimeError("ffmpeg 未找到，请确保已安装并加入系统 PATH")

    return tmp, wav

def _safe_remove(*paths):
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass
def index(request):
    return render(request, "index.html")





# 假设 VoiceTranscriptionPipeline 和 TextAnalysisPipeline 类已经定义好
from .utils import synthesize as tts_synthesize  # ← 新增导入
from .utils import VoiceTranscriptionPipeline, TextAnalysisPipeline
transcription_pipeline = VoiceTranscriptionPipeline()
analysis_pipeline = TextAnalysisPipeline()
@csrf_exempt
def process_audio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio'}, status=400)

    tmp_path, wav_path = _save_and_transcode(audio)
    tts_output_path = None

    try:
        print(f"[DEBUG] Starting audio processing, file size: {audio.size}")
        
        # 语音识别
        print("[DEBUG] Starting transcription...")
        transcription = transcription_pipeline.transcribe_audio(wav_path)
        print(f"[DEBUG] Transcribed text: {transcription}")
        
        # 生成回复
        print("[DEBUG] Generating response...")
        short = analysis_pipeline.short_response(transcription)
        print(f"[DEBUG] Generated response: {short}")
        
        # TTS 合成英文语音
        print("[DEBUG] Starting TTS synthesis...")
        tts_dir = os.path.join(settings.MEDIA_ROOT, 'tts_replies')
        os.makedirs(tts_dir, exist_ok=True)
        tts_filename = f"tts_{uuid.uuid4().hex}.wav"
        tts_output_path = os.path.join(tts_dir, tts_filename)

        tts_synthesize(short, tts_output_path)
        print(f"[DEBUG] Synthesized audio saved to {tts_output_path}")
        
        # 检查文件是否生成成功
        if not os.path.exists(tts_output_path):
            raise Exception(f"TTS output file not created: {tts_output_path}")
        
        print(f"[DEBUG] TTS file exists, size: {os.path.getsize(tts_output_path)} bytes")
        
        # 存 session
        request.session.setdefault("questions", []).append(transcription)
        request.session.modified = True

        audio_reply_url = os.path.join(settings.MEDIA_URL, 'tts_replies', tts_filename).replace("\\", "/")
        print(f"[DEBUG] audio_reply_url: {audio_reply_url}")
        
        response_data = {
            "short_reply": short,
            "transcription": transcription,
            "audio_reply_url": audio_reply_url
        }
        
        print(f"[DEBUG] Sending response to client: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return JsonResponse({"error": f"Processing failed: {str(e)}"}, status=500)
    
    finally:
        _safe_remove(tmp_path, wav_path)
        # 注意：tts_output_path 不删除，留给前端访问
        # 注意：tts_output_path 不删除，留给前端访问
@csrf_exempt
def finish_session(request):
    questions = request.session.pop("questions", [])
    if not questions:
        return JsonResponse({"error": "No dialogue yet"}, status=400)

    # 初始化文本分析管道
    analysis_pipeline = TextAnalysisPipeline()

    # 生成详细分析报告
    report = []
    for idx, question in enumerate(questions, 1):
        analyse = analysis_pipeline.analyse_response(question)
        report.append({
            "round": idx,
            "original": question,
            "issues": analyse.get("issues", []),
            "corrected": analyse.get("corrected", ""),
            "advanced": analyse.get("advanced", ""),
            "extra_words": analyse.get("extra_words", []),
            "extra_idioms": analyse.get("extra_idioms", []),
            "extra_phrase": analyse.get("extra_phrase", []),
            "extra": analyse.get("extra", [])
        })

    # 生成 PDF
    pdf_io = io.BytesIO()
    doc = SimpleDocTemplate(pdf_io, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    for item in report:
        story.append(Paragraph(f"Round {item['round']}", styles['Heading2']))
        story.append(Spacer(1, 6))
        story.append(Paragraph("Original: " + item['original'], styles['Normal']))
        story.append(Paragraph("Issues: " + "; ".join(item['issues']), styles['Normal']))
        story.append(Paragraph("Corrected: " + item['corrected'], styles['Normal']))
        story.append(Paragraph("Advanced: " + item['advanced'], styles['Normal']))
        story.append(Paragraph("Extra words: " + "; ".join(item['extra_words']), styles['Normal']))
        story.append(Paragraph("Extra idioms: " + "; ".join(item['extra_idioms']), styles['Normal']))
        story.append(Paragraph("Extra phrase: " + "; ".join(item['extra_phrase']), styles['Normal']))
        story.append(Paragraph("Extra examples:", styles['Normal']))
        for ex in item['extra']:
            story.append(Paragraph(f"- {ex}", styles['Normal']))
        story.append(Spacer(1, 12))
    doc.build(story)

    pdf_io.seek(0)
    response = HttpResponse(pdf_io, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="spoken_report.pdf"'
    print("PDF generated successfully")
    return response

# -------------- 小工具 --------------


# 把 text_to_speech 封装成「保存为文件」版本
def text_to_speech_file(self, text, outfile):
    self.tts_engine.save_to_file(text, outfile)
    self.tts_engine.runAndWait()
def spoken_ai(request):
    return render(request, "spoken_ai.html")
def login(request):
    return render(request, "login.html")
# spoken/views.py
from datetime import datetime
from reportlab.pdfgen import canvas   # pip install reportlab

