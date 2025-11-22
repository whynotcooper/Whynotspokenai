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
from django.shortcuts import render, get_object_or_404
from .models import Task1Model
from .models import Task2Model
from django.views.decorators.http import require_http_methods

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'audio')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_and_transcode(audio):# 用来转录语音为wav格式
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
from .utils import ToeflTaskAnalysisPipeline
transcription_pipeline = VoiceTranscriptionPipeline()
analysis_pipeline = TextAnalysisPipeline()
analysis_task_pipeline = ToeflTaskAnalysisPipeline()
@csrf_exempt
def process_audio(request):# 用来处理上传的音频文件变成文本文件
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
def finish_session(request):# 这里其实没有做好，后续用来可以连续对话，分析
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
def spoken_ai(request): # spoken_ai.html ，第一个主页面
    return render(request, "spoken_ai.html")
def toefl_index(request):  # toefl_index.html ，第二个主页面/toefl页面
    return render(request, "toefl_index.html")
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import UserInfoModel

import json

class RegisterView(View):
    """用户注册视图"""
    
    def get(self, request):
        """GET请求返回注册页面"""
        return render(request, 'register.html')
    
    def post(self, request):
        """POST请求处理注册逻辑"""
        try:
            # 获取请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            phone = data.get('phone', '').strip()
            
            # 基本数据验证
            if not all([username, password, phone]):
                return JsonResponse({
                    'code': 400,
                    'message': '用户名、密码和手机号不能为空',
                    'data': None
                })
            
            # 创建用户实例（不直接保存到数据库）
            user = UserInfoModel(
                username=username,
                password=make_password(password),  # 密码加密
                phone=phone
            )
            
            # 完整验证模型字段
            user.full_clean()
            
            # 保存到数据库
            user.save()
            
            return JsonResponse({
                'code': 200,
                'message': '注册成功',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'phone': user.phone
                }
            })
            
        except ValidationError as e:
            # 处理字段验证错误
            error_messages = []
            for field, errors in e.message_dict.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            return JsonResponse({
                'code': 400,
                'message': '; '.join(error_messages),
                'data': None
            })
            
        except Exception as e:
            # 处理其他异常（如唯一约束冲突）
            error_msg = str(e)
            if 'username' in error_msg.lower() or 'username' in error_msg:
                return JsonResponse({
                    'code': 400,
                    'message': '用户名已存在',
                    'data': None
                })
            elif 'phone' in error_msg.lower() or 'phone' in error_msg:
                return JsonResponse({
                    'code': 400,
                    'message': '手机号已存在',
                    'data': None
                })
            else:
                return JsonResponse({
                    'code': 500,
                    'message': f'注册失败: {error_msg}',
                    'data': None
                })

# 如果需要函数视图版本
def register(request):
    if request.method == 'GET':
        return render(request,'register.html')
    else:
        # 用户注册
        print("register1111111")
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        print(username, password, phone, )
        if not (username or password or phone ):
            return JsonResponse({'code': 400, 'message': '缺少必传的参数'})
        user = UserInfoModel.objects.filter(username=username).first()
        if user:
            return JsonResponse({'code': 400, 'message': '用户名已存在'})
        user = UserInfoModel.objects.create(username=username, password=password, phone=phone)
        request.session['login_in'] = True
        request.session['username'] = user.username
        request.session['user_id'] = user.id
        return JsonResponse({'code': 200})

def task1_list(request):
    tasks = Task1Model.objects.all().order_by('name')
    return render(request, 'toefl_task1.html', {'tasks': tasks})
def task2_list(request):
    tasks = Task2Model.objects.all().order_by('name')
    return render(request, 'toefl_task2.html', {'tasks': tasks})

def show_task1(request, task_id):
    task = Task1Model.objects.get(id=task_id)
    return render(request, 'show_task1.html', {'task': task})
def show_task2(request, task_id):
    task = Task2Model.objects.get(id=task_id)
    return render(request, 'show_task2.html', {'task': task})
# views.py

@csrf_exempt
@require_http_methods(["POST"])
def process_task_audio(request, task_id):
    """
    接收音频，转写后返回文本供用户编辑。
    """
    task = get_object_or_404(Task1Model, id=task_id)
    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio file provided.'}, status=400)

    tmp_path, wav_path = _save_and_transcode(audio)
    try:
        transcription = transcription_pipeline.transcribe_audio(wav_path, language="auto")
        if not transcription.strip():
            return JsonResponse({'error': 'Transcription is empty.'}, status=400)
        return JsonResponse({
            'success': True,
            'transcription': transcription
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] Transcription failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        _safe_remove(tmp_path, wav_path)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils import generate_pdf_report  # 你需要实现这个函数

@csrf_exempt
@require_http_methods(["POST"])
def analyse_task1(request, task_id):
    """
    接收用户确认后的文本，进行 AI 分析并生成 PDF。
    """
    task = get_object_or_404(Task1Model, id=task_id)
    try:
        data = json.loads(request.body)
        student_answer = data.get('student_answer', '').strip()
        if not student_answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        # AI 分析
        feedback = analysis_task_pipeline.analyze_task1(
            question=task.readingtext or "No prompt provided.",
            student_answer=student_answer
        )

        # 生成 PDF（你需要实现 generate_pdf_report）
        pdf_url = generate_pdf_report(
            task=task,
            student_answer=student_answer,
            feedback=feedback
        )

        return JsonResponse({
            'success': True,
            'feedback': feedback,
            'pdf_url': pdf_url
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] Analysis failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)
def solve_followup(request):
    """
    接收前端 follow-up 追问，调用 AI 追问 agent，并把结果以 JSON 返回给页面。
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "请求数据格式错误（JSON 解析失败）"},
            status=400
        )

    # 学生的追问（中英文都可以）
    student_question = (data.get("message") or "").strip()
    print("学生追问：", student_question)
    # 上下文字段（readingtext + student_answer）
    context = data.get("context") or {}
    reading_text = (context.get("readingtext") or "").strip()
    student_answer = (context.get("student_answer") or "").strip()

    if not student_question:
        return JsonResponse(
            {"success": False, "error": "追问内容不能为空。"},
            status=400
        )

    # 调用你已经写好的追问 agent
    try:
        print("上下文字段：", reading_text, student_answer)
        feedback = analysis_task_pipeline.answer_followup_question(
            reading_text=reading_text,
            student_answer=student_answer,
            student_question=student_question,
            temperature=0.3,
            log=True,
        )
    except Exception as e:
        # LLM 调用错误兜底
        return JsonResponse(
            {"success": False, "error": f"AI 分析失败：{str(e)}"},
            status=500
        )

    # 追问 agent 约定返回结构：
    # {
    #   "english_answer": "...",
    #   "chinese_answer": "..."
    # }
    english_answer = (feedback.get("english_answer") or "").strip()
    chinese_answer = (feedback.get("chinese_answer") or "").strip()

    # 拼成一个文本，方便前端直接展示
    # 你也可以分两条气泡展示，这里先简单拼在一起
    parts = []
    if english_answer:
        parts.append("【English Explanation】\n" + english_answer)
    if chinese_answer:
        parts.append("【中文讲解】\n" + chinese_answer)

    if not parts:
        reply_text = "暂时没有生成有效解答，请稍后再试。"
    else:
        reply_text = "\n\n".join(parts)

    return JsonResponse(
        {
            "success": True,
            "reply": reply_text,
        }
    )
def followup(request):
    """
    通用追问页面：
    所有要展示的内容都通过 URL query 参数传进来，
    比如：/followup/?task_name=...&readingtext=...&student_answer=...&issues=...&reason=...&answer=...
    """

    context = {
        "task_name": request.GET.get("task_name", ""),          # 任务名/题目名，显示在页面标题
        "readingtext": request.GET.get("readingtext", ""),      # 阅读原文
        "student_answer": request.GET.get("student_answer", ""),# 学生最终回答
        "issues": request.GET.get("issues", ""),                # AI 反馈：问题
        "reason": request.GET.get("reason", ""),                # AI 反馈：建议/原因
        "answer": request.GET.get("answer", ""),                # AI 反馈：参考答案
    }

    return render(request, "followup.html", context)

 


