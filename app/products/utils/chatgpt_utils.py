import requests
from django.conf import settings
import re

def clean_description(text):
    return re.split(r"(## Step|The final answer:)", text)[0].strip()

def generate_product_description(name):
    prompt = f"""
Тебе нужно найти в открых источниках описание пива «{name}».
Структурировать информацию и привести в легкочитаемый вид.
Упомяни вкус, аромат и кому он подойдет. Разбей на абзацы.
"""
    response = requests.post(
        "https://api.together.xyz/inference",
        headers={
            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "prompt": prompt.strip(),
            "max_tokens": 600,
            "temperature": 0.7,
        },
    )
    data = response.json()
    return clean_description(data["output"]["choices"][0]["text"])
