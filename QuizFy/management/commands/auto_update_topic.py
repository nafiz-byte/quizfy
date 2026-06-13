from django.core.management.base import BaseCommand
from QuizFy.models import Topic, Question
from QuizFy.gemini import generate_questions
import requests, os

def get_hot_topic():
    api_key = "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"
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "এখন বাংলাদেশে সবচেয়ে আলোচিত ১টি বিষয় বলো যেটা নিয়ে কুইজ হতে পারে। শুধু বিষয়ের নাম দাও।"}]
        }
    )
    return response.json()['choices'][0]['message']['content'].strip()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Topic.objects.all().update(is_hot=False)
        topic_name = get_hot_topic()
        self.stdout.write(f'🔥 নতুন টপিক: {topic_name}')
        topic, _ = Topic.objects.get_or_create(name=topic_name, defaults={'is_hot': True})
        topic.is_hot = True
        topic.save()
        questions = generate_questions(topic_name, count=30)
        for q in questions:
            Question.objects.get_or_create(
                topic=topic, question_text=q['question'],
                defaults={'option_a': q['options']['a'], 'option_b': q['options']['b'], 'option_c': q['options']['c'], 'option_d': q['options']['d'], 'correct_option': q['answer']}
            )
        self.stdout.write(f'✅ {len(questions)}টি প্রশ্ন সেভ হয়েছে')