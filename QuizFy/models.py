from django.db import models


class Player(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    is_charged = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone


class OTPSession(models.Model):
    phone = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} - {self.otp_code}"


class Topic(models.Model):
    name = models.CharField(max_length=100)
    is_hot = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1)

    def __str__(self):
        return self.question_text[:60]

class QuizSession(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=15)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)

    @property
    def percentage(self):
        return round((self.score / self.total) * 100) if self.total > 0 else 0