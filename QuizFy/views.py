from django.shortcuts import render, redirect
from django.utils import timezone
import random
from .models import Player, OTPSession, Topic, Question, QuizSession

def landing(request):
    return render(request, 'index.html')

def send_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone.startswith('018') or len(phone) != 11:
            return redirect('landing')
        otp = str(random.randint(100000, 999999))
        OTPSession.objects.filter(phone=phone).delete()
        OTPSession.objects.create(phone=phone, otp_code=otp)
        print(f"📱 OTP for {phone}: {otp}")
        request.session['otp_phone'] = phone
        return redirect('verify_otp')
    return redirect('landing')

def verify_otp(request):
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('landing')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        try:
            session = OTPSession.objects.get(phone=phone, otp_code=entered_otp, is_used=False)
            diff = timezone.now() - session.created_at
            if diff.seconds > 300:
                return redirect('landing')
            session.is_used = True
            session.save()
            player, _ = Player.objects.get_or_create(phone=phone)
            player.is_verified = True
            player.is_charged = True
            player.save()
            request.session['player_phone'] = phone
            request.session.pop('otp_phone', None)
            return redirect('quiz')
        except OTPSession.DoesNotExist:
            return render(request, 'verify_otp.html', {'phone': phone, 'error': 'ভুল OTP'})
    return render(request, 'verify_otp.html', {'phone': phone})

def quiz(request):
    phone = request.session.get('player_phone')
    if not phone:
        return redirect('landing')
    topic = Topic.objects.filter(is_hot=True).first()
    questions = list(Question.objects.filter(topic=topic))
    random.shuffle(questions)
    questions = questions[:15]
    request.session['quiz_questions'] = [q.id for q in questions]
    request.session['quiz_index'] = 0
    request.session['quiz_score'] = 0
    return redirect('quiz_question')

def quiz_question(request):
    phone = request.session.get('player_phone')
    if not phone:
        return redirect('landing')
    ids = request.session.get('quiz_questions', [])
    index = request.session.get('quiz_index', 0)
    if index >= len(ids):
        return redirect('quiz_result')
    question = Question.objects.get(id=ids[index])
    if request.method == 'POST':
        selected = request.POST.get('answer')
        if selected == question.correct_option:
            request.session['quiz_score'] = request.session.get('quiz_score', 0) + 1
        request.session['quiz_index'] = index + 1
        return redirect('quiz_question')
    options = [
        ('a', question.option_a),
        ('b', question.option_b),
        ('c', question.option_c),
        ('d', question.option_d),
    ]
    return render(request, 'quiz.html', {
        'question': question,
        'options': options,
        'index': index + 1,
        'total': len(ids),
        'score': request.session.get('quiz_score', 0),
    })

def quiz_result(request):
    phone = request.session.get('player_phone')
    score = request.session.get('quiz_score', 0)
    total = len(request.session.get('quiz_questions', []))
    player = Player.objects.get(phone=phone)
    QuizSession.objects.create(player=player, score=score, total=total, completed=True)
    wrong = total - score
    percentage = round((score / total) * 100) if total > 0 else 0
    ring_offset = round(358 * (1 - score / total)) if total > 0 else 358
    for key in ['quiz_questions', 'quiz_index', 'quiz_score']:
        request.session.pop(key, None)
    return render(request, 'result.html', {
        'score': score, 'total': total,
        'wrong': wrong, 'percentage': percentage,
        'ring_offset': ring_offset, 'phone': phone,
    })

def leaderboard(request):
    phone = request.session.get('player_phone')
    today = timezone.now().date()
    sessions = QuizSession.objects.filter(
        started_at__date=today, completed=True
    ).select_related('player').order_by('-score', 'started_at')[:20]
    top3 = list(sessions[:3])
    my_rank = None
    my_score = None
    if phone:
        for i, s in enumerate(sessions):
            if s.player.phone == phone:
                my_rank = i + 1
                my_score = s.score
                break
    return render(request, 'leaderboard.html', {
        'leaderboard': sessions,
        'top3': top3,
        'phone': phone,
        'my_rank': my_rank,
        'my_score': my_score,
    })