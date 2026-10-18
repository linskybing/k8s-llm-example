# Ask any LLM server here on port 8000 (first: kubectl port-forward job/<job> 8000:8000 &)
#   python3 k8s-llm-example/chat.py "Hi"
import sys

from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")
r = client.chat.completions.create(
    model="meta-llama/Llama-3.2-1B-Instruct",
    messages=[{"role": "user", "content": sys.argv[1] if len(sys.argv) > 1 else "Hi"}],
)
print(r.choices[0].message.content)
