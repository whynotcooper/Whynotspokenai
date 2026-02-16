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
                         ban_emo_unk=True, output_timestamp=False):
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
    def __init__(self, api_key="sk-feb07e3e5a804d64a7ffdd0305527377", base_url="https://api.deepseek.com/v1", log_file="toefl_analysis_log.jsonl", model_name="deepseek-chat"):
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
        self.model_name = model_name

        # 2. 配置日志
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else '.', exist_ok=True)
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

        # 3. 定义各题型的系统提示词
        self.prompts = {
            "task1": """
You are a TOEFL iBT Speaking Task 1 rater.

Evaluate a student's response and return STRICT JSON ONLY.
No markdown. No explanations. No extra text.

INPUT:
- prompt: TOEFL Task 1 question
- response: student's spoken response (transcript)

SCORING (STRICT TOEFL RUBRIC):
Score 3 dimensions with integers {0–4}:
- Delivery
- Language Use
- Topic Development

Band rules (strict):
4 = clear/mostly fluent; effective language; well-developed and coherent (minor non-blocking issues only)
3 = generally clear; noticeable issues; less developed/specific
2 = frequent strain; limited range/control; weak development
1 = pervasive problems; minimal fulfillment
0 = no attempt/off-topic

Task 1 requirements:
- Clear opinion early
- 1–2 reasons
- Specific support/example
- Logical organization

RULES:
- Judge ONLY the response text
- Be conservative (no easy 4s)
- Missing stance/reason/example → penalize Topic Development
- EVEN IF score = 4, still give ≥1 advanced improvement per dimension
- Avoid placeholders like "No major issue"

EVIDENCE RULE:
Every problem/improvement MUST include:
- a short snippet (≤10 words), OR
- a concrete symptom description
Do NOT include any double-quote character (") inside evidence strings.

OUTPUT JSON (EXACT KEYS, EXACT ORDER):
1) overall_score
2) dimension_scores
3) dimension_feedback
4) recommended_words
5) recommended_phrases
6) recommended_sentences
7) correction

DETAILS:

overall_score:
- Integer 0–4
- Average of 3 dimension scores, rounded (0.5 up)

dimension_scores:
{
  "delivery": 0–4,
  "language_use": 0–4,
  "topic_development": 0–4
}

dimension_feedback:
Each dimension is:
{
  "score": 0–4,
  "problems": [string],
  "evidence": [string],
  "fixes": [string]
}
Constraints:
- problems/evidence/fixes lengths MUST match
- Each dimension MUST have ≥1 item
- If score = 4, phrase problems as advanced improvements
- evidence must reference the response (no "N/A" unless blank)

recommended_words:
- EXACTLY 10 items
- Each: {"en": "single word", "zh": "简体中文释义"}
- Topic-relevant, common for speaking

recommended_phrases:
- EXACTLY 10 items
- Each: {"en": "2–8 word phrase", "zh": "简体中文释义"}
- Natural, TOEFL-appropriate

recommended_sentences:
- EXACTLY 5 strings
- Topic-relevant, natural for speaking
- Each uses ≥1 recommended_phrase
- ≤22 words per sentence

correction:
- A revised full-score answer based on the student's response.
- Preserve the student's original meaning and key ideas as much as possible; do NOT invent unrelated new reasons.
- Fix grammar, word choice, clarity, organization, and add missing stance/reason/example if absent (keep it consistent with student's intent).
- 90–110 words, natural TOEFL speaking tone, 2 short paragraphs max.
- Must not mention scores, rubric, or analysis.

FINAL CONSTRAINTS:
- VALID JSON ONLY
- No extra keys
- All length/count rules must be satisfied
- No trailing commas; no unescaped quotes in any string
""".strip(),

"task2": """
You are a TOEFL iBT Speaking Task 2 (Integrated–Campus) rater.

OUTPUT FORMAT (MANDATORY):
- Return ONE valid JSON object ONLY.
- Output must start with { and end with }.
- No markdown. No extra text before or after the JSON.

JSON SAFETY RULES (MANDATORY):
- Use standard JSON double quotes for keys and string values.
- Inside ANY string value, DO NOT use quotation marks of any kind: no ", no ', no `, no “ ”, no 「 」.
  If you need to reference words, write them without quotes.
- Do NOT include raw newline characters in any string value.
  Use \\n to represent a new paragraph inside the correction field.
- No trailing commas. No comments.

INPUT: prompt, reading, listening, response (transcript)

SCORING: 3 integers 0–4: delivery, language_use, topic_development
Strict: give 4 only if very strong; even if 4, include >=1 advanced improvement per dimension.

Content must match sources:
- Reading: proposal/change + reason(s)
- Listening: speaker stance + reason(s)
- Connection: explicitly link listening reasons to reading reasons

OUTPUT JSON KEYS (EXACT ORDER):
1) overall_score
2) dimension_scores
3) dimension_feedback
4) integrated_content_check
5) recommended_words
6) recommended_phrases
7) recommended_sentences
8) correction

overall_score: avg of 3 dimension_scores, rounded (0.5 up)

dimension_scores:
{"delivery":int,"language_use":int,"topic_development":int}

dimension_feedback:
{
 "delivery":{"score":int,"problems":[...],"evidence":[...],"fixes":[...]},
 "language_use":{"score":int,"problems":[...],"evidence":[...],"fixes":[...]},
 "topic_development":{"score":int,"problems":[...],"evidence":[...],"fixes":[...]}
}
Rules:
- problems/evidence/fixes arrays must be the same length in each dimension.
- each dimension must contain at least 1 item.

integrated_content_check:
{
 "reading_key_points":[string],
 "listening_key_points":[string],
 "missing_or_incorrect":[
   {"type":"reading"|"listening"|"connection","issue":string,"evidence":string,"fix":string}
 ]
}
Rules:
- key_points derive ONLY from reading/listening.
- missing_or_incorrect must contain at least 1 item even if strong (advanced precision/connection/conciseness).

recommended_words: EXACTLY 10 items, each {"en":"word","zh":"中文"}
recommended_phrases: EXACTLY 10 items, each {"en":"2-8 words","zh":"中文"}
recommended_sentences: EXACTLY 5 strings, each <=22 words, each uses >=1 phrase.

correction (MANDATORY STRING RULES):
- 90–110 words total
- max 2 short paragraphs, represented as a single JSON string using \\n between paragraphs
- Keep student meaning; fix grammar/clarity/organization/linking
- DO NOT invent facts outside reading/listening
- Do NOT mention scores/rubric/analysis

Now produce the JSON.
""".strip(),
"task3": """
TASK 3 (Integrated: Reading + Lecture) — Prompt (model_answer -> correction)

You are a TOEFL iBT Speaking Task 3 rater. Return STRICT JSON ONLY.
No markdown. No extra text.

INPUT: prompt, reading, listening, response (transcript)

SCORE (0–4 ints): Delivery, Language Use, Topic Development
Strict: 4 only if strong; even 4 must include >=1 advanced improvement per dimension.

Task 3 must:
- Reading: concept/definition (key feature[s])
- Listening: professor example(s)/details
- Connection: show how example demonstrates concept
Preferred order: concept -> example -> link

Rules:
- Judge ONLY response text
- Missing/incorrect concept/example/link or source confusion lowers Topic Development
- Avoid No major issue

Evidence rule (every item): <=10-word snippet WITHOUT double quotes, OR concrete symptom from response. Use N/A only if blank.

OUTPUT JSON KEYS (EXACT ORDER):
1) overall_score (avg 3 dims, round 0.5 up)
2) dimension_scores {"delivery":0-4,"language_use":0-4,"topic_development":0-4}
3) dimension_feedback (each: {"score":int,"problems":[...],"evidence":[...],"fixes":[...]}; arrays same length; >=1 item each)
4) integrated_content_check
   {
     "reading_key_points":[...] (ONLY from reading),
     "listening_key_points":[...] (ONLY from listening),
     "missing_or_incorrect":[{"type":"reading"|"listening"|"connection","issue":...,"evidence":...,"fix":...}]
   }
   missing_or_incorrect >=1 even if strong (advanced precision/linking/conciseness).
5) recommended_words (EXACTLY 10; {"en":"single word","zh":"简体中文释义"})
6) recommended_phrases (EXACTLY 10; {"en":"2-8 words","zh":"简体中文释义"})
7) recommended_sentences (EXACTLY 5 strings; <=22 words; each uses >=1 recommended_phrase)
8) correction
   - A revised high-scoring answer based on the student's response
   - Preserve original meaning and key ideas as much as possible
   - Fix grammar, word choice, clarity, organization, and missing links
   - DO NOT invent facts outside reading/listening
   - 90–110 words, max 2 short paragraphs
   - Must not mention scores/rubric/analysis

FINAL: valid JSON only; no extra keys; no trailing commas; no unescaped quotes.
""".strip(),
"task4": """
You are a TOEFL iBT Speaking Task 4 rater. Return STRICT JSON ONLY.
No markdown. No extra text.

INPUT: prompt, listening, response (transcript)

SCORE (0–4 ints): Delivery, Language Use, Topic Development
Strict: 4 only if strong; even 4 must include >=1 advanced improvement per dimension.

Task 4 must:
- Clear lecture main idea/topic
- Key points (usually 2) + how each is explained (example/detail)
Preferred order: main idea -> point 1 -> point 2 (or lecture order)
No invented facts; accurate attribution to lecture

Rules:
- Judge ONLY response text
- Missing/incorrect main idea or key supports lowers Topic Development
- Avoid No major issue

Evidence rule (every item): <=10-word snippet WITHOUT double quotes, OR concrete symptom from response. Use N/A only if blank.

OUTPUT JSON KEYS (EXACT ORDER):
1) overall_score (avg 3 dims, round 0.5 up)
2) dimension_scores {"delivery":0-4,"language_use":0-4,"topic_development":0-4}
3) dimension_feedback (each: {"score":int,"problems":[...],"evidence":[...],"fixes":[...]}; arrays same length; >=1 item each)
4) listening_content_check
   {
     "listening_key_points":[...] (ONLY from listening),
     "missing_or_incorrect":[{"type":"listening"|"organization","issue":...,"evidence":...,"fix":...}]
   }
   missing_or_incorrect >=1 even if strong (advanced precision/organization/conciseness).
5) recommended_words (EXACTLY 10; {"en":"single word","zh":"简体中文释义"})
6) recommended_phrases (EXACTLY 10; {"en":"2-8 words","zh":"简体中文释义"})
7) recommended_sentences (EXACTLY 5 strings; <=22 words; each uses >=1 recommended_phrase)
8) correction
   - A revised high-scoring answer based on the student's response
   - Preserve original meaning and key ideas as much as possible
   - Fix grammar, word choice, clarity, organization
   - DO NOT invent facts outside listening
   - 90–110 words, max 2 short paragraphs
   - Must not mention scores/rubric/analysis

FINAL: valid JSON only; no extra keys; no trailing commas; no unescaped quotes.
""".strip(),

     
  "followup": """
You are an expert TOEFL Speaking tutor and English learning coach.

Your task: answer the student's FOLLOW-UP QUESTION about a previous TOEFL task.

You are given:
- `reading_text`: the original TOEFL material or prompt (for context).
- `student_answer`: the student's original speaking response (transcribed text).
- `student_question`: the student's follow-up question. This question may be in English or Chinese.

Your goals:
1. Understand what the student is confused about (content, structure, vocabulary, grammar, logic, scoring, etc.).
2. Use the information in `reading_text` and `student_answer` ONLY as context. Do NOT re-evaluate or rescore the whole answer unless the question asks for it.
3. Give a clear, practical, and concise explanation that directly solves the student's doubt.

Language requirements:
- You MUST output two versions of your explanation:
  - One in English (for language learning and TOEFL context).
  - One in Chinese (for deeper understanding).
- The two versions should express the same core content, but natural in each language.

Style guidelines:
- Be encouraging and constructive, never harsh.
- Use simple, clear English in the English part (CEFR B2–C1 level).
- In the Chinese part, you can explain concepts more thoroughly if necessary.
- If the student’s question is vague, infer the most likely intention based on `student_answer` and give a helpful explanation instead of asking for clarification.

Output format:
Return ONLY valid JSON with this structure:

{
  "english_answer": "<Your explanation in English. Paragraphs allowed.>",
  "chinese_answer": "<Your explanation in Chinese. 段落说明均可。>"
}

Constraints:
- Do NOT include any keys other than "english_answer" and "chinese_answer".
- Do NOT add extra text outside the JSON.
- Do NOT mention that you are an AI model; just act as a human TOEFL tutor.
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
            max_tokens=2000
        )

        raw_output = response.choices[0].message.content.strip()
        print("this is raw_output", raw_output)
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
        分析 TOEFL Speaking Task 1（宽松校验版本：不强制补齐/不强制截断）
        :param question: 题目文本
        :param student_answer: 学生回答文本（语音转写后）
        :return: 结构化反馈 dict
        """

        required_keys = {
            "overall_score",
            "dimension_feedback",
            "recommended_words",
            "recommended_phrases",
            "recommended_sentences",
        }

        input_data = {"question": question, "student_answer": student_answer}

        def _coerce_list(x):
            """尽量把输出转成 list（宽松处理）"""
            if x is None:
                return []
            if isinstance(x, list):
                return x
            return [x]

        def _coerce_dict(x):
            return x if isinstance(x, dict) else {}

        def _validate_structure(result: dict) -> None:
            """最小必要检查：字段存在 + 类型基本正确（不限制长度、不补齐）"""
            if not isinstance(result, dict):
                raise ValueError("Model output is not a JSON object (dict).")

            missing = required_keys - set(result.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

            overall = result.get("overall_score")
            if overall is not None and (not isinstance(overall, int) or overall < 0 or overall > 4):
                raise ValueError("overall_score must be an integer between 0 and 4 (or null).")

            df = result.get("dimension_feedback")
            if not isinstance(df, dict):
                raise ValueError("dimension_feedback must be an object/dict.")

            for dim in ["delivery", "language_use", "topic_development"]:
                if dim not in df:
                    raise ValueError(f"dimension_feedback missing key: {dim}")

                d = df.get(dim)
                if not isinstance(d, dict):
                    raise ValueError(f"dimension_feedback.{dim} must be an object/dict.")

                score = d.get("score")
                if score is not None and (not isinstance(score, int) or score < 0 or score > 4):
                    raise ValueError(f"dimension_feedback.{dim}.score must be an integer 0-4 (or null).")

                # problems：允许空/多条，但应为 list（若为 str 在 normalize 里会转）
                problems = d.get("problems", [])
                if problems is not None and not isinstance(problems, list) and not isinstance(problems, str):
                    raise ValueError(f"dimension_feedback.{dim}.problems must be a list or string.")

            words = result.get("recommended_words")
            if not isinstance(words, list):
                raise ValueError("recommended_words must be a list.")
            for i, w in enumerate(words):
                if not isinstance(w, dict):
                    raise ValueError(f"recommended_words[{i}] must be an object with keys en/zh.")
                if "en" not in w or "zh" not in w:
                    raise ValueError(f"recommended_words[{i}] missing 'en' or 'zh'.")

            phrases = result.get("recommended_phrases")
            if not isinstance(phrases, list):
                raise ValueError("recommended_phrases must be a list.")
            for i, p in enumerate(phrases):
                if not isinstance(p, dict):
                    raise ValueError(f"recommended_phrases[{i}] must be an object with keys en/zh.")
                if "en" not in p or "zh" not in p:
                    raise ValueError(f"recommended_phrases[{i}] missing 'en' or 'zh'.")

            sents = result.get("recommended_sentences")
            if not isinstance(sents, list) and not isinstance(sents, str):
                raise ValueError("recommended_sentences must be a list (or string that can be coerced).")

            if isinstance(sents, list):
                for i, s in enumerate(sents):
                    if not isinstance(s, str):
                        raise ValueError(f"recommended_sentences[{i}] must be a string.")



        def _normalize_minimal(result: dict) -> dict:
            """
            最小规范化：只做类型兼容（不补齐、不截断）
            """
            if not isinstance(result, dict):
                return result

            df = _coerce_dict(result.get("dimension_feedback"))
            for dim in ["delivery", "language_use", "topic_development"]:
                d = _coerce_dict(df.get(dim))
                d["problems"] = _coerce_list(d.get("problems", []))

                # 若你 prompt 未来扩展 evidence/fixes，顺手兼容
                if "evidence" in d:
                    d["evidence"] = _coerce_list(d.get("evidence"))
                if "fixes" in d:
                    d["fixes"] = _coerce_list(d.get("fixes"))

                df[dim] = d

            result["dimension_feedback"] = df

            # recommended_sentences：若是字符串，转 list
            result["recommended_sentences"] = _coerce_list(result.get("recommended_sentences", []))

            return result

        try:
            user_message = f"""prompt:
{question}

response:
{student_answer}
"""

            result = self._call_llm(self.prompts["task1"], user_message)

            # 最小规范化（不补齐/不截断）
            result = _normalize_minimal(result)

            # 结构校验（字段存在 + 类型正确）
            _validate_structure(result)

            self._log_interaction("task1", input_data, result)
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task1 Analysis Failed: {error_msg}")
            self._log_interaction("task1", input_data, error=error_msg)
            raise

    def analyze_task2(
        self,
        reading_passage: str,
        listening_passage: str,
        question: str,
        student_answer: str,
    ) -> dict:
        """
        分析 TOEFL Speaking Task 2（Integrated – Campus）
        （宽松校验版本：不强制补齐/不强制截断，只做最小类型兼容）
        :param reading_passage: 阅读材料文本
        :param listening_passage: 听力材料文本（语音已转写）
        :param question: 题目文本（Task 2 的 prompt）
        :param student_answer: 学生回答文本（语音转写后）
        :return: 结构化反馈 dict
        """

        required_keys = {
            "overall_score",
            "dimension_feedback",
            "integrated_content_check",
            "recommended_words",
            "recommended_phrases",
            "recommended_sentences",
            "correction",
        }

        input_data = {
            "reading_passage": reading_passage,
            "listening_passage": listening_passage,
            "question": question,
            "student_answer": student_answer,
        }

        def _coerce_list(x):
            """尽量把输出转成 list（宽松处理）"""
            if x is None:
                return []
            if isinstance(x, list):
                return x
            return [x]

        def _coerce_dict(x):
            return x if isinstance(x, dict) else {}

        def _validate_structure(result: dict) -> None:
            """最小必要检查：字段存在 + 类型基本正确（不限制长度、不补齐）"""
            if not isinstance(result, dict):
                raise ValueError("Model output is not a JSON object (dict).")

            missing = required_keys - set(result.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

            overall = result.get("overall_score")
            if overall is not None and (not isinstance(overall, int) or overall < 0 or overall > 4):
                raise ValueError("overall_score must be an integer between 0 and 4 (or null).")

            df = result.get("dimension_feedback")
            if not isinstance(df, dict):
                raise ValueError("dimension_feedback must be an object/dict.")

            for dim in ["delivery", "language_use", "topic_development"]:
                if dim not in df:
                    raise ValueError(f"dimension_feedback missing key: {dim}")

                d = df.get(dim)
                if not isinstance(d, dict):
                    raise ValueError(f"dimension_feedback.{dim} must be an object/dict.")

                score = d.get("score")
                if score is not None and (not isinstance(score, int) or score < 0 or score > 4):
                    raise ValueError(f"dimension_feedback.{dim}.score must be an integer 0-4 (or null).")

                problems = d.get("problems", [])
                if problems is not None and not isinstance(problems, list) and not isinstance(problems, str):
                    raise ValueError(f"dimension_feedback.{dim}.problems must be a list or string.")

            icc = result.get("integrated_content_check")
            if not isinstance(icc, dict):
                raise ValueError("integrated_content_check must be an object/dict.")

            words = result.get("recommended_words")
            if not isinstance(words, list):
                raise ValueError("recommended_words must be a list.")
            for i, w in enumerate(words):
                if not isinstance(w, dict):
                    raise ValueError(f"recommended_words[{i}] must be an object with keys en/zh.")
                if "en" not in w or "zh" not in w:
                    raise ValueError(f"recommended_words[{i}] missing 'en' or 'zh'.")

            phrases = result.get("recommended_phrases")
            if not isinstance(phrases, list):
                raise ValueError("recommended_phrases must be a list.")
            for i, p in enumerate(phrases):
                if not isinstance(p, dict):
                    raise ValueError(f"recommended_phrases[{i}] must be an object with keys en/zh.")
                if "en" not in p or "zh" not in p:
                    raise ValueError(f"recommended_phrases[{i}] missing 'en' or 'zh'.")

            sents = result.get("recommended_sentences")
            if not isinstance(sents, list) and not isinstance(sents, str):
                raise ValueError("recommended_sentences must be a list (or string that can be coerced).")
            if isinstance(sents, list):
                for i, s in enumerate(sents):
                    if not isinstance(s, str):
                        raise ValueError(f"recommended_sentences[{i}] must be a string.")

            correction = result.get("correction")
            if correction is not None and not isinstance(correction, str):
                raise ValueError("correction must be a string (or null).")

        def _normalize_minimal(result: dict) -> dict:
            """
            最小规范化：只做类型兼容（不补齐、不截断）
            """
            if not isinstance(result, dict):
                return result

            df = _coerce_dict(result.get("dimension_feedback"))
            for dim in ["delivery", "language_use", "topic_development"]:
                d = _coerce_dict(df.get(dim))
                d["problems"] = _coerce_list(d.get("problems", []))
                if "evidence" in d:
                    d["evidence"] = _coerce_list(d.get("evidence"))
                if "fixes" in d:
                    d["fixes"] = _coerce_list(d.get("fixes"))
                df[dim] = d
            result["dimension_feedback"] = df

            icc = _coerce_dict(result.get("integrated_content_check"))
            if "reading_key_points" in icc:
                icc["reading_key_points"] = _coerce_list(icc.get("reading_key_points"))
            if "listening_key_points" in icc:
                icc["listening_key_points"] = _coerce_list(icc.get("listening_key_points"))
            if "missing_or_incorrect" in icc:
                icc["missing_or_incorrect"] = _coerce_list(icc.get("missing_or_incorrect"))
            result["integrated_content_check"] = icc

            result["recommended_sentences"] = _coerce_list(result.get("recommended_sentences", []))

            return result

        try:
            user_message = f"""prompt:
{question}

reading:
{reading_passage}

listening:
{listening_passage}

response:
{student_answer}
"""

            result = self._call_llm(self.prompts["task2"], user_message)

            result = _normalize_minimal(result)
            _validate_structure(result)

            self._log_interaction("task2", input_data, result)
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task2 Analysis Failed: {error_msg}")
            self._log_interaction("task2", input_data, error=error_msg)
            raise

    def analyze_task3(
        self,
        reading_passage: str,
        listening_passage: str,
        question: str,
        student_answer: str,
    ) -> dict:
        """
        分析 TOEFL Speaking Task 3（Integrated – Academic）
        （宽松校验版本：不强制补齐/不强制截断，只做最小类型兼容）
        :param reading_passage: 阅读材料文本（学术概念/理论等）
        :param listening_passage: 听力材料文本（教授讲解，语音已转写）
        :param question: 题目文本（Task 3 的 prompt）
        :param student_answer: 学生回答文本（语音转写后）
        :return: 结构化反馈 dict
        """

        required_keys = {
            "overall_score",
            "dimension_feedback",
            "integrated_content_check",
            "recommended_words",
            "recommended_phrases",
            "recommended_sentences",
            "correction",
        }

        input_data = {
            "reading_passage": reading_passage,
            "listening_passage": listening_passage,
            "question": question,
            "student_answer": student_answer,
        }

        def _coerce_list(x):
            """尽量把输出转成 list（宽松处理）"""
            if x is None:
                return []
            if isinstance(x, list):
                return x
            return [x]

        def _coerce_dict(x):
            return x if isinstance(x, dict) else {}

        def _validate_structure(result: dict) -> None:
            """最小必要检查：字段存在 + 类型基本正确（不限制长度、不补齐）"""
            if not isinstance(result, dict):
                raise ValueError("Model output is not a JSON object (dict).")

            missing = required_keys - set(result.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

            overall = result.get("overall_score")
            if overall is not None and (not isinstance(overall, int) or overall < 0 or overall > 4):
                raise ValueError("overall_score must be an integer between 0 and 4 (or null).")

            df = result.get("dimension_feedback")
            if not isinstance(df, dict):
                raise ValueError("dimension_feedback must be an object/dict.")

            for dim in ["delivery", "language_use", "topic_development"]:
                if dim not in df:
                    raise ValueError(f"dimension_feedback missing key: {dim}")

                d = df.get(dim)
                if not isinstance(d, dict):
                    raise ValueError(f"dimension_feedback.{dim} must be an object/dict.")

                score = d.get("score")
                if score is not None and (not isinstance(score, int) or score < 0 or score > 4):
                    raise ValueError(f"dimension_feedback.{dim}.score must be an integer 0-4 (or null).")

                problems = d.get("problems", [])
                if problems is not None and not isinstance(problems, list) and not isinstance(problems, str):
                    raise ValueError(f"dimension_feedback.{dim}.problems must be a list or string.")

            icc = result.get("integrated_content_check")
            if not isinstance(icc, dict):
                raise ValueError("integrated_content_check must be an object/dict.")

            words = result.get("recommended_words")
            if not isinstance(words, list):
                raise ValueError("recommended_words must be a list.")
            for i, w in enumerate(words):
                if not isinstance(w, dict):
                    raise ValueError(f"recommended_words[{i}] must be an object with keys en/zh.")
                if "en" not in w or "zh" not in w:
                    raise ValueError(f"recommended_words[{i}] missing 'en' or 'zh'.")

            phrases = result.get("recommended_phrases")
            if not isinstance(phrases, list):
                raise ValueError("recommended_phrases must be a list.")
            for i, p in enumerate(phrases):
                if not isinstance(p, dict):
                    raise ValueError(f"recommended_phrases[{i}] must be an object with keys en/zh.")
                if "en" not in p or "zh" not in p:
                    raise ValueError(f"recommended_phrases[{i}] missing 'en' or 'zh'.")

            sents = result.get("recommended_sentences")
            if not isinstance(sents, list) and not isinstance(sents, str):
                raise ValueError("recommended_sentences must be a list (or string that can be coerced).")
            if isinstance(sents, list):
                for i, s in enumerate(sents):
                    if not isinstance(s, str):
                        raise ValueError(f"recommended_sentences[{i}] must be a string.")

            correction = result.get("correction")
            if correction is not None and not isinstance(correction, str):
                raise ValueError("correction must be a string (or null).")

        def _normalize_minimal(result: dict) -> dict:
            """
            最小规范化：只做类型兼容（不补齐、不截断）
            """
            if not isinstance(result, dict):
                return result

            df = _coerce_dict(result.get("dimension_feedback"))
            for dim in ["delivery", "language_use", "topic_development"]:
                d = _coerce_dict(df.get(dim))
                d["problems"] = _coerce_list(d.get("problems", []))
                if "evidence" in d:
                    d["evidence"] = _coerce_list(d.get("evidence"))
                if "fixes" in d:
                    d["fixes"] = _coerce_list(d.get("fixes"))
                df[dim] = d
            result["dimension_feedback"] = df

            icc = _coerce_dict(result.get("integrated_content_check"))
            if "reading_key_points" in icc:
                icc["reading_key_points"] = _coerce_list(icc.get("reading_key_points"))
            if "listening_key_points" in icc:
                icc["listening_key_points"] = _coerce_list(icc.get("listening_key_points"))
            if "missing_or_incorrect" in icc:
                icc["missing_or_incorrect"] = _coerce_list(icc.get("missing_or_incorrect"))
            result["integrated_content_check"] = icc

            result["recommended_sentences"] = _coerce_list(result.get("recommended_sentences", []))

            return result

        try:
            user_message = f"""prompt:
{question}

reading:
{reading_passage}

listening:
{listening_passage}

response:
{student_answer}
"""

            result = self._call_llm(self.prompts["task3"], user_message)

            result = _normalize_minimal(result)
            _validate_structure(result)

            self._log_interaction("task3", input_data, result)
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task3 Analysis Failed: {error_msg}")
            self._log_interaction("task3", input_data, error=error_msg)
            raise

    def analyze_task4(
        self,
        listening_passage: str,
        question: str,
        student_answer: str,
    ) -> dict:
        """
        分析 TOEFL Speaking Task 4（Integrated – Academic Lecture）
        （宽松校验版本：不强制补齐/不强制截断，只做最小类型兼容）
        :param listening_passage: 听力材料文本（学术讲座/课堂内容，语音已转写）
        :param question: 题目文本（Task 4 的 prompt）
        :param student_answer: 学生回答文本（语音转写后）
        :return: 结构化反馈 dict
        """

        required_keys = {
            "overall_score",
            "dimension_feedback",
            "listening_content_check",
            "recommended_words",
            "recommended_phrases",
            "recommended_sentences",
            "correction",
        }

        input_data = {
            "listening_passage": listening_passage,
            "question": question,
            "student_answer": student_answer,
        }


        def _coerce_list(x):
            """尽量把输出转成 list（宽松处理）"""
            if x is None:
                return []
            if isinstance(x, list):
                return x
            return [x]

        def _coerce_dict(x):
            return x if isinstance(x, dict) else {}

        def _validate_structure(result: dict) -> None:
            """最小必要检查：字段存在 + 类型基本正确（不限制长度、不补齐）"""
            if not isinstance(result, dict):
                raise ValueError("Model output is not a JSON object (dict).")

            missing = required_keys - set(result.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

            overall = result.get("overall_score")
            if overall is not None and (not isinstance(overall, int) or overall < 0 or overall > 4):
                raise ValueError("overall_score must be an integer between 0 and 4 (or null).")

            df = result.get("dimension_feedback")
            if not isinstance(df, dict):
                raise ValueError("dimension_feedback must be an object/dict.")

            for dim in ["delivery", "language_use", "topic_development"]:
                if dim not in df:
                    raise ValueError(f"dimension_feedback missing key: {dim}")

                d = df.get(dim)
                if not isinstance(d, dict):
                    raise ValueError(f"dimension_feedback.{dim} must be an object/dict.")

                score = d.get("score")
                if score is not None and (not isinstance(score, int) or score < 0 or score > 4):
                    raise ValueError(f"dimension_feedback.{dim}.score must be an integer 0-4 (or null).")

                problems = d.get("problems", [])
                if problems is not None and not isinstance(problems, list) and not isinstance(problems, str):
                    raise ValueError(f"dimension_feedback.{dim}.problems must be a list or string.")

            lcc = result.get("listening_content_check")
            if not isinstance(lcc, dict):
                raise ValueError("listening_content_check must be an object/dict.")

            words = result.get("recommended_words")
            if not isinstance(words, list):
                raise ValueError("recommended_words must be a list.")
            for i, w in enumerate(words):
                if not isinstance(w, dict):
                    raise ValueError(f"recommended_words[{i}] must be an object with keys en/zh.")
                if "en" not in w or "zh" not in w:
                    raise ValueError(f"recommended_words[{i}] missing 'en' or 'zh'.")

            phrases = result.get("recommended_phrases")
            if not isinstance(phrases, list):
                raise ValueError("recommended_phrases must be a list.")
            for i, p in enumerate(phrases):
                if not isinstance(p, dict):
                    raise ValueError(f"recommended_phrases[{i}] must be an object with keys en/zh.")
                if "en" not in p or "zh" not in p:
                    raise ValueError(f"recommended_phrases[{i}] missing 'en' or 'zh'.")

            sents = result.get("recommended_sentences")
            if not isinstance(sents, list) and not isinstance(sents, str):
                raise ValueError("recommended_sentences must be a list (or string that can be coerced).")
            if isinstance(sents, list):
                for i, s in enumerate(sents):
                    if not isinstance(s, str):
                        raise ValueError(f"recommended_sentences[{i}] must be a string.")

            correction = result.get("correction")
            if correction is not None and not isinstance(correction, str):
                raise ValueError("correction must be a string (or null).")

        def _normalize_minimal(result: dict) -> dict:
            """
            最小规范化：只做类型兼容（不补齐、不截断）
            """
            if not isinstance(result, dict):
                return result

            df = _coerce_dict(result.get("dimension_feedback"))
            for dim in ["delivery", "language_use", "topic_development"]:
                d = _coerce_dict(df.get(dim))
                d["problems"] = _coerce_list(d.get("problems", []))
                if "evidence" in d:
                    d["evidence"] = _coerce_list(d.get("evidence"))
                if "fixes" in d:
                    d["fixes"] = _coerce_list(d.get("fixes"))
                df[dim] = d
            result["dimension_feedback"] = df

            lcc = _coerce_dict(result.get("listening_content_check"))
            if "listening_key_points" in lcc:
                lcc["listening_key_points"] = _coerce_list(lcc.get("listening_key_points"))
            if "missing_or_incorrect" in lcc:
                lcc["missing_or_incorrect"] = _coerce_list(lcc.get("missing_or_incorrect"))
            result["listening_content_check"] = lcc

            result["recommended_sentences"] = _coerce_list(result.get("recommended_sentences", []))

            return result

        try:
            user_message = f"""prompt:
{question}

listening:
{listening_passage}

response:
{student_answer}
"""

            result = self._call_llm(self.prompts["task4"], user_message)

            result = _normalize_minimal(result)
            _validate_structure(result)

            self._log_interaction("task4", input_data, result)
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task4 Analysis Failed: {error_msg}")
            self._log_interaction("task4", input_data, error=error_msg)
            raise
    def answer_followup_question(
            self,
            reading_text: str,
            student_answer: str,
            student_question: str,
            temperature: float = 0.3,
            log: bool = True,
        ) -> dict:
            """
            处理学生对某一题的追问，返回中英双语解答（字典形式）

            :param reading_text: 原始题目 / 阅读材料 / 听力文本
            :param student_answer: 学生最初的口语作答（文本版）
            :param student_question: 学生的追问（中/英文都可以）
            :param temperature: LLM 采样温度
            :param log: 是否写入日志文件
            :return: {
                "english_answer": "...",
                "chinese_answer": "..."
            }
            """
            system_prompt = self.prompts["followup"]
            
            user_content = (
                "Here is the context for the question.\n\n"
                f"=== READING TEXT / ORIGINAL PROMPT ===\n{reading_text}\n\n"
                f"=== STUDENT ANSWER (ORIGINAL RESPONSE) ===\n{student_answer}\n\n"
                f"=== STUDENT FOLLOW-UP QUESTION ===\n{student_question}\n"
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
            )

            raw_text = response.choices[0].message.content.strip()
            print("原始模型输出：", raw_text)
            # 尝试解析 JSON
            try:
                result = json.loads(raw_text)
            except json.JSONDecodeError:
                # 如果模型有轻微格式问题，可以做一点点兜底（也可以直接 raise）
                # 这里简单兜底成一个统一结构
                result = {
                    "english_answer": raw_text,
                    "chinese_answer": "模型返回的 JSON 格式不完全合法，已原样保留英文内容，请检查上游 prompt 或输出。"
                }

            # 写日志（可选）
            if log:
                log_record = {
                    "type": "followup",
                    "reading_text": reading_text,
                    "student_answer": student_answer,
                    "student_question": student_question,
                    "model_name": self.model_name,
                    "temperature": temperature,
                    "raw_response": raw_text,
                    "parsed_response": result,
                }
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
            return result


import os
import io
from urllib.parse import urljoin

from django.conf import settings

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


# =========================
# Globals
# =========================
_font_registered = False
_chinese_styles = None


# =========================
# Content Builder
# =========================
class PDFContentBuilder:
    """PDF内容构建器"""

    def __init__(self, styles):
        self.styles = styles
        self.story = []

    def add_title(self, text):
        self.story.append(Paragraph(str(text), self.styles['ChineseTitle']))
        self.add_spacer(8)

    def add_heading(self, text):
        self.story.append(Paragraph(str(text), self.styles['ChineseHeading']))
        self.add_spacer(6)

    def add_paragraph(self, text, style='ChineseNormal'):
        if text is None:
            return
        s = str(text).strip()
        if s:
            self.story.append(Paragraph(s, self.styles.get(style, self.styles['ChineseNormal'])))
            self.add_spacer(6)

    def add_spacer(self, height=12):
        self.story.append(Spacer(1, height))

    def get_content(self):
        return self.story


# =========================
# Style Manager (Apple-like)
# =========================
import os
from django.conf import settings
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# 全局变量（你原来就是这样缓存的）
_font_registered = False
_chinese_styles = None


# =========================
# Style Manager (Apple-like)
# =========================


# 全局变量（你原来就是这样缓存的）
_font_registered = False
_chinese_styles = None

class PDFStyleManager:
    """PDF样式管理器（回到你第一版：优先系统字体/项目字体）"""

    @staticmethod
    def _register_chinese_font():
        """注册中文字体"""
        global _font_registered, _chinese_styles
        if _font_registered and _chinese_styles:
            return _chinese_styles

        windows_font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
        ]

        font_path = None
        font_name = "ChineseFont"

        # 1) 查找系统字体
        for path in windows_font_paths:
            if os.path.exists(path):
                font_path = path
                break

        # 2) 系统字体找不到就用项目字体
        if not font_path:
            base_dir = getattr(settings, "BASE_DIR", "")
            project_font_path = os.path.join(base_dir, "font", "NotoSansSC-Regular.ttf")
            if os.path.exists(project_font_path):
                font_path = project_font_path

        if not font_path:
            raise FileNotFoundError("未找到可用的中文字体文件（系统字体与项目字体都不存在）")

        # 3) 注册字体
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception as e:
            raise Exception(f"字体注册失败: {e}")

        # 4) 创建中文样式
        base_styles = getSampleStyleSheet()

        chinese_styles = {
            "ChineseNormal": ParagraphStyle(
                name="ChineseNormal",
                fontName=font_name,
                fontSize=11,
                leading=16,
                spaceAfter=6,
                firstLineIndent=20,
            ),
            "ChineseMuted": ParagraphStyle(
                name="ChineseMuted",
                fontName=font_name,
                fontSize=10.5,
                leading=15,
                spaceAfter=4,
                textColor=colors.HexColor("#6E6E73"),
                firstLineIndent=0,
            ),
            "ChineseHeading": ParagraphStyle(
                name="ChineseHeading",
                fontName=font_name,
                fontSize=14,
                leading=18,
                spaceAfter=12,
                spaceBefore=12,
                textColor=colors.HexColor("#333333"),
            ),
            "ChineseTitle": ParagraphStyle(
                name="ChineseTitle",
                fontName=font_name,
                fontSize=16,
                leading=22,
                spaceAfter=18,
                spaceBefore=18,
                alignment=1,
                textColor=colors.HexColor("#000000"),
            ),
            "ChineseBold": ParagraphStyle(
                name="ChineseBold",
                fontName=font_name,
                fontSize=11,
                leading=16,
                spaceAfter=6,
                textColor=colors.HexColor("#222222"),
            ),
        }

        def safe_add(style_obj):
            try:
                base_styles.add(style_obj)
            except Exception:
                pass

        for style in chinese_styles.values():
            safe_add(style)

        _font_registered = True
        _chinese_styles = chinese_styles
        return chinese_styles

    @classmethod
    def get_styles(cls):
        """获取样式"""
        if not _font_registered or not _chinese_styles:
            return cls._register_chinese_font()
        return _chinese_styles

    @classmethod
    def get_style(cls, style_name="ChineseNormal"):
        """获取指定样式"""
        styles = cls.get_styles()
        return styles.get(style_name, styles["ChineseNormal"])


class FeedbackPDFGenerator:
    @staticmethod
    def _clean_text(text):
        if text is None:
            return ""
        return " ".join(str(text).split())

    @staticmethod
    def _join_bullets(items):
        if not items:
            return ""
        lines = []
        for x in items:
            s = str(x).strip()
            if s:
                lines.append(f"• {s}")
        return "<br/>".join(lines)

    @staticmethod
    def _divider(width):
        t = Table([[""]], colWidths=[width])
        t.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E5EA")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return t

    @staticmethod
    def _score_card(styles, width, overall, ds):
        muted = styles.get("ChineseMuted", styles.get("ChineseNormal"))
        title = styles.get("ChineseTitle", styles.get("ChineseNormal"))
        bold = styles.get("ChineseBold", styles.get("ChineseNormal"))

        overall_text = f"<b>{overall}/4</b>" if overall is not None else "<b>—</b>"
        delivery = ds.get("delivery", "—")
        language = ds.get("language_use", "—")
        topic = ds.get("topic_development", "—")

        left_w = min(170, max(150, width * 0.33))
        right_w = width - left_w

        data = [
            [Paragraph("Overall", muted), Paragraph(overall_text, title)],
            [Paragraph("Delivery", muted), Paragraph(str(delivery), bold)],
            [Paragraph("Language Use", muted), Paragraph(str(language), bold)],
            [Paragraph("Topic Development", muted), Paragraph(str(topic), bold)],
        ]

        table = Table(data, colWidths=[left_w, right_w])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F7")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E5EA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return table

    @staticmethod
    def _pairs_table(styles, width, pairs, header_left="EN", header_right="中文释义"):
        normal = styles.get("ChineseNormal")
        muted = styles.get("ChineseMuted", normal)

        left_w = width * 0.47
        right_w = width - left_w

        rows = [[Paragraph(header_left, muted), Paragraph(header_right, muted)]]

        for it in pairs:
            if not isinstance(it, dict):
                continue
            en = str(it.get("en", "")).strip()
            zh = str(it.get("zh", "")).strip()
            if not (en or zh):
                continue
            rows.append([Paragraph(en, normal), Paragraph(zh, normal)])

        table = Table(rows, colWidths=[left_w, right_w])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F5F7")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#E5E5EA")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#EFEFF4")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E5EA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return table

    @classmethod
    def _infer_task_no(cls, task, task_no=None):
        """兼容不同模型字段命名：task_no / task_number / task_type 等"""
        if task_no is not None:
            return int(task_no)

        for attr in ("task_no", "task_number", "tasktype", "task_type", "task", "type"):
            v = getattr(task, attr, None)
            if v is None:
                continue
            s = str(v).lower()
            for n in (1, 2, 3, 4):
                if s == str(n) or f"task{n}" in s or f"_{n}" in s:
                    return n

        return 1

    @classmethod
    def _pick_task_title(cls, task, taskname=None):
        """优先用外部传入 taskname，否则从 task 常见字段兜底"""
        if taskname:
            return str(taskname)

        for attr in ("name", "task_name", "taskname", "title", "topic", "label"):
            v = getattr(task, attr, None)
            if v:
                return str(v)

        return f"ID {getattr(task, 'id', '')}"

    @classmethod
    def _build_dim_scores_from_feedback(cls, feedback: dict) -> dict:
        """
        兼容：如果没有 dimension_scores，就从 dimension_feedback 提取
        """
        if not isinstance(feedback, dict):
            return {}

        ds = feedback.get("dimension_scores")
        if isinstance(ds, dict) and ds:
            return ds

        df = feedback.get("dimension_feedback", {})
        if not isinstance(df, dict):
            return {}

        def pick(dim_key):
            d = df.get(dim_key) or {}
            if isinstance(d, dict):
                return d.get("score", "—")
            return "—"

        return {
            "delivery": pick("delivery"),
            "language_use": pick("language_use"),
            "topic_development": pick("topic_development"),
        }

    @classmethod
    def generate_pdf_report2(cls, task, student_answer, feedback, task_no=None, taskname=None):
        styles = PDFStyleManager.get_styles()

        tno = cls._infer_task_no(task, task_no=task_no)

        filename = f"task{tno}_{task.id}_report.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        pdf_io = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_io,
            pagesize=A4,
            topMargin=36,
            bottomMargin=36,
            leftMargin=44,
            rightMargin=44,
        )

        builder = PDFContentBuilder(styles)

        # ✅ Title：支持外部传 taskname + 多字段兜底
        task_title = cls._pick_task_title(task, taskname=taskname)
        builder.add_title(f"TOEFL 口语 Task {tno} 评分报告：{task_title}")

        # ✅ 题目内容：兼容 Task1/2/3/4（reading + listening transcript）
        question_text = cls._clean_text(getattr(task, "questiontext", "") or "")
        reading_text = cls._clean_text(getattr(task, "readingtext", "") or "")
        listening_text = cls._clean_text(
            getattr(task, "listeningtext", "") or getattr(task, "listening_text", "") or ""
        )

        if question_text or reading_text or listening_text:
            builder.add_heading("题目内容")

            if question_text:
                builder.add_paragraph("Prompt", style="ChineseMuted")
                builder.add_paragraph(question_text, style="ChineseNormal")
                builder.add_spacer(6)

            if reading_text:
                builder.add_paragraph("Reading", style="ChineseMuted")
                builder.add_paragraph(reading_text, style="ChineseNormal")
                builder.add_spacer(6)

            if listening_text:
                builder.add_paragraph("Listening Transcript", style="ChineseMuted")
                builder.add_paragraph(listening_text, style="ChineseNormal")

        builder.story.append(cls._divider(doc.width))

        # -------------------------
        # Student Answer
        # -------------------------
        builder.add_heading("你的回答")
        student_answer_clean = cls._clean_text(student_answer) or "（无回答）"
        builder.add_paragraph(student_answer_clean, style="ChineseNormal")

        # -------------------------
        # ✅ Correction（满分修正版，紧跟学生回答）
        # -------------------------
        correction_text = ""
        if isinstance(feedback, dict):
            correction_text = cls._clean_text(feedback.get("correction", "") or "")

        builder.add_spacer(6)
        builder.add_heading("满分修正版（基于你的回答）")
        builder.add_paragraph(
            "在尽量保留你原意的基础上，优化表达、逻辑与语言准确性。",
            style="ChineseMuted",
        )
        builder.add_paragraph(
            correction_text if correction_text else "（暂无）",
            style="ChineseNormal" if correction_text else "ChineseMuted",
        )

        builder.story.append(cls._divider(doc.width))

        # -------------------------
        # Scores
        # -------------------------
        overall = feedback.get("overall_score", None) if isinstance(feedback, dict) else None
        dim_scores = cls._build_dim_scores_from_feedback(feedback)
        dim_fb = feedback.get("dimension_feedback", {}) if isinstance(feedback, dict) else {}
        dim_fb = dim_fb or {}

        builder.add_heading("评分结果")
        builder.story.append(cls._score_card(styles, doc.width, overall, dim_scores))
        builder.add_spacer(6)

        def render_dimension(title_cn, key):
            data = dim_fb.get(key, {}) if isinstance(dim_fb, dict) else {}
            score = data.get("score", None) if isinstance(data, dict) else None

            problems = data.get("problems", []) if isinstance(data, dict) else []
            evidence = data.get("evidence", []) if isinstance(data, dict) else []
            fixes = data.get("fixes", []) if isinstance(data, dict) else []

            score_text = f"{score}/4" if score is not None else "—/4"
            builder.add_heading(f"{title_cn}  {score_text}")

            builder.add_paragraph("Issues & Improvements", style="ChineseMuted")
            p_text = cls._join_bullets(problems)
            builder.add_paragraph(
                p_text if p_text else "（暂无）",
                style="ChineseNormal" if p_text else "ChineseMuted",
            )

            if evidence:
                builder.add_paragraph("Evidence", style="ChineseMuted")
                e_text = cls._join_bullets(evidence)
                builder.add_paragraph(
                    e_text if e_text else "（暂无）",
                    style="ChineseNormal" if e_text else "ChineseMuted",
                )

            if fixes:
                builder.add_paragraph("Actionable Fixes", style="ChineseMuted")
                f_text = cls._join_bullets(fixes)
                builder.add_paragraph(
                    f_text if f_text else "（暂无）",
                    style="ChineseNormal" if f_text else "ChineseMuted",
                )

            builder.story.append(cls._divider(doc.width))

        render_dimension("Delivery（表达）", "delivery")
        render_dimension("Language Use（语言运用）", "language_use")
        render_dimension("Topic Development（内容展开）", "topic_development")

        # -------------------------
        # Reference answers（有就显示）
        # -------------------------
        answer1 = cls._clean_text(getattr(task, "answertext1", "") or "")
        answer2 = cls._clean_text(getattr(task, "answertext2", "") or "")
        if answer1 or answer2:
            builder.add_heading("参考答案")
            builder.add_paragraph("参考答案1", style="ChineseMuted")
            builder.add_paragraph(answer1 if answer1 else "无", style="ChineseNormal")
            builder.add_spacer(4)
            builder.add_paragraph("参考答案2", style="ChineseMuted")
            builder.add_paragraph(answer2 if answer2 else "无", style="ChineseNormal")
            builder.story.append(cls._divider(doc.width))

        # -------------------------
        # Recommendations
        # -------------------------
        words = feedback.get("recommended_words", []) if isinstance(feedback, dict) else []
        if words:
            builder.add_heading("推荐单词")
            builder.story.append(
                cls._pairs_table(styles, doc.width, words[:10], header_left="Word", header_right="中文释义")
            )
            builder.story.append(cls._divider(doc.width))

        phrases = feedback.get("recommended_phrases", []) if isinstance(feedback, dict) else []
        if phrases:
            builder.add_heading("推荐短语")
            builder.story.append(
                cls._pairs_table(styles, doc.width, phrases[:10], header_left="Phrase", header_right="中文释义")
            )
            builder.story.append(cls._divider(doc.width))

        sentences = feedback.get("recommended_sentences", []) if isinstance(feedback, dict) else []
        if sentences:
            builder.add_heading("推荐句子")
            for i, s in enumerate(sentences[:5], 1):
                s_clean = cls._clean_text(s)
                if s_clean:
                    builder.add_paragraph(f"{i}. {s_clean}", style="ChineseNormal")
            builder.add_spacer(6)

        doc.build(builder.get_content())

        with open(filepath, "wb") as f:
            f.write(pdf_io.getvalue())

        return urljoin(settings.MEDIA_URL, f"reports/{filename}")

    @classmethod
    def generate_pdf_report(cls, task, student_answer, feedback, task_no=None, taskname=None):
        return cls.generate_pdf_report2(
            task=task,
            student_answer=student_answer,
            feedback=feedback,
            task_no=task_no,
            taskname=taskname,
        )





def generate_pdf_report2(task, student_answer, feedback, task_no="1", taskname="任务1"):
    return FeedbackPDFGenerator.generate_pdf_report2(task, student_answer, feedback, task_no=task_no, taskname=taskname)
