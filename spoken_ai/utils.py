#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/FunAudioLLM/SenseVoice). All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

import os
import json
import datetime
from model import SenseVoiceSmall
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from openai import OpenAI
import pyttsx3
from pydub import AudioSegment
import os
import uuid
import tempfile

class VoiceTranscriptionPipeline:
    def __init__(self, model_dir="iic/SenseVoiceSmall", device="cuda:0"):
        """
        初始化语音转录管道
        """
        # 语音识别模型
        self.model, self.kwargs = SenseVoiceSmall.from_pretrained(
            model=model_dir, device=device)
        self.model.eval()

    def transcribe_audio(self, audio_path, language="auto", use_itn=False,
                         ban_emo_unk=False, output_timestamp=False):
        """
        转录音频文件
        """
        res = self.model.inference(
            data_in=audio_path,
            language=language,
            use_itn=use_itn,
            ban_emo_unk=ban_emo_unk,
            output_timestamp=output_timestamp,
            **self.kwargs
        )
        text = rich_transcription_postprocess(res[0][0]["text"])
        if output_timestamp:
            return text, res[0][0]["timestamp"]
        return text
import json
from datetime import datetime
from openai import OpenAI

class TextAnalysisPipeline:
    def __init__(self, api_key="sk-feb07e3e5a804d64a7ffdd0305527377", base_url="https://api.deepseek.com/v1", log_file="session_log.jsonl"):
        """
        初始化文本分析管道
        """
        # LLM 客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # 会话日志文件
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

    def short_response(self, transcribed_text):
        """
        简短、自然的日常交流回应
        """
        system = ("You are a friendly English speaking partner. "
                  "Reply briefly and naturally as if in a real conversation. "
                  "Keep your response within 1-2 sentences.")
        user = f"User said: \"{transcribed_text}\""
        rsp = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.7,
            stream=False
        )
        print(rsp.choices[0].message.content.strip())
        return rsp.choices[0].message.content.strip()

    def analyse_response(self, transcribed_text: str) -> dict:
        """
        深度分析 + 纠错 + 拓展语料
        返回 dict 并自动落盘
        """
        system = (
            "You are an IELTS Band-9 speaking coach. "
            "YOUR answer MUST be in English. "
            "You MUST return a single-line JSON object with NO markdown, NO explanation, NO \\n or \\t. "
            "JSON keys (exact order): "
            "1. issues: list[str] – 1–3 条具体问题，英文，≤40 字； "
            "2. corrected: str – 60–80 字符高分改写； "
            "3. advanced: str – 在 corrected 上再用 C2 词汇/习语升级，60–80 字符； "
            "4. extra: list[str] – 3 句额外高分示范，每句 15–30 词，主题相关。 "
            "5. extra_words: list[str] – 20 个 tofel 词汇/习语，与 主题 相关,并给出中文意思 。"
            "6. extra_idioms: list[str] – 3 个 tofel 习语，与 主题 相关,并给出中文意思 。"
            "7. extra_phrase: list[str] – 5个短语,与 主题 相关,并给出中文意思,并且给出短语的使用句子,每个短语的使用句子不能超过20个字符。"
            
            "If any rule is broken, you lose 100 USD."
        )
        user = f"Analyse: \"{transcribed_text}\""
        rsp = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=1.0,
            max_tokens=600,
            stream=False
        )

        raw = rsp.choices[0].message.content.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"issues": ["Parse error"], "corrected": transcribed_text,
                    "advanced": transcribed_text, "extra": []}

        record = {
            "timestamp": datetime.now().isoformat(),
            "original": transcribed_text,
            **data
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return data

    def process_text_pipeline(self, text: str, need_short=True, need_analyse=True):
        """
        对文本进行处理，包括简短回应和详细分析
        """
        results = {}

        # 1. 简短回应
        if need_short:
            short = self.short_response(text)
            results["short_response"] = short

        # 2. 详细分析
        if need_analyse:
            analyse = self.analyse_response(text)
            results["analyse"] = analyse

        return results
# tts_pipeline.py
import pyttsx3
import os
import re
from datetime import datetime



def synthesize(text: str, output_path: str):
    """
    将英文文本合成语音，保存为 WAV 文件。
    """
    try:
        print(f"[TTS] Starting synthesis: '{text}'")
        
        # 每次都创建新引擎，避免状态问题
        engine = pyttsx3.init()
        
        # === 英文专用优化 ===
        engine.setProperty('rate', 170)      # 语速：170 words/min（自然）
        engine.setProperty('volume', 1.0)    # 音量：最大

        # 选择英文语音
        voices = engine.getProperty('voices')
        en_voice = None
        for voice in voices:
            if 'en' in str(voice.languages).lower() or 'english' in voice.name.lower():
                en_voice = voice
                break
        if en_voice:
            engine.setProperty('voice', en_voice.id)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        # 显式停止引擎
        engine.stop()
        
        # 检查文件是否生成
        if not os.path.exists(output_path):
            raise RuntimeError("TTS failed: output file not created.")
            
        file_size = os.path.getsize(output_path)
        print(f"[TTS] Synthesis completed: {output_path} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"[TTS ERROR] Synthesis failed: {e}")
        raise RuntimeError(f"Text-to-speech synthesis failed: {e}")

class ToeflTaskAnalysisPipeline:
    def __init__(self, api_key="sk-feb07e3e5a804d64a7ffdd0305527377", base_url="https://api.deepseek.com/v1", log_file="toefl_analysis_log.jsonl"):
        """
        初始化通用托福任务分析管道
        :param api_key: LLM API 密钥 (建议通过环境变量传入)
        :param base_url: LLM API 基础 URL
        :param log_file: 分析日志文件路径 (.jsonl 格式)
        """
        # 1. 初始化 LLM 客户端
        if api_key is None:
            raise ValueError("API key must be provided.")
        self.client = OpenAI(api_key=api_key, base_url=base_url.strip())

        # 2. 配置日志
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else '.', exist_ok=True)
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

        # 3. 定义各题型的系统提示词
        self.prompts = {
            "task1": """
You are an expert TOEFL Speaking coach. Analyze the student's response to the given TOEFL Speaking Task 1 question and provide feedback in strict JSON format.

Given:
- The TOEFL question (prompt)
- The student's spoken response (transcribed text)

Do the following:

1. **issues**: Identify exactly THREE major problems (e.g., "Off-topic response", "No clear stance", "Lack of development").

2. **reason**: Explain how you evaluated the response against TOEFL criteria (task fulfillment, coherence, language use, etc.) in the context of the given question.

3. **answer**: Write a high-scoring (4.0/4.0) model answer (100–120 words) that directly addresses the question with a clear opinion, logical structure, and specific examples.

4. **phrases**: List exactly FIVE useful academic/idiomatic phrases relevant to the topic.

5. **sentences**: Provide one example sentence for each phrase, in the same order.

Output ONLY valid JSON with keys: "issues", "reason", "answer", "phrases", "sentences".          
""".strip(),

            "task2": """
            """.strip(),
        }

    def _call_llm(self, system_prompt: str, user_message: str, model: str = "deepseek-chat") -> dict:
        """通用 LLM 调用与 JSON 解析方法"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )

        raw_output = response.choices[0].message.content.strip()

        # 尝试解析 JSON
        try:
            result = json.loads(raw_output)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("Model output is not valid JSON.")

        return result

    def _validate_feedback(self, result: dict, required_keys: set) -> bool:
        """验证 LLM 返回结果是否包含必要字段"""
        return required_keys.issubset(result.keys())

    def _log_interaction(self, task_type: str, input_data: dict, output_data: dict = None, error: str = None):
        """统一日志记录方法"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            **input_data
        }
        if error:
            log_entry["error"] = error
        else:
            log_entry["feedback"] = output_data

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def analyze_task1(self, question: str, student_answer: str) -> dict:
        """
        分析 TOEFL Speaking Task 1
        :param question: 题目文本
        :param student_answer: 学生回答文本（语音转写后）
        :return: 结构化反馈 dict
        """
        required_keys = {"issues", "reason", "answer", "phrases", "sentences"}
        input_data = {"question": question, "student_answer": student_answer}

        try:
            user_message = f"""TOEFL Speaking Task 1 Question:
{question}

Student's Response:
{student_answer}"""

            result = self._call_llm(self.prompts["task1"], user_message)
            
            if not self._validate_feedback(result, required_keys):
                raise ValueError(f"Missing required keys in model output. Expected: {required_keys}, Got: {result.keys()}")

            self._log_interaction("task1", input_data, result)
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task1 Analysis Failed: {error_msg}")
            self._log_interaction("task1", input_data, error=error_msg)
            raise
# utils.py
# utils.py
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from urllib.parse import urljoin

def generate_pdf_report(task, student_answer, feedback):
    # 注册中文字体（建议只注册一次，此处为简化）
    font_path = os.path.join(settings.BASE_DIR, 'font', 'NotoSansSC-Regular.ttf')
    if not hasattr(generate_pdf_report, '_font_registered'):
        pdfmetrics.registerFont(TTFont('NotoSansSC', font_path))
        generate_pdf_report._font_registered = True

    filename = f"task1_{task.id}_report.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 50
    left_margin = 50

    # 统一使用中文字体
    def draw_text(text, size=12, bold=False):
        nonlocal y
        font_name = "NotoSansSC-Bold" if bold else "NotoSansSC"
        try:
            c.setFont(font_name, size)
        except:
            c.setFont("NotoSansSC", size)  # fallback
        c.drawString(left_margin, y, text)
        y -= 20 if size >= 12 else 16

    # 标题
    c.setFont("NotoSansSC-Bold", 16)
    c.drawString(left_margin, y, f"TOEFL 口语 Task 1 评分报告：{task.name}")
    y -= 30

    # 题目
    draw_text(f"题目：{task.readingtext or '无'}", bold=True)
    y -= 10

    # 学生回答
    draw_text("你的回答：", bold=True)
    y += 5  # 微调
    c.setFont("NotoSansSC", 11)
    lines = student_answer.split('\n')
    for line in lines:
        if y < 50:  # 防止超出页面
            c.showPage()
            y = height - 50
        c.drawString(left_margin, y, line[:80])  # 简单截断长行
        y -= 16
    y -= 10

    # AI 参考答案
    model_answer = feedback.get('answer', '').strip()
    if model_answer:
        draw_text("AI 参考答案：", bold=True)
        y += 5
        c.setFont("NotoSansSC", 11)
        for line in model_answer.split('\n'):
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(left_margin, y, line[:80])
            y -= 16
        y -= 10

    # 问题与建议
    issues = feedback.get('issues', '').strip()
    reason = feedback.get('reason', '').strip()
    if issues or reason:
        draw_text("问题与建议：", bold=True)
        if issues:
            c.setFont("NotoSansSC", 11)
            c.drawString(left_margin, y, f"• 问题：{issues}")
            y -= 18
        if reason:
            c.setFont("NotoSansSC", 11)
            c.drawString(left_margin, y, f"• 建议：{reason}")
            y -= 18
        y -= 10

    # 推荐短语
    phrases = feedback.get('phrases')
    if phrases:
        draw_text("推荐短语：", bold=True)
        c.setFont("NotoSansSC", 11)
        phrase_text = "；".join(phrases) if isinstance(phrases, list) else str(phrases)
        c.drawString(left_margin, y, phrase_text[:100] + ("..." if len(phrase_text) > 100 else ""))
        y -= 20

    # 推荐句型
    sentences = feedback.get('sentences')
    if sentences:
        draw_text("推荐句型：", bold=True)
        c.setFont("NotoSansSC", 11)
        sent_text = "；".join(sentences) if isinstance(sentences, list) else str(sentences)
        c.drawString(left_margin, y, sent_text[:100] + ("..." if len(sent_text) > 100 else ""))
        y -= 20

    c.save()
    return urljoin(settings.MEDIA_URL, f'reports/{filename}')