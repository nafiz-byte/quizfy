import requests
import json, re, time
import os

def generate_questions(topic="FIFA World Cup 2026", count=15):

    api_key = os.environ.get("OPENROUTER_API_KEY", "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")
    prompt = f"""
তুমি একটি বাংলা কুইজ অ্যাপের প্রশ্ন তৈরি করো।
'{topic}' বিষয়ে {count}টি MCQ প্রশ্ন বাংলায় তৈরি করো।

শুধু এই JSON format এ দাও, আর কিছু না:
[
  {{
    "question": "প্রশ্ন এখানে",
    "options": {{"a": "অপশন ১", "b": "অপশন ২", "c": "অপশন ৩", "d": "অপশন ৪"}},
    "answer": "a"
  }}
]
"""
    for attempt in range(3):  # ৩ বার চেষ্টা করবে
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/auto",

                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        print(f"Response: {data}")

        if 'choices' in data:
            text = data['choices'][0]['message']['content']
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())

        print(f"⚠️ চেষ্টা {attempt+1} ব্যর্থ, ৩ সেকেন্ড অপেক্ষা...")
        time.sleep(3)

    return []

