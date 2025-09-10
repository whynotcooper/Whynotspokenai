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



class VoiceProcessingPipeline:
    def __init__(self,
                 model_dir="iic/SenseVoiceSmall",
                 device="cuda:0",
                 api_key="sk-feb07e3e5a804d64a7ffdd0305527377",
                 base_url="https://api.deepseek.com",
                 log_file="session_log.jsonl"):
        """
        初始化
        """
        # 语音识别
        self.model, self.kwargs = SenseVoiceSmall.from_pretrained(
            model=model_dir, device=device)
        self.model.eval()

        # LLM 客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # TTS
        self.tts_engine = pyttsx3.init()
        self.set_tts_properties()

        # 会话日志文件
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

    # ====================== 基础工具 ======================
    def set_tts_properties(self, rate=150, volume=0.9):
        self.tts_engine.setProperty('rate', rate)
        self.tts_engine.setProperty('volume', volume)

    def transcribe_audio(self, audio_path, language="auto", use_itn=False,
                         ban_emo_unk=False, output_timestamp=False):
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

    def text_to_speech(self, text):
        print("[TTS] 正在播放语音回复...")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        print("[TTS] 播放完毕。")

    # ====================== LLM 交互 ======================
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
        return rsp.choices[0].message.content.strip()

    def analyse_response(self, transcribed_text: str) -> dict:
            '''
              深度分析 + 纠错 + 拓展语料
               返回 dict 并自动落盘
            '''
            system = (
        "You are an IELTS Band-9 speaking coach. "
        "You MUST return a single-line JSON object with NO markdown, NO explanation, NO \\n or \\t. "
        "JSON keys (exact order): "
        "1. issues: list[str] – 1–3 条具体问题，中文，≤40 字； "
        "2. corrected: str – 60–80 字符高分改写； "
        "3. advanced: str – 在 corrected 上再用 C2 词汇/习语升级，60–80 字符； "
        "4. extra: list[str] – 3 句额外高分示范，每句 15–30 词，主题相关。 "
        "5. extra_words: list[str] – 20 个 tofel 词汇/习语，与 主题 相关,并给出中文意思 。"
        "6.extra_idioms: list[str] – 3 个 tofel 习语，与 主题 相关,并给出中文意思 。"
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

    # ====================== 主流程 ======================
    def process_audio_pipeline(self, audio_path, language="auto",
                               need_short=True, need_analyse=True,
                               play_short=True, play_analyse=True):
        """
        完整流程
        """
        results = {}

        # 1. ASR
        transcription = self.transcribe_audio(audio_path, language=language)
        results["transcription"] = transcription
        print(f"[ASR] {transcription}")

        # 2. short response
        if need_short:
            short = self.short_response(transcription)
            results["short_response"] = short
            print(f"[SHORT] {short}")
            if play_short:
                self.text_to_speech(short)

        # 3. analyse response
        if need_analyse:
           analyse = self.analyse_response(transcription)
           results["analyse"] = analyse

    # 生成文件名：时间戳 + 用户原句前10字符
           safe_text = "".join(c for c in transcription[:10] if c.isalnum() or c in (' ', '_'))
           report_file = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_text}.txt"
           report_path = os.path.abspath(report_file)

           with open(report_path, "w", encoding="utf-8") as f:
                f.write("========== 修改报告 ==========\n")
                f.write(f"Issues: {'; '.join(analyse['issues'])}\n")
                f.write(f"Corrected: {analyse['corrected']}\n")
                f.write(f"Advanced: {analyse['advanced']}\n")
                f.write(f"Extra words: {'; '.join(analyse['extra_words'])}\n")
                f.write(f"Extra idioms: {'; '.join(analyse['extra_idioms'])}\n")
                f.write(f"Extra phrase: {'; '.join(analyse['extra_phrase'])}\n")
                f.write("Extra examples:\n")
                for idx, ex in enumerate(analyse["extra"], 1):
                    f.write(f"  {idx}. {ex}\n")
                f.write("==============================\n")

           print(f"[ANALYSE] 报告已写入：{report_path}")