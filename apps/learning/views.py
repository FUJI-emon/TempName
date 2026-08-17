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
from django.http import JsonResponse
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai.services.dto import ChatScope, ConceptDTO, LearningContextDTO
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMRateLimitError, LLMServiceError
from apps.learning.models import (
    ChatMessage,
    ChatThread,
    LearningConcept,
    LearningGoal,
    LearningMaterial,
    ProgressLesson,
    ProgressLessonCard,
    ProgressPathStep,
    ProgressStudentMaterialProgress,
    ProgressStudentStepStatus,
    QuizOption,
    QuizQuestion,
    UsersUser,
)
from apps.learning.services import LearningApplicationService

FRONTEND_DIR = Path(settings.BASE_DIR) / "Newfrontend"
FRONTEND_PAGES = {
    "course_history_my_learning_journeys_1.html",
    "final_test_ai_review_conversation.html",
    "final_test_full_screen_question_review.html",
    "final_test_result_summary_review.html",
    "interactive_lesson_linear_regression_with_sidebar.html",
    "lumina_learning_landing_page.html",
    "lumina_learning_login_screen.html",
    "lumina_learning_upload_document_desktop.html",
    "new_course_ai_topic_discussion.html",
    "personalized_learning_path.html",
    "review_document_content_selection.html",
    "settings_user_account_preferences.html",
    "student_dashboard_overview.html",
}


def _serve_newfrontend_file(filename: str, content_type: str = "text/html; charset=utf-8"):
    if filename not in FRONTEND_PAGES and filename not in ("navigation.js", "api.js"):
        raise Http404("Frontend page not found")

    file_path = FRONTEND_DIR / filename
    if not file_path.exists():
        raise Http404("Frontend page not found")

    body = file_path.read_text(encoding="utf-8", errors="ignore")
    if content_type.startswith("text/html") and "<body" in body and 'data-page=' not in body:
        body = body.replace("<body", f'<body data-page="{filename}"', 1)

    response = HttpResponse(body, content_type=content_type)
    response["Cache-Control"] = "no-store"
    return response


def index(request):
    return _serve_newfrontend_file("lumina_learning_landing_page.html")


def frontend_page(request, page_name):
    return _serve_newfrontend_file(page_name)


def frontend_navigation_js(request):
    return _serve_newfrontend_file("navigation.js", content_type="application/javascript; charset=utf-8")


def frontend_api_js(request):
    return _serve_newfrontend_file("api.js", content_type="application/javascript; charset=utf-8")


@csrf_exempt
@require_http_methods(["POST"])
def onboarding_view(request):
    """
    Endpoint cho câu hỏi mở đầu onboarding.
    Input: {"user_message": "...", "uploaded_material": "..."}
    """
    try:
        data = json.loads(request.body)
        user_message = data.get("user_message", "")
        uploaded_material = data.get("uploaded_material")

        service = LearningApplicationService()
        result = service.start_onboarding_conversation(user_message, uploaded_material)

        return JsonResponse({
            "status": "success",
            "reply": result.reply,
            "ready_to_analyze": result.ready_to_analyze,
            "detected_goal": result.detected_goal,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMRateLimitError as exc:
        return JsonResponse({"status": "error", "error_code": "AI_LIMIT_REACHED", "message": f"Hệ thống AI hiện đã đạt giới hạn/Quota lượt gọi API: {exc}"}, status=429)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"Dịch vụ AI gặp sự cố: {exc}"}, status=500)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Không thể kết nối với AI Engine (có thể hết token hoặc lỗi mạng): {exc}"}, status=500)


def extract_text_from_file_obj(uploaded_file):
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    extracted_text = ""
    if filename.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = [p.extract_text() for p in reader.pages if p.extract_text()]
            extracted_text = "\n".join(pages).strip()
        except Exception:
            extracted_text = ""
    else:
        try:
            raw = file_bytes.decode("utf-8", errors="ignore")
            extracted_text = "".join(c for c in raw if c.isprintable() or c in ("\n", "\r", "\t")).strip()
        except Exception:
            extracted_text = ""

    if not extracted_text or extracted_text.startswith("%PDF-"):
        extracted_text = ""

    return extracted_text


@csrf_exempt
@require_http_methods(["POST"])
def create_material_view(request):
    """
    Endpoint tạo LearningMaterial + gọi analyze_material.
    Input: {"title": "...", "content": "...", "goal_title": "..."} hoặc multipart/form-data
    """
    try:
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            data = request.POST
            uploaded_document = request.FILES.get("document") or request.FILES.get("file")
            title = data.get("title", "")
            content = data.get("content", "")
            goal_title = data.get("goal_title", "")

            if uploaded_document is not None:
                if not title:
                    title = uploaded_document.name
                if not goal_title:
                    goal_title = title
                if not content:
                    content = extract_text_from_file_obj(uploaded_document)
                    if not content:
                        content = f"Nội dung môn học và chủ đề từ tài liệu: {title}"
            elif not title or not content:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Cần chọn file tài liệu hoặc nhập nội dung chủ đề học tập.",
                    },
                    status=400,
                )
        else:
            data = json.loads(request.body)
            title = data.get("title", "")
            content = data.get("content", "")
            goal_title = data.get("goal_title", "")

        student = get_current_student(request)
        if not student:
            return JsonResponse(
                {"status": "error", "message": "Authentication required."},
                status=401,
            )

        service = LearningApplicationService()
        material, analysis = service.process_and_create_material(title, content, goal_title, user=student)

        ProgressStudentMaterialProgress.objects.get_or_create(
            student=student,
            material=material,
            defaults={
                "status": ProgressStudentMaterialProgress.MaterialStatus.IN_PROGRESS,
                "completion_percent": Decimal("0.00"),
                "last_active_at": timezone.now(),
            }
        )

        return JsonResponse({
            "status": "success",
            "material_id": material.id,
            "id": material.id,
            "title": material.title,
            "goal_title": goal_title or material.subject,
            "concepts": [
                {"id": c.id, "title": c.title, "description": c.description}
                for c in analysis.concepts
            ],
            "suggested_skills": analysis.suggested_skills,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMRateLimitError as exc:
        return JsonResponse({"status": "error", "error_code": "AI_LIMIT_REACHED", "message": f"Hệ thống AI hiện đã đạt giới hạn/Quota lượt gọi API: {exc}"}, status=429)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"Dịch vụ AI gặp sự cố: {exc}"}, status=500)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Không thể trích xuất khái niệm từ tài liệu (có thể hết token hoặc lỗi kết nối AI Engine): {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_material_view(request, material_id):
    """
    API xóa LearningMaterial cùng toàn bộ tiến trình học tập liên quan.
    DELETE /material/<material_id>/delete/
    """
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        service = LearningApplicationService()
        success = service.delete_material(material_id=material_id, student_id=student.id)

        if success:
            return JsonResponse({"status": "success", "message": "Xóa khóa học thành công."})
        else:
            return JsonResponse({"status": "error", "message": "Không tìm thấy khóa học để xóa."}, status=404)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Không thể xóa khóa học: {exc}"}, status=500)


@require_http_methods(["GET"])
def list_courses_view(request):
    """
    API lấy danh sách các khóa học (Learning Goal / Learning Journeys) của học viên từ DB.
    """
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        from django.db.models import Q
        progress_qs = ProgressStudentMaterialProgress.objects.filter(student=student).select_related("material")
        material_ids = [p.material_id for p in progress_qs]
        materials = list(LearningMaterial.objects.filter(Q(user=student) | Q(id__in=material_ids)).distinct().order_by("-created_at"))

        courses = []
        for mat in materials:
            goal = mat.goals.first()
            concepts = list(LearningConcept.objects.filter(goal__material=mat))
            steps = list(ProgressPathStep.objects.filter(material=mat).order_by("order_index", "id"))

            progress_record = None
            if student:
                progress_record = ProgressStudentMaterialProgress.objects.filter(student=student, material=mat).first()

            completion_percent = int(progress_record.completion_percent) if progress_record else mat.progress

            # Determine course status
            status = "in_progress"
            if progress_record and progress_record.status:
                status = progress_record.status
            elif completion_percent >= 100:
                status = "completed"
            elif completion_percent == 0 and not steps:
                status = "not_started"

            # Find active step to resume
            current_step = None
            for step in steps:
                if step.status != "completed":
                    current_step = step
                    break
            if not current_step and steps:
                current_step = steps[0]

            course_title = goal.title if (goal and goal.title) else (mat.subject or mat.title)

            courses.append({
                "id": mat.id,
                "course_id": mat.id,
                "material_id": mat.id,
                "title": course_title,
                "material_name": mat.title,
                "has_material": bool(mat.content and len(mat.content.strip()) > 0),
                "created_at": mat.created_at.strftime("%Y-%m-%d %H:%M:%S") if mat.created_at else "",
                "progress": completion_percent,
                "status": status,
                "concepts_count": len(concepts),
                "lessons_count": len(steps),
                "current_step_id": current_step.id if current_step else None,
                "current_step_title": current_step.title if current_step else None
            })

        return JsonResponse({
            "status": "success",
            "courses": courses,
            "materials": courses
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_http_methods(["GET"])
def list_materials_view(request):
    """
    API lấy danh sách các tài liệu học tập (Material History) từ DB.
    """
    return list_courses_view(request)


@require_http_methods(["GET"])
def get_material_detail_view(request, material_id):
    """
    API lấy chi tiết tài liệu học tập và danh sách khái niệm từ DB theo material_id.
    """
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        from django.db.models import Q
        material = LearningMaterial.objects.filter(
            Q(user=student) | Q(progressstudentmaterialprogress__student=student),
            id=material_id
        ).distinct().first()

        if not material:
            return JsonResponse({"status": "error", "message": "Không tìm thấy thông tin bài học hoặc bạn không có quyền truy cập."}, status=404)

        goal = material.goals.first()
        concepts = LearningConcept.objects.filter(goal__material=material).order_by("order_index", "id")

        steps = ProgressPathStep.objects.filter(material=material).order_by("order_index", "id")

        student_statuses = {}
        if student:
            statuses = ProgressStudentStepStatus.objects.filter(student=student, step__material=material)
            student_statuses = {s.step_id: s.status for s in statuses}

        step_list = [
            {
                "id": s.id,
                "order_index": s.order_index,
                "title": s.title,
                "status": s.status,
                "student_status": student_statuses.get(s.id, "unlocked" if s.order_index == 1 else "locked"),
                "concept_id": s.concept_id
            }
            for s in steps
        ]

        completed_steps_count = sum(1 for st in step_list if st["student_status"] == "completed")

        return JsonResponse({
            "status": "success",
            "material_id": material.id,
            "id": material.id,
            "title": material.title,
            "goal_title": goal.title if goal else material.title,
            "subject": material.subject or material.title,
            "created_at": material.created_at.strftime("%Y-%m-%d %H:%M:%S") if material.created_at else "",
            "progress": material.progress or 0,
            "total_concepts_count": concepts.count(),
            "completed_steps_count": completed_steps_count,
            "concepts": [
                {
                    "id": c.external_id or str(c.id),
                    "title": c.title,
                    "description": c.description or ""
                }
                for c in concepts
            ],
            "steps": step_list
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_path_view(request):
    """
    Endpoint sinh đợt learning path kế tiếp cho material.
    Input:
    {
        "material_id": 1,
        "concepts": [
            {"id": "c1", "title": "...", "description": "..."}
        ]
    }
    """
    try:
        data = json.loads(request.body)

        material_id = data.get("material_id")
        concepts_raw = data.get("concepts", [])

        # Get current student from session
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        material = get_object_or_404(
            LearningMaterial,
            id=material_id,
        )

        concepts = [
            ConceptDTO(
                id=c.get("id"),
                title=c.get("title"),
                description=c.get("description", ""),
            )
            for c in concepts_raw
        ]

        service = LearningApplicationService()

        path_batch, steps = service.generate_and_save_learning_path_batch(
            material=material,
            concepts=concepts,
            student=student,
        )

        return JsonResponse({
            "status": "success",
            "ordered_concept_ids": path_batch.ordered_concept_ids,
            "is_final_batch": path_batch.is_final_batch,
            "created_step_ids": [s.id for s in steps],
            "steps": [
                {
                    "id": s.id,
                    "order_index": s.order_index,
                    "title": s.title,
                    "status": s.status,
                    "concept_id": s.concept_id,
                }
                for s in steps
            ],
        })

    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )
    except LLMRateLimitError as exc:
        return JsonResponse(
            {
                "status": "error",
                "error_code": "AI_LIMIT_REACHED",
                "message": f"Hệ thống AI hiện đã đạt giới hạn/Quota lượt gọi API: {exc}",
            },
            status=429,
        )
    except LLMServiceError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Dịch vụ AI gặp sự cố: {exc}",
            },
            status=500,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Dịch vụ AI gặp sự cố: {exc}",
            },
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def submit_checkpoint_view(request):
    """
    Endpoint nộp đáp án checkpoint question.
    Input: {"student_id": 1, "question_id": 1, "selected_option_id": 2, "hints_used": 0}
    """
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        question_id = data.get("question_id")
        selected_option_id = data.get("selected_option_id")
        hints_used = data.get("hints_used", 0)

        if not student_id:
            student = get_current_student(request)
            if not student:
                student, _ = UsersUser.objects.get_or_create(
                    username="demo_student",
                    defaults={
                        "email": "demo@lumina.ai",
                        "display_name": "Alex Learner",
                        "password_hash": "demo_hash"
                    }
                )
        else:
            student = get_object_or_404(UsersUser, id=student_id)

        service = LearningApplicationService()

        attempt, next_action_res = service.submit_checkpoint_answer(
            student=student,
            question_id=question_id,
            selected_option_id=selected_option_id,
            hints_used=hints_used,
        )

        question_model = QuizQuestion.objects.filter(id=question_id).first()
        explanation = question_model.explanation if question_model else "Đã phân tích kết quả bài làm."

        return JsonResponse({
            "status": "success",
            "is_correct": attempt.is_correct,
            "next_action": next_action_res.action.value,
            "needs_next_batch": next_action_res.needs_next_batch,
            "reasoning": next_action_res.reasoning,
            "explanation": explanation,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@require_http_methods(["GET"])
def get_step_quiz_view(request, step_id):
    """
    Endpoint lấy câu hỏi checkpoint, danh sách bài học và các lựa chọn cho 1 step.
    GET /step/<step_id>/quiz/
    """
    try:
        step = ProgressPathStep.objects.filter(id=step_id).first()
        lesson_obj = None

        if step:
            lesson_obj = getattr(step, "lesson", None)

        questions_list = []
        if lesson_obj:
            q_models = list(QuizQuestion.objects.filter(lesson=lesson_obj).order_by("after_card_order", "id"))
            for q in q_models:
                options = list(QuizOption.objects.filter(question=q))
                questions_list.append({
                    "id": q.id,
                    "question_type": q.question_type,
                    "after_card_order": q.after_card_order,
                    "question_text": q.question_text,
                    "explanation": q.explanation,
                    "options": [
                        {
                            "id": opt.id,
                            "option_text": opt.option_text,
                        }
                        for opt in options
                    ]
                })

        if not questions_list:
            # Fallback: find any QuizQuestion created in the system
            fallback_q = QuizQuestion.objects.order_by("-id").first()
            if fallback_q:
                if not lesson_obj and fallback_q.lesson:
                    lesson_obj = fallback_q.lesson
                options = list(QuizOption.objects.filter(question=fallback_q))
                questions_list.append({
                    "id": fallback_q.id,
                    "question_type": fallback_q.question_type,
                    "after_card_order": fallback_q.after_card_order,
                    "question_text": fallback_q.question_text,
                    "explanation": fallback_q.explanation,
                    "options": [
                        {
                            "id": opt.id,
                            "option_text": opt.option_text,
                        }
                        for opt in options
                    ]
                })

        if not questions_list:
            return JsonResponse({
                "status": "error",
                "message": "Chưa có câu hỏi checkpoint trong hệ thống."
            }, status=404)

        lesson_data = None
        if lesson_obj:
            cards = list(ProgressLessonCard.objects.filter(lesson=lesson_obj).order_by("order_index"))
            lesson_data = {
                "id": lesson_obj.id,
                "explanation": lesson_obj.explanation,
                "example": lesson_obj.example,
                "cards": [
                    {
                        "id": c.id,
                        "order_index": c.order_index,
                        "heading": c.heading,
                        "body": c.body
                    }
                    for c in cards
                ]
            }

        student = get_current_student(request)
        student_status = "unlocked" if (step and step.order_index == 1) else "locked"
        if student and step:
            st = ProgressStudentStepStatus.objects.filter(student=student, step=step).first()
            if st:
                student_status = st.status

        return JsonResponse({
            "status": "success",
            "step_id": step.id if step else step_id,
            "order_index": step.order_index if step else 1,
            "step_title": step.title if step else "Kiểm tra kiến thức",
            "student_status": student_status,
            "lesson": lesson_data,
            "questions": questions_list,
            "question": questions_list[0] if questions_list else None
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@require_http_methods(["GET"])
def get_hint_view(request, question_id, level):
    """
    Endpoint lấy gợi ý (level 1..3) cho câu hỏi checkpoint.
    GET /hint/<question_id>/<level>/
    """
    try:
        service = LearningApplicationService()
        hint_res = service.get_question_hint(question_id=question_id, level=level)

        return JsonResponse({
            "status": "success",
            "level": hint_res.level,
            "hint": hint_res.text,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMInvalidResponseError as exc:
        return JsonResponse({"status": "error", "message": f"Guardrail blocked: {exc}"}, status=422)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chat_view(request):
    """
    Endpoint tương tác chat AI theo scope.
    Input: {"student_id": 1, "thread_id": 1, "message": "...", "scope": "goal", "goal_id": 1, "material_id": 1, "concept_id": 2, "lesson_id": 3}
    """
    try:
        data = json.loads(request.body)
        thread_id = data.get("thread_id")
        message = data.get("message", "")
        scope_str = data.get("scope", "goal")

        goal_id = data.get("goal_id")
        material_id = data.get("material_id")
        concept_id = data.get("concept_id")
        lesson_id = data.get("lesson_id") or data.get("step_id")

        scope = ChatScope(scope_str)

        student = get_current_student(request)

        if student is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Authentication required.",
                },
                status=401,
            )

        # Validate and resolve context relationships from Database
        current_goal_title = None
        current_concept_title = None
        current_lesson_text = None

        if lesson_id:
            lesson_obj = ProgressLesson.objects.select_related(
                "concept", "concept__goal", "concept__goal__material", "step"
            ).filter(id=lesson_id).first()
            if not lesson_obj:
                lesson_obj = ProgressLesson.objects.select_related(
                    "concept", "concept__goal", "concept__goal__material", "step"
                ).filter(step_id=lesson_id).first()

            if lesson_obj:
                step_title = lesson_obj.step.title if lesson_obj.step else "Lesson"
                current_lesson_text = f"{step_title}: {lesson_obj.explanation}"
                if lesson_obj.concept:
                    current_concept_title = lesson_obj.concept.title
                    if lesson_obj.concept.goal:
                        current_goal_title = lesson_obj.concept.goal.title

        if not current_concept_title and concept_id:
            concept_obj = LearningConcept.objects.select_related("goal", "goal__material").filter(id=concept_id).first()
            if concept_obj:
                current_concept_title = concept_obj.title
                if concept_obj.goal and not current_goal_title:
                    current_goal_title = concept_obj.goal.title

        if not current_goal_title and goal_id:
            goal_obj = LearningGoal.objects.select_related("material").filter(id=goal_id).first()
            if goal_obj:
                current_goal_title = goal_obj.title

        if not current_goal_title and material_id:
            material_obj = LearningMaterial.objects.filter(id=material_id).first()
            if material_obj:
                first_goal = material_obj.goals.first()
                current_goal_title = first_goal.title if first_goal else material_obj.title

        learning_context = None
        if current_goal_title or current_concept_title or current_lesson_text:
            learning_context = LearningContextDTO(
                current_goal=current_goal_title,
                current_concept=current_concept_title,
                current_lesson=current_lesson_text,
            )

        service = LearningApplicationService()
        ai_msg = service.send_chat_message(
            student=student,
            thread_id=thread_id,
            user_message=message,
            scope=scope,
            learning_context=learning_context,
        )

        return JsonResponse({
            "status": "success",
            "role": ai_msg.role,
            "content": ai_msg.content,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMInvalidResponseError as exc:
        return JsonResponse({"status": "error", "message": f"Guardrail blocked chat: {exc}"}, status=422)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)
# apps/learning/views.py の一番下に追加します
def result(request):
    try:
        return render(request, 'learning/ft_result.html')
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_chat_thread_view(request):
    try:
        if request.method == "GET":
            scope_str = request.GET.get("scope", "goal")
            scope_id = request.GET.get("scope_id")
        else:
            data = json.loads(request.body)
            scope_str = data.get("scope", "goal")
            scope_id = data.get("scope_id")

        if scope_id is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "scope_id is required.",
                },
                status=400,
            )

        student = get_current_student(request)

        if student is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Authentication required.",
                },
                status=401,
            )

        scope = ChatScope(scope_str)

        service = LearningApplicationService()
        thread = service.create_chat_thread(
            student=student,
            scope=scope,
            scope_id=int(scope_id),
        )

        messages = service.get_thread_messages(student=student, thread_id=thread.id)
        messages_data = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

        return JsonResponse({
            "status": "success",
            "thread_id": thread.id,
            "scope": thread.scope_type,
            "scope_id": thread.scope_id,
            "messages": messages_data,
        }, status=201)

    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )


@require_http_methods(["GET"])
def list_user_chat_threads_view(request):
    """
    API lấy danh sách các ChatThread có tin nhắn của học viên hiện tại (tự động dọn dẹp thread rỗng).
    GET /chat/threads/
    """
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        # Xóa các thread rỗng chưa từng có tin nhắn nào của học viên
        ChatThread.objects.filter(student=student, chatmessage__isnull=True).delete()

        threads = ChatThread.objects.filter(student=student).order_by("-created_at")
        threads_data = []

        for t in threads:
            last_msg = ChatMessage.objects.filter(thread=t).order_by("-created_at").first()
            if not last_msg:
                continue

            title = f"Đoạn chat #{t.id}"

            if t.scope_type == ChatThread.ScopeType.GOAL:
                goal_obj = LearningGoal.objects.filter(id=t.scope_id).first()
                if goal_obj:
                    title = goal_obj.title
            elif t.scope_type == ChatThread.ScopeType.MATERIAL:
                mat_obj = LearningMaterial.objects.filter(id=t.scope_id).first()
                if mat_obj:
                    title = mat_obj.title

            if title.startswith("Đoạn chat #"):
                title = last_msg.content[:40] + ("..." if len(last_msg.content) > 40 else "")

            threads_data.append({
                "id": t.id,
                "scope_type": t.scope_type,
                "scope_id": t.scope_id,
                "title": title,
                "created_at": t.created_at.strftime("%H:%M %d/%m/%Y"),
                "last_message": last_msg.content[:60] if last_msg else ""
            })

        return JsonResponse({
            "status": "success",
            "threads": threads_data
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_http_methods(["GET"])
def get_chat_thread_detail_view(request, thread_id):
    """
    API lấy danh sách tin nhắn của một ChatThread theo thread_id.
    GET /chat/thread/<thread_id>/
    """
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        thread = get_object_or_404(ChatThread, id=thread_id, student=student)
        messages = ChatMessage.objects.filter(thread=thread).order_by("created_at")

        messages_data = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

        return JsonResponse({
            "status": "success",
            "thread_id": thread.id,
            "scope": thread.scope_type,
            "scope_id": thread.scope_id,
            "messages": messages_data
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_new_chat_thread_view(request):
    """
    API khởi tạo đoạn chat mới cho học viên (xóa tin nhắn cũ nếu đã có thread để dọn hội thoại).
    POST /chat/thread/new/
    """
    try:
        data = json.loads(request.body)
        scope_str = data.get("scope", "goal")
        scope_id = data.get("scope_id", 1)

        student = get_current_student(request)
        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        scope_type = ChatThread.ScopeType.GOAL if scope_str == "goal" else ChatThread.ScopeType.MATERIAL
        
        # Purge empty threads before creating new thread
        ChatThread.objects.filter(student=student, chatmessage__isnull=True).delete()

        thread, created = ChatThread.objects.get_or_create(
            student=student,
            scope_type=scope_type,
            scope_id=int(scope_id),
        )
        if not created:
            ChatMessage.objects.filter(thread=thread).delete()

        return JsonResponse({
            "status": "success",
            "thread_id": thread.id,
            "scope": thread.scope_type,
            "scope_id": thread.scope_id,
            "messages": []
        }, status=201)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Không thể tạo đoạn chat mới: {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    """
    API xử lý đăng ký tài khoản người dùng mới.

    Phương thức: POST
    Payload (JSON): username, email, password, display_name (optional)
    """
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        display_name = data.get("display_name", "").strip()

        if not username or not email or not password:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Username, email and password are required.",
                },
                status=400,
            )

        if UsersUser.objects.filter(username=username).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Username already exists.",
                },
                status=409,
            )

        if UsersUser.objects.filter(email=email).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Email already exists.",
                },
                status=409,
            )

        user = UsersUser.objects.create(
            username=username,
            email=email,
            password_hash=make_password(password),
            display_name=display_name or username,
        )

        request.session.flush()
        request.session["user_id"] = user.id
        request.session.save()

        return JsonResponse(
            {
                "status": "success",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": user.display_name,
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid JSON.",
            },
            status=400,
        )


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    API xử lý đăng nhập người dùng và tạo session xác thực.

    Phương thức: POST
    Payload (JSON): username, password
    """
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Username and password are required.",
                },
                status=400,
            )

        user = UsersUser.objects.filter(username=username).first()

        if user is None or not check_password(password, user.password_hash):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Invalid username or password.",
                },
                status=401,
            )

        # Clear old session and create a new authenticated session.
        request.session.flush()
        request.session["user_id"] = user.id
        request.session.save()

        return JsonResponse({
            "status": "success",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
            },
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid JSON.",
            },
            status=400,
        )


@require_http_methods(["GET"])
def me_view(request):
    """API lấy thông tin tài khoản đang đăng nhập dựa trên session."""
    user_id = request.session.get("user_id")

    if not user_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "Authentication required.",
            },
            status=401,
        )

    user = UsersUser.objects.filter(id=user_id).first()

    if user is None:
        request.session.flush()

        return JsonResponse(
            {
                "status": "error",
                "message": "User not found.",
            },
            status=401,
        )

    return JsonResponse(
        {
            "status": "success",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    request.session.flush()

    return JsonResponse({
        "status": "success",
        "message": "Logged out successfully.",
    })


def get_current_student(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return UsersUser.objects.filter(id=user_id).first()
