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

def process_audio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    # 确保session存在
    if not request.session.session_key:
        request.session.create()
    
    session_id = request.session.session_key
    print(f"[SESSION] Processing audio for session: {session_id}")

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio'}, status=400)

    tmp_path, wav_path = _save_and_transcode(audio)
    tts_output_path = None

    try:
        print(f"[DEBUG] Starting audio processing for session {session_id}, file size: {audio.size}")
        
        # 语音识别
        print("[DEBUG] Starting transcription...")
        transcription = transcription_pipeline.transcribe_audio(wav_path)
        print(f"[SESSION {session_id}] User: {transcription}")
        
        # 生成回复（使用session ID）
        print("[DEBUG] Generating response with context...")
        short = analysis_pipeline.short_response(transcription, session_id=session_id)
        print(f"[SESSION {session_id}] Assistant: {short}")
        
        # 获取当前会话的历史记录（用于调试）
        current_history = analysis_pipeline.get_session_history(session_id)
        print(f"[SESSION {session_id}] History length: {len(current_history)} messages")
        
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
        
        # 存储会话数据到Django session（可选，用于前端显示）
        conversation_entry = {
            "user": transcription,
            "assistant": short,
            "timestamp": datetime.datetime.now().isoformat(),
            "audio_url": os.path.join(settings.MEDIA_URL, 'tts_replies', tts_filename).replace("\\", "/")
        }
        
        request.session.setdefault("conversation_history", []).append(conversation_entry)
        
        # 限制Django session中存储的对话数量
        if len(request.session["conversation_history"]) > 10:
            request.session["conversation_history"] = request.session["conversation_history"][-10:]
            
        request.session.modified = True

        audio_reply_url = conversation_entry["audio_url"]
        print(f"[DEBUG] audio_reply_url: {audio_reply_url}")
        
        response_data = {
            "short_reply": short,
            "transcription": transcription,
            "audio_reply_url": audio_reply_url,
            "session_id": session_id,
            "conversation_turn": len(current_history) // 2 + 1  # 当前对话轮数
        }
        
        print(f"[DEBUG] Sending response to client: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"[ERROR] Processing failed for session {session_id}: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return JsonResponse({"error": f"Processing failed: {str(e)}"}, status=500)
    
    finally:
        _safe_remove(tmp_path, wav_path)