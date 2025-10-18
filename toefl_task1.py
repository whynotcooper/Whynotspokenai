import os
import json
import re
from datetime import datetime
from openai import OpenAI

class ToeflTaskAnalysisPipeline:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com/v1", log_file="toefl_analysis_log.jsonl"):
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
""".strip()
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