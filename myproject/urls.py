from django.urls import path
from QuizFy import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/question/', views.quiz_question, name='quiz_question'),
    path('quiz/result/', views.quiz_result, name='quiz_result'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
path('robi/notify/', views.robi_notify, name='robi_notify'),
path('robi/subscription/', views.robi_subscription, name='robi_subscription'),
path('Unsubscribe/', views.unsubscribe, name='Unsubscribe'),
]
