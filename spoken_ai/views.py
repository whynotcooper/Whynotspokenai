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
from .models import Task2Model, Task3Model, Task4Model
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
    username = request.session.get('username')
    login_in = request.session.get('login_in', False)

    context = {
        'username': username,
        'login_in': login_in,
    }
    return render(request, 'index.html', context)




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


# 如果需要函数视图版本
def register(request):
    if request.method == 'GET':
        # 直接渲染注册页面
        return render(request, 'register.html')

    # POST 请求：用户注册
    print("进入 register 视图 POST")
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    phone = request.POST.get('phone', '').strip()
    print("接收参数：", username, password, phone)

    # 参数校验：只要有一个为空就返回错误
    if not (username and password and phone):
        return JsonResponse({'code': 400, 'message': '缺少必传的参数'})

    # 再做一次简单校验（长度、手机号格式），也可以只在前端做
    if len(password) < 8:
        return JsonResponse({'code': 400, 'message': '密码长度至少为8位'})

    import re
    phone_regex = re.compile(r'^1[3-9]\d{9}$')
    if not phone_regex.match(phone):
        return JsonResponse({'code': 400, 'message': '手机号格式不正确'})

    # 检查用户名是否已存在
    user = UserInfoModel.objects.filter(username=username).first()
    if user:
        return JsonResponse({'code': 400, 'message': '用户名已存在'})

    # 创建用户（这里是明文密码，后续建议使用加密密码）
    user = UserInfoModel.objects.create(
        username=username,
        password=password,
        phone=phone
    )
    print("新建用户：", user)

    # 设置 session
    request.session['login_in'] = True
    request.session['username'] = user.username
    request.session['user_id'] = user.id

    return JsonResponse({'code': 200, 'message': '注册成功'})
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .models import UserInfoModel

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    登录视图：
    - GET  请求：渲染 login.html
    - POST 请求：用 UserInfoModel 校验用户名/手机号 + 密码
    """
    # 统一拿 next：POST 优先，其次 GET
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    if request.method == "GET":
        return render(request, "login.html", {"next": next_url})

    # POST：提交登录
    login_id = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    if not (login_id and password):
        messages.error(request, "用户名/手机号 和 密码不能为空。")
        return render(request, "login.html", {"next": next_url, "username": login_id})

    user = UserInfoModel.objects.filter(
        Q(username=login_id) | Q(phone=login_id),
        password=password
    ).first()

    if user:
        request.session['login_in'] = True
        request.session['username'] = user.username
        request.session['user_id'] = user.id

        # ✅ 安全校验 next，防止跳转到外站
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        return redirect("spoken_ai:index")

    messages.error(request, "用户名或密码不正确，请重试。")
    return render(request, "login.html", {"next": next_url, "username": login_id})

from django.contrib.auth.forms import PasswordResetForm

def password_reset(request):
    """
    简单版找回密码视图：
    - GET：展示表单
    - POST：校验邮箱，成功后在当前页提示发送成功
    """
    email_sent = False

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # TODO：后面你想真正发邮件时，再把这段打开
            # form.save(
            #     request=request,
            #     use_https=request.is_secure(),
            #     email_template_name="spoken_ai/password_reset_email.html",
            #     subject_template_name="spoken_ai/password_reset_subject.txt",
            # )

            email_sent = True
    else:
        form = PasswordResetForm()

    context = {
        "form": form,
        "email_sent": email_sent,
    }
    return render(request, "password_reset.html", context)
def logout_view(request):
    """
    退出登录视图：
    - 调用 Django 的 logout() 清除会话
    - 再渲染一个精美的 logout.html 提示“已安全退出”
    """
    # 不管是否已登录，logout 都是安全的（幂等）
    logout(request)

    # 你之前写好的精美退出页面
    # 如果你想直接回首页，也可以改成 return redirect("index")
    return render(request, "logout.html")
def task1_list(request):
    tasks = Task1Model.objects.all().order_by('name')
    return render(request, 'toefl_task1.html', {'tasks': tasks})
def task2_list(request):
    tasks = Task2Model.objects.all().order_by('name')
    return render(request, 'toefl_task2.html', {'tasks': tasks})
def task3_list(request):
    tasks = Task3Model.objects.all().order_by('name')
    return render(request, 'toefl_task3.html', {'tasks': tasks})
def task4_list(request):
    tasks = Task4Model.objects.all().order_by('name')
    return render(request, 'toefl_task4.html', {'tasks': tasks})



def show_task1(request, task_id):
    task = Task1Model.objects.get(id=task_id)
    return render(request, 'show_task1.html', {'task': task})
def show_task2(request, task_id):
    task = Task2Model.objects.get(id=task_id)
    return render(request, 'show_task2.html', {'task': task})
def show_task3(request, task_id):
    task = Task3Model.objects.get(id=task_id)
    return render(request, 'show_task3.html', {'task': task})
def show_task4(request, task_id):
    task = Task4Model.objects.get(id=task_id)
    return render(request, 'show_task4.html', {'task': task})

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
from .utils import generate_pdf_report, generate_pdf_report2  # 你需要实现这个函数

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
@csrf_exempt
@require_http_methods(["POST"])
def analyse_task2(request, task_id):
    """
    接收用户的 Task2 回答文本，进行 AI 分析并生成 PDF。
    """
    # 获取对应的 Task2 题目
    task = get_object_or_404(Task2Model, id=task_id)

    try:
        data = json.loads(request.body)
        student_answer = data.get('student_answer', '').strip()
        if not student_answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        # === 调用 AI 分析（Task2 专用） ===
        feedback = analysis_task_pipeline.analyze_task2(
            reading_passage=task.readingtext or "No reading passage provided.",
            listening_passage=task.listeningtext or "No listening passage provided.",
            question=task.questiontext or "No prompt provided.",
            student_answer=student_answer
        )

        # === 生成 PDF 报告 ===
        # 如果 generate_pdf_report 已经支持 Task1，用法基本可以复用
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
        print(f"[ERROR] Task2 Analysis failed: {e}\n{traceback.format_exc()}")
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
@csrf_exempt
@require_http_methods(["POST"])
def analyse_task3(request, task_id):
    """
    接收用户的 Task3 回答文本，进行 AI 分析并生成 PDF。（Integrated – Academic）
    """
    # 获取对应的 Task3 题目
    task = get_object_or_404(Task3Model, id=task_id)

    try:
        data = json.loads(request.body)
        student_answer = data.get('student_answer', '').strip()
        if not student_answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        # === 调用 AI 分析（Task3 专用） ===
        feedback = analysis_task_pipeline.analyze_task3(
            reading_passage=task.readingtext or "No reading passage provided.",
            listening_passage=task.listeningtext or "No listening passage provided.",
            question=task.questiontext or "No prompt provided.",
            student_answer=student_answer
        )

        # === 生成 PDF 报告 ===
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
        print(f"[ERROR] Task3 Analysis failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)
def analyse_task4(request, task_id):
    """
    接收用户的 Task4 回答文本，进行 AI 分析并生成 PDF。（Integrated – Academic Lecture Only）
    """
    # 获取对应的 Task4 题目
    task = get_object_or_404(Task4Model, id=task_id)

    try:
        data = json.loads(request.body)
        student_answer = data.get('student_answer', '').strip()
        if not student_answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        # === 调用 AI 分析（Task4 专用，无阅读文本） ===
        feedback = analysis_task_pipeline.analyze_task4(
            listening_passage=task.listeningtext or "No listening passage provided.",
            question=task.questiontext or "No prompt provided.",
            student_answer=student_answer
        )

        # === 生成 PDF 报告 ===
        pdf_url = generate_pdf_report2(
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
        print(f"[ERROR] Task4 Analysis failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)

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

 


