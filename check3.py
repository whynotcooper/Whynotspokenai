import os
from openai import OpenAI

def call_deepseek_api(api_key, base_url, model, messages):
    """
    调用 DeepSeek API
    :param api_key: DeepSeek API 密钥
    :param base_url: DeepSeek API 基础 URL
    :param model: 使用的模型
    :param messages: 与 API 交互的消息列表
    :return: API 的响应
    """
    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        # 调用 API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.0,
            max_tokens=600,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # 配置 API 密钥和基础 URL
    api_key = "sk-feb07e3e5a804d64a7ffdd0305527377"  # 使用你提供的密钥
    base_url = "https://api.deepseek.com/v1"  # 使用你提供的基础 URL

    # 定义模型和消息
    model = "deepseek-chat"  # 使用 deepseek-chat 模型
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]

    # 调用 API
    response = call_deepseek_api(api_key, base_url, model, messages)

    # 打印响应
    if response:
        print("Response from DeepSeek API:")
        print(response)