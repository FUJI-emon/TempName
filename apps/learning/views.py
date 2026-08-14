import json
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# 🌟 モデルのインポート
from .models import (
    LearningMaterial,
    Topic,
    UploadedDocument,
    ChatThread,
    ChatMessage,
    UserStepProgress,
)


def index(request):
    """トップページ（ログイン前の案内画面 / LP）"""
    return render(request, "learning/index.html")


def dashboard(request):
    """ログイン後のダッシュボード画面：直近の学習履歴も含めて表示"""
    recent_list = LearningMaterial.objects.all().order_by("-last_used_at", "-id")[:5]
    
    try:
        materials = LearningMaterial.objects.prefetch_related("goals").all()
    except Exception:
        materials = LearningMaterial.objects.all()

    context = {
        "title": "AIとともに学習するクイズアプリ",
        "materials": materials,
        "recent_materials": recent_list,
        "recent_topics": recent_list,
        "recent_history": recent_list,
    }
    return render(request, "learning/dashboard.html", context)


def subject_select(request):
    """教科選択画面"""
    return redirect('learning:index')


def topic_list(request, subject):
    """トピック一覧画面"""
    materials = LearningMaterial.objects.filter(subject__iexact=subject).order_by("-last_used_at")

    TOTAL_SLOTS = 8
    active_count = materials.count()
    empty_slots_count = max(0, TOTAL_SLOTS - 1 - active_count)

    subject_name = subject.replace('_', ' ').replace('-', ' ').title()

    context = {
        "subject": subject,
        "subject_name": subject_name,
        "topics": materials,
        "empty_slots": range(empty_slots_count),
    }
    return render(request, "f2/topic_list.html", context)


def add_topic(request, subject):
    """「ファイルを追加」フロー"""
    if request.method == "POST" and request.FILES.get("file"):
        file_obj = request.FILES["file"]
        doc_name = file_obj.name
        
        time.sleep(2)
        
        context = {
            'topic': {'id': 0, 'subject': subject, 'title': doc_name},
            'subject': subject,
            'document_name': doc_name,
            'sections': [
                {'id': 1, 'title': '基礎概念と用語の整理', 'is_understood': False},
                {'id': 2, 'title': '基本ルールの理解と整理', 'is_understood': False},
                {'id': 3, 'title': '応用パターンの演習', 'is_understood': False},
                {'id': 4, 'title': '実践問題・ケーススタディ', 'is_understood': False},
                {'id': 5, 'title': '総合復習・総まとめ', 'is_understood': False},
            ]
        }
        return render(request, "f2/review_document.html", context)

    context = {
        "topic": {'id': 0, 'subject': subject, 'title': '新規資料'},
        "subject": subject,
        "documents": [],
    }
    return render(request, "f2/document_upload.html", context)


def topic_detail(request, topic_id):
    """トピック詳細"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    material.last_used_at = timezone.now()
    material.save()

    return redirect('learning:path_map', topic_id=topic_id)


def ai_chat_start(request):
    return render(request, "f2/subject_select.html")


def document_upload(request, topic_id):
    """既存トピックに対するドキュメント追加画面"""
    if topic_id == 0:
        subject = request.GET.get('subject') or 'math'
        return redirect('learning:add_topic', subject=subject)

    material = get_object_or_404(LearningMaterial, id=topic_id)

    if request.method == "POST" and request.FILES.get("file"):
        file_obj = request.FILES["file"]
        
        doc = UploadedDocument.objects.create(
            learning_material=material,
            file=file_obj,
            name=file_obj.name,
            size=file_obj.size,
        )
        
        time.sleep(2)
        
        context = {
            'topic': material,
            'subject': material.subject,
            'document_name': doc.name,
            'sections': [
                {'id': 1, 'title': 'アーキテクチャの基礎概念', 'is_understood': False},
                {'id': 2, 'title': 'メモリ管理と割り当て', 'is_understood': False},
                {'id': 3, 'title': '割り込み処理の仕組み', 'is_understood': False},
                {'id': 4, 'title': '高度なプロトコル制御', 'is_understood': False},
                {'id': 5, 'title': 'システム最適化と総合復習', 'is_understood': False},
            ]
        }
        return render(request, "f2/review_document.html", context)

    documents = material.documents.all()[:4]

    context = {
        "topic": material,
        "subject": material.subject,
        "documents": documents,
    }

    return render(request, "f2/document_upload.html", context)


def edit_topic_title(request, topic_id):
    """トピック名の編集処理"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    referer = request.META.get('HTTP_REFERER')
    
    if request.method == 'POST':
        new_title = request.POST.get('title')
        if new_title:
            material.title = new_title
            material.save()
            
    if referer:
        return redirect(referer)
    return redirect('learning:topic_list', subject=material.subject)


@require_POST
def delete_topic(request, topic_id):
    """単一トピックの削除"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    subject = material.subject

    for doc in material.documents.all():
        if doc.file:
            doc.file.delete(save=False)
    
    material.delete()
    return redirect('learning:topic_list', subject=subject)


@require_POST
def batch_delete_topics(request, subject):
    """一括削除"""
    topic_ids = request.POST.getlist("topic_ids")
    if topic_ids:
        materials = LearningMaterial.objects.filter(id__in=topic_ids)
        for material in materials:
            for doc in material.documents.all():
                if doc.file:
                    doc.file.delete(save=False)
            material.delete()

        if 'recent_topics' in request.session:
            updated_recent = [
                item for item in request.session.get('recent_topics', [])
                if str(item.get('id')) not in [str(tid) for tid in topic_ids]
            ]
            request.session['recent_topics'] = updated_recent
            request.session.modified = True

    return redirect('learning:topic_list', subject=subject)


def save_understanding(request, topic_id):
    """理解度チェック送信時"""
    doc_name = request.POST.get('document_name') or '学習ロードマップ'
    subject = request.POST.get('subject') or 'math'

    if topic_id == 0:
        material = LearningMaterial.objects.create(
            subject=subject,
            title=doc_name,
            progress=0,
            last_used_at=timezone.now(),
        )
        topic_id = material.id
    else:
        material = get_object_or_404(LearningMaterial, id=topic_id)
        material.last_used_at = timezone.now()
        if material.title == "no title" or not material.title:
            material.title = doc_name
        material.save()

    return redirect('learning:path_map', topic_id=topic_id)


# 🌟 Step 1 〜 Step 5 までのロードマップ生成・管理
def path_map_view(request, topic_id):
    """Adaptive Path Map 画面表示（Step 1〜5対応）"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    user = request.user if request.user.is_authenticated else None

    progress_records = UserStepProgress.objects.filter(user=user, topic_id=topic_id)
    progress_dict = {p.step_num: p.status for p in progress_records}

    # 初期状態で Step 1 は解放中(1)
    if 1 not in progress_dict:
        progress_dict[1] = 1

    steps_data = [
        {'number': 1, 'title': '基礎概念とキーワード', 'card_count': 5, 'xp_reward': 100},
        {'number': 2, 'title': '基本ルールの理解と応用', 'card_count': 8, 'xp_reward': 250},
        {'number': 3, 'title': '実践問題・ケーススタディ', 'card_count': 12, 'xp_reward': 500},
        {'number': 4, 'title': '高度な設定とトラブルシューティング', 'card_count': 15, 'xp_reward': 750},
        {'number': 5, 'title': '総合理解と最終確認', 'card_count': 20, 'xp_reward': 1000},
    ]

    steps = []
    current_step_num = 1

    for step in steps_data:
        s_num = step['number']
        status_val = progress_dict.get(s_num, 0) # 0:ロック, 1:解放中(挑戦可能), 2:完了

        if status_val == 2:
            status_str = 'completed'
        elif status_val == 1:
            status_str = 'current'
            current_step_num = s_num
        else:
            status_str = 'locked'

        steps.append({
            'number': s_num,
            'title': step['title'],
            'card_count': step['card_count'],
            'status': status_str,
            'xp_reward': step['xp_reward'],
        })

    # Step 5 まで全クリアしたかのフラグ
    all_completed = all(progress_dict.get(i, 0) == 2 for i in range(1, 6))

    current_step_xp = steps[min(current_step_num - 1, len(steps) - 1)]['xp_reward']

    context = {
        'topic': material,
        'steps': steps,
        'current_step_num': current_step_num,
        'current_step_xp': current_step_xp,
        'all_completed': all_completed,
        'finaltest_url': reverse('learning:finaltest'),
    }
    return render(request, "f2/path_map.html", context)


def finaltest(request):
    """最終テスト画面"""
    return render(request, 'learning/finaltest.html')


# ==========================================
# 🤖 AIアシスタント・チャット機能 View
# ==========================================

def chat_thread_list(request):
    threads = ChatThread.objects.all().order_by('-updated_at')
    return render(request, "learning/chat_thread_list.html", {'threads': threads})


def chat_detail(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    messages = thread.messages.all().order_by('created_at')
    return render(request, "learning/chat_detail.html", {'thread': thread, 'chat_messages': messages})


@require_POST
def send_chat_message(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    
    try:
        data = json.loads(request.body)
        user_content = data.get('content', '').strip()
    except json.JSONDecodeError:
        user_content = request.POST.get('content', '').strip()

    if not user_content:
        return JsonResponse({'status': 'error', 'message': 'メッセージが空です'}, status=400)

    user_msg = ChatMessage.objects.create(thread=thread, sender='user', content=user_content)
    ai_text = f"「{user_content}」についての質問ですね！わかりやすくお答えします。"
    ai_msg = ChatMessage.objects.create(thread=thread, sender='ai', content=ai_text)
    thread.save()

    return JsonResponse({
        'status': 'success',
        'user_message': {'content': user_msg.content, 'created_at': user_msg.created_at.strftime('%H:%M')},
        'ai_message': {'content': ai_msg.content, 'created_at': ai_msg.created_at.strftime('%H:%M')}
    })


def create_chat_thread(request, topic_id):
    material = get_object_or_404(LearningMaterial, id=topic_id)
    thread = ChatThread.objects.create(learning_material=material, title=f"{material.title} についての質問")
    ChatMessage.objects.create(thread=thread, sender='ai', content=f"こんにちは！「{material.title}」について分からないことがあれば何でも聞いてね！")
    return redirect('learning:chat_detail', thread_id=thread.id)


def lesson_card_view(request, topic_id, step_num=1):
    material = get_object_or_404(LearningMaterial, id=topic_id)
    cards = [
        {
            'icon': '💾',
            'title': f'ステップ {step_num} : メモリ割り当ての基礎',
            'content': f'ステップ {step_num} のコンテンツです。重要項目を重点的に確認しましょう。',
            'diagram_title': 'メモリ構造・概念図',
        },
        {
            'icon': '⚡',
            'title': '要点の確認',
            'content': '各ステップを順にクリアすることで応用力が身につきます。',
            'diagram_title': '処理フローチャート',
        },
    ]

    context = {
        'topic': material,
        'step_num': step_num,
        'step_title': f'ステップ {step_num} の学習',
        'cards': cards,
        'total_cards': len(cards),
    }
    return render(request, "f2/lesson_card.html", context)


def lesson_checkpoint_view(request, topic_id, step_num=1):
    """理解度チェック画面"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    user = request.user if request.user.is_authenticated else None

    progress, _ = UserStepProgress.objects.get_or_create(
        user=user,
        topic_id=topic_id,
        step_num=step_num
    )

    checkpoint_data = {
        'question': f'【ステップ {step_num} クイズ】コンパイル時に領域が割り当てられるメモリの種類はどれですか？',
        'options': [
            {'id': 'a', 'text': 'スタックメモリ'},
            {'id': 'b', 'text': 'ヒープメモリ'},
            {'id': 'c', 'text': '静的メモリ', 'is_correct': True},
            {'id': 'd', 'text': 'レジスタメモリ'},
        ],
        'hint': 'プログラムを実行する前（コンパイル時）に固定のサイズが確定するメモリ領域です。',
    }

    context = {
        'topic': material,
        'step_num': step_num,
        'step_title': f'ステップ {step_num} 理解度チェック',
        'checkpoint': checkpoint_data,
    }
    return render(request, "f2/lesson_checkpoint.html", context)


# 🌟 クイズクリア用API（Step 5クリア時は finaltest のURLを返す）
@csrf_exempt
def complete_step_api(request, topic_id, step_num):
    """クイズ正解時に呼び出され、ステップ解放または finaltest への誘導を行う"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

        mistakes = data.get('mistakes', 0)
        time_taken = data.get('time_taken', 0)
        user = request.user if request.user.is_authenticated else None

        # 1. 現在のステップを「完了 (status=2)」にする
        current_progress, _ = UserStepProgress.objects.get_or_create(
            user=user,
            topic_id=topic_id,
            step_num=step_num
        )
        current_progress.status = 2
        current_progress.mistake_count = mistakes
        current_progress.time_taken_seconds = time_taken
        current_progress.save()

        # 2. Step 5 クリア時は Final Test（最終テスト）へ遷移するフラグとURLを返す
        if step_num >= 5:
            return JsonResponse({
                'status': 'success',
                'is_final': True,
                'redirect_url': reverse('learning:finaltest')
            })

        # 3. Step 1〜4 クリア時は次のステップを「解放中 (status=1)」にする
        next_step_num = step_num + 1
        next_progress, _ = UserStepProgress.objects.get_or_create(
            user=user,
            topic_id=topic_id,
            step_num=next_step_num
        )
        if next_progress.status == 0:
            next_progress.status = 1
            next_progress.save()

        return JsonResponse({
            'status': 'success',
            'is_final': False,
            'next_step': next_step_num
        })

    return JsonResponse({'status': 'error'}, status=400)

@require_POST
def update_settings(request):
    """ダッシュボードの設定メニューからメールアドレスとユーザー名を更新"""
    if request.user.is_authenticated:
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()

        if email:
            request.user.email = email
        if username:
            request.user.username = username

        request.user.save()

    return redirect('learning:dashboard')

# ⭕️ OK: スッキリ1つずつにする
def settings_view(request):
    """設定画面"""
    return render(request, "learning/settings.html")

def profile_view(request):
    """プロフィール画面"""
    return render(request, "learning/profile.html")
