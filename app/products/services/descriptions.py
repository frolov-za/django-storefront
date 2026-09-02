import re

from products.integrations.together import generate_completion


def generate_product_description(name):
    prompt = f"""
Тебе нужно найти в открытых источниках описание пива «{name}».
Структурируй информацию и изложи её в лёгком для чтения виде.
Упомяни вкус, аромат и кому напиток подойдёт. Разбей ответ на абзацы.
"""
    return clean_description(generate_completion(prompt.strip()))


def clean_description(text):
    return re.split(r"(## Step|The final answer:)", text)[0].strip()
