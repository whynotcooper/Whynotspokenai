import os
from pathlib import Path
from openai import OpenAI

import os
from pathlib import Path
from openai import OpenAI

class TextAnalysisPipeline:
    def __init__(self, api_key="sk-feb07e3e5a804d64a7ffdd0305527377", base_url="https://api.deepseek.com/v1", log_file="session_log.jsonl"):
        """
        初始化文本分析管道
        """
        base_url = base_url.strip()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

    def short_response(self, transcribed_text):
        """简短、自然的日常交流回应"""
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

    def _generate_three_parts(self, system_prompt, user_prompt):
        """生成并解析：reasoning + answer1 + answer2"""
        rsp = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            stream=False
        )
        output = rsp.choices[0].message.content.strip()

        try:
            if "Reasoning:" in output and "Answer 1:" in output and "Answer 2:" in output:
                reasoning_part = output.split("Reasoning:")[1].split("Answer 1:")[0].strip()
                answer1_part = output.split("Answer 1:")[1].split("Answer 2:")[0].strip()
                answer2_part = output.split("Answer 2:")[1].strip()
                return {
                    "reasoning": reasoning_part,
                    "answer1": answer1_part,
                    "answer2": answer2_part
                }
            else:
                parts = [p.strip() for p in output.split("\n\n") if p.strip()]
                if len(parts) >= 3:
                    return {
                        "reasoning": parts[0],
                        "answer1": parts[1],
                        "answer2": parts[2]
                    }
                else:
                    return {
                        "reasoning": "Failed to parse reasoning.",
                        "answer1": output,
                        "answer2": output
                    }
        except Exception as e:
            print(f"Warning: Parsing failed. Error: {e}")
            return {
                "reasoning": f"Parsing error: {str(e)}",
                "answer1": output,
                "answer2": output
            }

    def task1_reply(self, reading_text):
        """TOEFL Task 1: Independent Speaking"""
        system = (
            "You are a TOEFL expert. Generate a response with THREE parts for Independent Speaking Task 1.\n\n"
            "Part 1 - Reasoning:\n"
            "Explain your approach: What is the topic? What opinion will you take? Why is this stance clear and supportable? "
            "How will you structure your response (e.g., opinion → reason 1 + example → reason 2 + example)?\n\n"
            "Part 2 & 3 - Answers:\n"
            "Generate TWO spoken responses (Answer 1 and Answer 2) that:\n"
            "- Are 80–100 words long, suitable for a 45-second speech.\n"
            "- Express a clear opinion with two well-developed reasons and examples.\n"
            "- Use natural, fluent academic spoken English.\n"
            "- Have identical meaning but different vocabulary, sentence structures, and transitions.\n"
            "- Do NOT invent facts beyond the topic.\n\n"
            "Output format:\n"
            "Reasoning:\n[...]\n\nAnswer 1:\n[...]\n\nAnswer 2:\n[...]"
        )
        user = f"Topic:\n{reading_text}"
        return self._generate_three_parts(system, user)

    def task2_reply(self, reading_text, listening_text, question_text):
        """TOEFL Task 2: Campus Situation"""
        system = (
            "You are a TOEFL expert. Generate a response with THREE parts for Integrated Speaking Task 2.\n\n"
            "Part 1 - Reasoning:\n"
            "Explain how you will use the reading (which presents a campus policy or proposal), the listening (a student's opinion), "
            "and the specific question prompt to construct your response. Emphasize that you must summarize the reading, "
            "state the speaker’s stance (agree/disagree), and explain their two reasons — all while directly addressing the question.\n\n"
            "Part 2 & 3 - Answers:\n"
            "Generate TWO spoken responses that:\n"
            "- Begin by briefly summarizing the reading.\n"
            "- Clearly state the speaker’s opinion as given in the listening.\n"
            "- Explain both reasons from the listening with relevant details.\n"
            "- Directly respond to the question in 'question.txt'.\n"
            "- Are 100–120 words, natural for a 60-second speech.\n"
            "- Use varied sentence structures and transitions between the two answers.\n"
            "- NEVER add, omit, or distort information from the sources.\n\n"
            "Output format:\n"
            "Reasoning:\n[...]\n\nAnswer 1:\n[...]\n\nAnswer 2:\n[...]"
        )
        user = f"Reading (campus announcement):\n{reading_text}\n\nListening (student's opinion):\n{listening_text}\n\nQuestion:\n{question_text}"
        return self._generate_three_parts(system, user)

    def task3_reply(self, reading_text, listening_text, question_text):
        """TOEFL Task 3: Academic Concept + Example"""
        system = (
            "You are a TOEFL expert. Generate a response with THREE parts for Integrated Speaking Task 3.\n\n"
            "Part 1 - Reasoning:\n"
            "Explain how you will define the academic concept from the reading, then connect it to the lecture example, "
            "while ensuring your response directly addresses the instructions in the question. "
            "Highlight the illustrative relationship between concept and example.\n\n"
            "Part 2 & 3 - Answers:\n"
            "Generate TWO spoken responses that:\n"
            "- Clearly define the academic concept from the reading.\n"
            "- Accurately describe how the lecture example illustrates or demonstrates that concept.\n"
            "- Explicitly follow the task described in the question (e.g., 'explain how the example relates to the concept').\n"
            "- Are 100–120 words, suitable for a 60-second oral response.\n"
            "- Use different phrasing, vocabulary, and sentence patterns in the two versions.\n"
            "- Remain strictly faithful to the provided materials.\n\n"
            "Output format:\n"
            "Reasoning:\n[...]\n\nAnswer 1:\n[...]\n\nAnswer 2:\n[...]"
        )
        user = f"Reading (academic concept):\n{reading_text}\n\nListening (lecture example):\n{listening_text}\n\nQuestion:\n{question_text}"
        return self._generate_three_parts(system, user)

    def task4_reply(self, listening_text, question_text):
        """TOEFL Task 4: Academic Lecture Summary"""
        system = (
            "You are a TOEFL expert. Generate a response with THREE parts for Integrated Speaking Task 4.\n\n"
            "Part 1 - Reasoning:\n"
            "Explain how you will identify the lecture’s main topic and its two key supporting points with examples, "
            "while adhering to the specific instructions in the question (e.g., 'describe the two strategies...'). "
            "Describe your strategy for organizing the summary logically (e.g., main idea → point 1 + example → point 2 + example).\n\n"
            "Part 2 & 3 - Answers:\n"
            "Generate TWO spoken responses that:\n"
            "- State the lecture’s main topic as framed by the question.\n"
            "- Summarize both key points and their examples accurately.\n"
            "- Directly address the task in the question (e.g., 'explain the two processes...').\n"
            "- Are 100–120 words, natural for a 60-second oral summary.\n"
            "- Use cohesive devices and varied sentence structures across the two versions.\n"
            "- Avoid personal opinions or external knowledge.\n\n"
            "Output format:\n"
            "Reasoning:\n[...]\n\nAnswer 1:\n[...]\n\nAnswer 2:\n[...]"
        )
        user = f"Lecture transcript:\n{listening_text}\n\nQuestion:\n{question_text}"
        return self._generate_three_parts(system, user)


def process_all_tpos(base_dir="data", pipeline=None):
    """
    自动遍历 data/ 下的 task1~task4，处理每个 TPO55~TPO75 子目录。
    文件命名规范（首字母大写）：
        - Reading.txt
        - Listening.txt
        - Question.txt
    输出：在每个 TPO 目录下生成 reasoning.txt, answer1.txt, answer2.txt
    """
    if pipeline is None:
        raise ValueError("Pipeline 未传入，请先初始化 TextAnalysisPipeline 实例。")

    tasks = ["task1", "task2", "task3", "task4"]
    
    for task_name in tasks:
        task_dir = Path(base_dir) / task_name
        if not task_dir.exists():
            print(f"⚠️  {task_dir} 不存在，跳过 {task_name}。")
            continue
        
        print(f"\n🟦 正在处理 {task_name}...")

        # 获取所有 TPO 文件夹（TPO55 到 TPO75）
        tpo_dirs = [d for d in task_dir.iterdir() if d.is_dir() and d.name.startswith("TPO")]
        
        for tpo_path in sorted(tpo_dirs):  # 按名称排序，如 TPO55, TPO56...
            tpo_name = tpo_path.name
            print(f"  📁 处理 {tpo_name}...")

            # 读取文件（注意首字母大写）
            reading_file = tpo_path / "Reading.txt"
            listening_file = tpo_path / "listening.txt"
            question_file = tpo_path / "question.txt"

            reading_text = ""
            listening_text = ""
            question_text = ""

            if reading_file.exists():
                with open(reading_file, 'r', encoding='utf-8') as f:
                    reading_text = f.read().strip()
            else:
                if task_name in ["task1", "task2", "task3"]:
                    print(f"    ⚠️  Reading.txt 缺失（{task_name} 必需）")

            if listening_file.exists():
                with open(listening_file, 'r', encoding='utf-8') as f:
                    listening_text = f.read().strip()
            else:
                if task_name in ["task2", "task3", "task4"]:
                    print(f"    ⚠️  Listening.txt 缺失（{task_name} 必需）")

            if question_file.exists():
                with open(question_file, 'r', encoding='utf-8') as f:
                    question_text = f.read().strip()
            else:
                if task_name in ["task2", "task3", "task4"]:
                    print(f"    ⚠️  Question.txt 缺失（{task_name} 必需）")

            # 调用对应任务
            try:
                if task_name == "task1":
                    if not reading_text:
                        print(f"    ❌ {tpo_name}: 缺少 Reading.txt，跳过。")
                        continue
                    result = pipeline.task1_reply(reading_text)
                
                elif task_name == "task2":
                    if not reading_text or not listening_text or not question_text:
                        print(f"    ❌ {tpo_name}: 缺少必要文件，跳过。")
                        continue
                    result = pipeline.task2_reply(reading_text, listening_text, question_text)
                
                elif task_name == "task3":
                    if not reading_text or not listening_text or not question_text:
                        print(f"    ❌ {tpo_name}: 缺少必要文件，跳过。")
                        continue
                    result = pipeline.task3_reply(reading_text, listening_text, question_text)
                
                elif task_name == "task4":
                    if not listening_text or not question_text:
                        print(f"    ❌ {tpo_name}: 缺少 Listening.txt 或 Question.txt，跳过。")
                        continue
                    result = pipeline.task4_reply(listening_text, question_text)
                
                else:
                    print(f"    ❌ 未知任务：{task_name}")
                    continue

                # 写入三个输出文件
                (tpo_path / "reasoning.txt").write_text(result["reasoning"].strip(), encoding="utf-8")
                (tpo_path / "answer1.txt").write_text(result["answer1"].strip(), encoding="utf-8")
                (tpo_path / "answer2.txt").write_text(result["answer2"].strip(), encoding="utf-8")
                print(f"    ✅ {tpo_name}: 已生成 reasoning.txt, answer1.txt, answer2.txt")

            except Exception as e:
                print(f"    ❌ {tpo_name}: 处理失败 — {e}")


# ========================
# 主程序入口
# ========================
if __name__ == "__main__":
    # 初始化 Pipeline（请确保 API Key 正确）
    pipeline = TextAnalysisPipeline(
        api_key="sk-feb07e3e5a804d64a7ffdd0305527377",
        base_url="https://api.deepseek.com/v1"
    )

    # 批量处理所有 TPO
    process_all_tpos(base_dir="data", pipeline=pipeline)