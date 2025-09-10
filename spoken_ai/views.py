from django.shortcuts import render
# views.py
# spoken/views.py
import os, uuid, json
from django.conf import settings

import subprocess
import json, os, tempfile, datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io


UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'audio')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_and_transcode(audio):
    """返回 (tmp_path, wav_path)"""
    ext = os.path.splitext(audio.name)[1] or ".webm"
    tmp = tempfile.mktemp(suffix=ext, dir=UPLOAD_DIR)
    wav = tempfile.mktemp(suffix=".wav", dir=UPLOAD_DIR)
    with open(tmp, "wb+") as f:
        for c in audio.chunks():
            f.write(c)
    subprocess.run([
        "ffmpeg", "-y", "-i", tmp, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", wav
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
from .utils import VoiceTranscriptionPipeline, TextAnalysisPipeline
transcription_pipeline = VoiceTranscriptionPipeline()
analysis_pipeline = TextAnalysisPipeline()

@csrf_exempt
def process_audio(request):
    """
    单次录音上传
    返回：{ short_reply: <str> }   （问题存 session，不返回）
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio'}, status=400)

    # 保存 + 转码 wav（同你旧代码）
    tmp_path, wav_path = _save_and_transcode(audio)   # 复用你旧逻辑，略
    print(f"tmp_path: {tmp_path}, wav_path: {wav_path}")
    try:
        # 初始化语音转录管道

        transcription = transcription_pipeline.transcribe_audio(wav_path)
        print(f"transcription: {transcription}")
        # 初始化文本分析管道

        short = analysis_pipeline.short_response(transcription)
        print(f"short: {short}")
        # 把问题攒到 session
        if "questions" not in request.session:
            request.session["questions"] = []
        request.session["questions"].append(transcription)
        request.session.modified = True

        # 返回短片段回答
        return JsonResponse({"short_reply": short})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        _safe_remove(tmp_path, wav_path)
@csrf_exempt
def finish_session(request):
    """
    结束对话，对 session 里所有问题进行详细分析并生成 PDF 供下载
    """
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
    return response

# -------------- 小工具 --------------


# 把 text_to_speech 封装成「保存为文件」版本
def text_to_speech_file(self, text, outfile):
    self.tts_engine.save_to_file(text, outfile)
    self.tts_engine.runAndWait()
def spoken_ai(request):
    return render(request, "spoken_ai.html")
# spoken/views.py
from datetime import datetime
from reportlab.pdfgen import canvas   # pip install reportlab

