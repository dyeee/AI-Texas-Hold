from openai import OpenAI

API_BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"

class LLMClient:
    def __init__(self, model="deepseek:7b", api_key=API_KEY, base_url=API_BASE_URL):
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def chat(self, messages, model=None):
        try:
            use_model = model or self.model
            print(f"LLM请求 ({use_model}): {messages}")
            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages
            )
            if response.choices:
                message = response.choices[0].message
                content = message.content if message.content else ""
                reasoning_content = getattr(message, "reasoning_content", "")
                print(f"LLM推理内容: {content}")
                return content, reasoning_content
            return "", ""
        except Exception as e:
            print(f"❌ LLM调用出错: {str(e)}")
            return "", ""

if __name__ == "__main__":
    llm = LLMClient()
    messages = [
        {"role": "user", "content": "你好"}
    ]
    response = llm.chat(messages)
    print(f"响应: {response}")