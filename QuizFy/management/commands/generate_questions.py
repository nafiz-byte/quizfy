from django.core.management.base import BaseCommand
from QuizFy.models import Topic, Question
from QuizFy.gemini import generate_questions

class Command(BaseCommand):
    help = 'Gemini দিয়ে প্রশ্ন জেনারেট করো'

    def handle(self, *args, **kwargs):
        topics = Topic.objects.filter(is_hot=True)

        if not topics.exists():
            # Default topic বানাও
            topic = Topic.objects.create(name="FIFA World Cup 2026", is_hot=True)
            topics = [topic]

        for topic in topics:
            self.stdout.write(f'⏳ {topic.name} এর জন্য প্রশ্ন বানাচ্ছি...')
            questions = generate_questions(topic.name, count=30)

            for q in questions:
                Question.objects.create(
                    topic=topic,
                    question_text=q['question'],
                    option_a=q['options']['a'],
                    option_b=q['options']['b'],
                    option_c=q['options']['c'],
                    option_d=q['options']['d'],
                    correct_option=q['answer'],
                )

            self.stdout.write(f'✅ {topic.name} — {len(questions)}টি প্রশ্ন সেভ হয়েছে')