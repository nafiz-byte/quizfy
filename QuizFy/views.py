from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import random, sys, json, os, requests
from .models import Player, OTPSession, Topic, Question, QuizSession


def landing(request):
    return render(request, 'index.html')


def send_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone.startswith('01') or len(phone) != 11:
            return redirect('landing')

        subscriber_id = f"tel:88{phone}"
        response = requests.post(
            "https://developer.bdapps.com/otp/request",
            json={
                "applicationId": os.environ.get('BDAPPS_APP_ID'),
                "password": os.environ.get('BDAPPS_PASSWORD'),
                "subscriberId": subscriber_id
            }
        )
        data = response.json()
        print("OTP Request:", data, flush=True, file=sys.stderr)

        if data.get('statusCode') == 'S1000':
            request.session['otp_phone'] = phone
            request.session['otp_ref'] = data.get('referenceNo')
            return redirect('verify_otp')
        return redirect('landing')
    return redirect('landing')


def verify_otp(request):
    phone = request.session.get('otp_phone')
    ref = request.session.get('otp_ref')
    if not phone:
        return redirect('landing')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        response = requests.post(
            "https://developer.bdapps.com/otp/verify",
            json={
                "applicationId": os.environ.get('BDAPPS_APP_ID'),
                "password": os.environ.get('BDAPPS_PASSWORD'),
                "referenceNo": ref,
                "otp": entered_otp
            }
        )
        data = response.json()
        print("OTP Verify:", data, flush=True, file=sys.stderr)

        if data.get('statusCode') == 'S1000':
            player, _ = Player.objects.get_or_create(phone=phone)
            player.is_verified = True
            player.is_charged = True
            player.save()
            request.session['player_phone'] = phone
            request.session.pop('otp_phone', None)
            request.session.pop('otp_ref', None)
            return redirect('quiz')
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


def unsubscribe(request):
    phone = request.session.get('player_phone')
    if not phone:
        return redirect('landing')
    if request.method == 'POST':
        try:
            player = Player.objects.get(phone=phone)
            player.is_verified = False
            player.is_charged = False
            player.save()
            requests.post(
                "https://developer.bdapps.com/subscription/send",
                json={
                    "applicationId": os.environ.get('BDAPPS_APP_ID'),
                    "password": os.environ.get('BDAPPS_PASSWORD'),
                    "subscriberId": f"tel:88{phone}",
                    "action": "0"
                }
            )
        except Player.DoesNotExist:
            pass
        request.session.flush()
        return redirect('landing')
    return render(request, 'unsubscribe.html', {'phone': phone})


@csrf_exempt
def robi_notify(request):
    data = json.loads(request.body)
    print("Robi Notification:", data, flush=True)
    return JsonResponse({"status": "ok"})


@csrf_exempt
def robi_subscription(request):
    data = json.loads(request.body)
    msisdn = data.get('msisdn', '') or data.get('subscriberId', '')
    status = data.get('status', '') or data.get('subscriptionStatus', '')
    phone = msisdn.replace('tel:88', '0').replace('880', '0')
    player, _ = Player.objects.get_or_create(phone=phone)
    if 'UNREGIST' in status.upper():
        player.is_charged = False
        player.save()
    return JsonResponse({"statusCode": "S1000", "statusDetail": "Success"})