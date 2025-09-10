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
            # 定义系统提示，用于指导AI如何分析文本
            system = (
        "You are an IELTS Band-9 speaking coach. "  # 指定AI角色为雅思9分口语教练
        "You MUST return a single-line JSON object with NO markdown, NO explanation, NO \\n or \\t. "  # 要求返回单行JSON，无格式化
        "JSON keys (exact order): "  # 指定JSON键的顺序
        "1. issues: list[str] – 1–3 条具体问题，中文，≤40 字； "  # 问题列表，1-3个中文问题，每条不超过40字
        "2. corrected: str – 60–80 字符高分改写； "  # 高分改写版本，60-80字符
        "3. advanced: str – 在 corrected 上再用 C2 词汇/习语升级，60–80 字符； "  # C2级别升级版本，60-80字符
        "4. extra: list[str] – 3 句额外高分示范，每句 15–30 词，主题相关。 "  # 3个高分示范句，每句15-30词
        "5. extra_words: list[str] – 20 个 tofel 词汇/习语，与 主题 相关,并给出中文意思 。"  # 20个托福词汇/习语及其中文意思
        "6.extra_idioms: list[str] – 3 个 tofel 习语，与 主题 相关,并给出中文意思 。"  # 3个托福习语及其中文意思
        "7. extra_phrase: list[str] – 5个短语,与 主题 相关,并给出中文意思,并且给出短语的使用句子,每个短语的使用句子不能超过20个字符。"  # 5个短语及其中文意思和使用示例
        
        "If any rule is broken, you lose 100 USD."  # 违反规则的惩罚提示
          )
            # 构建用户输入，包含需要分析的文本
            user = f"Analyse: \"{transcribed_text}\""
            # 调用AI模型进行分析
            rsp = self.client.chat.completions.create(
            model="deepseek-chat",  # 使用deepseek-chat模型
            messages=[{"role": "system", "content": system},  # 系统提示
                  {"role": "user", "content": user}],  # 用户输入
            temperature=1.0,  # 设置温度为1.0，增加回答的随机性
            max_tokens=600,  # 最大生成600个token
            stream=False  # 不使用流式输出
    )

            # 处理AI返回的原始响应，去除可能的markdown格式
            raw = rsp.choices[0].message.content.strip().removeprefix("```json").removesuffix("```").strip()
            try:
              # 尝试解析JSON响应
              data = json.loads(raw)
            except json.JSONDecodeError:
             # 如果解析失败，返回错误信息并使用原始文本
             data = {"issues": ["Parse error"], "corrected": transcribed_text,
                 "advanced": transcribed_text, "extra": []}

            # 构建包含时间戳和原始文本的记录字典
            record = {
              "timestamp": datetime.datetime.now().isoformat(),  # 添加当前时间戳
              "original": transcribed_text,  # 保存原始文本
            **data  # 合并分析结果
              }
            # 将记录写入日志文件
            with open(self.log_file, "a", encoding="utf-8") as f:
                 f.write(json.dumps(record, ensure_ascii=False) + "\n")  # 确保非ASCII字符不被转义
            return data  # 返回分析结果

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
            print(f"[ANALYSE] {analyse}")
            # 打印修改报告 + 拓展语料
            print("\n========== 修改报告 ==========")
            print("Issues:", "; ".join(analyse["issues"]))
            print("Corrected:",analyse["corrected"])
            print("Advanced:",analyse["advanced"])
            print("Extra words:", "; ".join(analyse["extra_words"]))
            print("Extra idioms:", "; ".join(analyse["extra_idioms"]))
            print("Extra phrase:", "; ".join(analyse["extra_phrase"]))
            print("Extra examples:")
            for idx, ex in enumerate(analyse["extra"], 1):
                print(f"  {idx}. {ex}")
            print("==============================\n")
            if play_analyse:
                self.text_to_speech(
                    f"Here is your corrected version: {analyse['corrected']}")

        return results


# ====================== 快速测试 ======================
if __name__ == "__main__":

    wav = "Task1.mp3"
    pl = VoiceProcessingPipeline()
    result=pl.transcribe_audio(wav)
    print(result)