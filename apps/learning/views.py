import time
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import LearningMaterial, UploadedDocument


def index(request):
    """ホームページ / ダッシュボード：直近の学習履歴も含めて表示"""
    # 🌟 最後に使った日時（last_used_at）、またはIDの新しい順で最新5件を取得
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
    return render(request, "learning/index.html", context)


def subject_select(request):
    """教科選択画面：indexへリダイレクトして確実にデータを渡す"""
    return redirect('index')


def topic_list(request, subject):
    """トピック一覧画面（PathMap作成済みの完成したファイルのみ表示）"""
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
    """「ファイルを追加」フロー：PathMap作成まではDBに保存しない"""
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
    """トピック詳細：直近の学習履歴から押されたら Path Map 画面へ転送（更新日時を最新化）"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    material.last_used_at = timezone.now()
    material.save()

    return redirect('path_map', topic_id=topic_id)


def ai_chat_start(request):
    return render(request, "f2/subject_select.html")


def document_upload(request, topic_id):
    """既存トピックに対するドキュメント追加画面"""
    if topic_id == 0:
        subject = request.GET.get('subject') or 'math'
        return redirect('add_topic', subject=subject)

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
                {'id': 1, 'title': 'Introduction to Firmware Architecture', 'is_understood': False},
                {'id': 2, 'title': 'Memory Management & Allocation', 'is_understood': False},
                {'id': 3, 'title': 'Interrupt Handling', 'is_understood': False},
                {'id': 4, 'title': 'Boot Sequence & Initialization', 'is_understood': False},
                {'id': 5, 'title': 'Communication Protocols (I2C, SPI)', 'is_understood': False},
                {'id': 6, 'title': 'Power Management', 'is_understood': False},
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
    return redirect('topic_list', subject=material.subject)


@require_POST
def delete_topic(request, topic_id):
    """単一トピックの削除"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    subject = material.subject

    # 添付ファイルの物理削除
    for doc in material.documents.all():
        if doc.file:
            doc.file.delete(save=False)
    
    # DBからの完全削除（履歴からも消えます）
    material.delete()

    return redirect('topic_list', subject=subject)


@require_POST
def batch_delete_topics(request, subject):
    """一括削除：添付ファイルの物理削除 ＋ DB完全削除"""
    topic_ids = request.POST.getlist("topic_ids")
    if topic_ids:
        materials = LearningMaterial.objects.filter(id__in=topic_ids)
        for material in materials:
            # 添付ファイルの物理削除
            for doc in material.documents.all():
                if doc.file:
                    doc.file.delete(save=False)
            # DB削除
            material.delete()

        # セッション側にも履歴が保存されていた場合の同期処理
        if 'recent_topics' in request.session:
            updated_recent = [
                item for item in request.session.get('recent_topics', [])
                if str(item.get('id')) not in [str(tid) for tid in topic_ids]
            ]
            request.session['recent_topics'] = updated_recent
            request.session.modified = True

    return redirect('topic_list', subject=subject)


def save_understanding(request, topic_id):
    """理解度チェック送信時：ここで初めて DB に新規作成して Path Map 画面へ移動"""
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

    return redirect('path_map', topic_id=topic_id)


def path_map_view(request, topic_id):
    """Adaptive Path Map 画面表示（難易度・ステップ別XP報酬を設定）"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    
    steps = [
        {
            'number': 1,
            'title': '基礎概念とキーワード',
            'card_count': 5,
            'status': 'current',
            'xp_reward': 100,
        },
        {
            'number': 2,
            'title': '基本ルールの理解と応用',
            'card_count': 8,
            'status': 'locked',
            'xp_reward': 250,
        },
        {
            'number': 3,
            'title': '実践問題・ケーススタディ',
            'card_count': 12,
            'status': 'locked',
            'xp_reward': 500,
        }
    ]
    
    current_step_num = 1
    current_step_xp = steps[current_step_num - 1]['xp_reward']

    context = {
        'topic': material,
        'steps': steps,
        'current_step_num': current_step_num,
        'current_step_xp': current_step_xp,
    }
    return render(request, "f2/path_map.html", context)