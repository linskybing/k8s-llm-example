# Ask the LLM from llm/job.yaml (first: kubectl port-forward job/llm-exp 8000:8000 &)
#   python3 k8s-n150-example/llm/chat.py "Hi"
import sys

from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")
r = client.chat.completions.create(
    model="meta-llama/Llama-3.2-1B-Instruct",
    messages=[{"role": "user", "content": sys.argv[1] if len(sys.argv) > 1 else "Hi"}],
)
print(r.choices[0].message.content)
