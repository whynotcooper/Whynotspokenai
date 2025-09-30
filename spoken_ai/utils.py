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
import datetime
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
            "timestamp": datetime.datetime.now().isoformat(),
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