import json
import time
import logging
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
    UsersUser,
    QuizFinalTestOption,
)

from .utils.extractor import extract_text_from_file
from apps.learning.services import LearningApplicationService
from apps.ai.services.dto import ConceptDTO, LessonDTO, QuestionPurpose, ChatScope

logger = logging.getLogger(__name__)



def index(request):
    """トップページ（ログイン前の案内画面 / LP）"""
    return render(request, "learning/index.html")


def dashboard(request):
    """ログイン後のダッシュボード画面：直近の学習履歴と進捗状況を表示"""
    user = request.user if request.user.is_authenticated else None
    materials = LearningMaterial.objects.all().order_by("-last_used_at", "-id")
    recent_activity = materials[:5]

    total_materials_count = materials.count()
    completed_materials_count = materials.filter(progress__gte=100).count()
    in_progress_materials_count = materials.filter(progress__gt=0, progress__lt=100).count()

    avg_progress = 0
    if total_materials_count > 0:
        total_progress_sum = sum(m.progress for m in materials)
        avg_progress = round(total_progress_sum / total_materials_count)

    if user:
        completed_steps_count = UserStepProgress.objects.filter(user=user, status=2).count()
    else:
        completed_steps_count = UserStepProgress.objects.filter(status=2).count()

    total_xp = completed_steps_count * 100
    active_material = materials.order_by("-last_used_at").first()

    context = {
        "title": "LearnAI | ダッシュボード",
        "materials": materials,
        "recent_activity": recent_activity,
        "recent_materials": recent_activity,
        "total_materials_count": total_materials_count,
        "completed_materials_count": completed_materials_count,
        "in_progress_materials_count": in_progress_materials_count,
        "avg_progress": avg_progress,
        "completed_steps_count": completed_steps_count,
        "total_xp": total_xp,
        "active_material": active_material,
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
    if request.method == "POST" and (request.FILES.get("file") or request.FILES.get("document")):
        file_obj = request.FILES.get("file") or request.FILES.get("document")
        doc_name = file_obj.name
        
        extracted_text = extract_text_from_file(file_obj)
        
        try:
            service = LearningApplicationService()
            material, analysis = service.process_and_create_material(
                title=doc_name,
                content=extracted_text,
                goal_title=f"{doc_name} の理解と習得"
            )
            material.subject = subject
            material.save()
            
            sections = []
            if analysis and analysis.concepts:
                for idx, concept in enumerate(analysis.concepts, 1):
                    sections.append({
                        'id': idx,
                        'title': concept.title,
                        'description': concept.description,
                        'is_understood': False
                    })
            
            if not sections:
                sections = [
                    {'id': 1, 'title': '基礎概念と用語の整理', 'is_understood': False},
                    {'id': 2, 'title': '基本ルールの理解と整理', 'is_understood': False},
                    {'id': 3, 'title': '応用パターンの演習', 'is_understood': False},
                    {'id': 4, 'title': '実践問題・ケーススタディ', 'is_understood': False},
                    {'id': 5, 'title': '総合復習・総まとめ', 'is_understood': False},
                ]
            
            topic_dict = {'id': material.id, 'subject': subject, 'title': material.title}
        except Exception as exc:
            logger.error(f"Error analyzing material in add_topic: {exc}")
            topic_dict = {'id': 0, 'subject': subject, 'title': doc_name}
            sections = [
                {'id': 1, 'title': '基礎概念と用語の整理', 'is_understood': False},
                {'id': 2, 'title': '基本ルールの理解と整理', 'is_understood': False},
                {'id': 3, 'title': '応用パターンの演習', 'is_understood': False},
                {'id': 4, 'title': '実践問題・ケーススタディ', 'is_understood': False},
                {'id': 5, 'title': '総合復習・総まとめ', 'is_understood': False},
            ]
        
        context = {
            'topic': topic_dict,
            'subject': subject,
            'document_name': doc_name,
            'sections': sections,
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

    if request.method == "POST" and (request.FILES.get("file") or request.FILES.get("document")):
        file_obj = request.FILES.get("file") or request.FILES.get("document")
        
        doc = UploadedDocument.objects.create(
            learning_material=material,
            file=file_obj,
            name=file_obj.name,
            size=file_obj.size,
        )
        
        extracted_text = extract_text_from_file(file_obj)
        sections = []
        
        try:
            service = LearningApplicationService()
            analysis = service.llm_service.analyze_material(
                material_content=extracted_text,
                goal=material.title
            )
            if analysis and analysis.concepts:
                for idx, concept in enumerate(analysis.concepts, 1):
                    sections.append({
                        'id': idx,
                        'title': concept.title,
                        'description': concept.description,
                        'is_understood': False
                    })
        except Exception as exc:
            logger.error(f"Error analyzing document in document_upload: {exc}")
        
        if not sections:
            sections = [
                {'id': 1, 'title': 'アーキテクチャの基礎概念', 'is_understood': False},
                {'id': 2, 'title': 'メモリ管理と割り当て', 'is_understood': False},
                {'id': 3, 'title': '割り込み処理の仕組み', 'is_understood': False},
                {'id': 4, 'title': '高度なプロトコル制御', 'is_understood': False},
                {'id': 5, 'title': 'システム最適化と総合復習', 'is_understood': False},
            ]

        context = {
            'topic': material,
            'subject': material.subject,
            'document_name': doc.name,
            'sections': sections,
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
def delete_document(request, doc_id):
    """単一ドキュメント/資料の削除（物理ファイルとDBレコードの整合性を保持）"""
    doc = get_object_or_404(UploadedDocument, id=doc_id)
    topic_id = doc.learning_material.id
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'status': 'success', 'message': 'ドキュメントを削除しました'})

    return redirect('learning:path_map', topic_id=topic_id)



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
        status_val = progress_dict.get(s_num, 0) # 0:未完了/未生成, 1:進行中, 2:完了

        if status_val == 2:
            status_str = 'completed'
        elif status_val == 1:
            status_str = 'current'
            current_step_num = s_num
        else:
            status_str = 'available' if s_num <= 3 else 'not_generated'

        is_review = s_num in [3, 4]

        steps.append({
            'number': s_num,
            'title': step['title'],
            'card_count': step['card_count'],
            'status': status_str,
            'xp_reward': step['xp_reward'],
            'is_review': is_review,
            'is_generated': s_num <= 3 or s_num <= current_step_num,
        })

    # Step 5 まで全クリアしたかのフラグ
    all_completed = all(progress_dict.get(i, 0) == 2 for i in range(1, 6))

    completed_count = UserStepProgress.objects.filter(user=user, topic_id=topic_id, status=2).count()
    progress_pct = min(100, completed_count * 20)
    if material.progress != progress_pct:
        material.progress = progress_pct
        material.save(update_fields=['progress'])

    current_step_xp = steps[min(current_step_num - 1, len(steps) - 1)]['xp_reward']
    documents = list(material.documents.all())

    context = {
        'topic': material,
        'steps': steps,
        'current_step_num': current_step_num,
        'current_step_xp': current_step_xp,
        'all_completed': all_completed,
        'finaltest_url': reverse('learning:finaltest_topic', kwargs={'topic_id': topic_id}),
        'documents': documents,
        'max_batch_lessons': 3,
    }
    return render(request, "f2/path_map.html", context)




def finaltest(request, topic_id=None):
    """最終テスト画面（topic_id がない場合は最新の教材を使用）"""
    if topic_id:
        material = get_object_or_404(LearningMaterial, id=topic_id)
    else:
        material = LearningMaterial.objects.order_by("-last_used_at", "-id").first()
        if not material:
            material = LearningMaterial.objects.create(
                title="総合AI学習テスト",
                content="全ステップの理解度をテストします。"
            )

    service = LearningApplicationService()
    final_test, question_models = service.get_or_create_final_test(material)

    questions_payload = []
    for q in question_models:
        opts = list(QuizFinalTestOption.objects.filter(question=q))
        questions_payload.append({
            'id': q.id,
            'order_index': q.order_index,
            'text': q.question_text,
            'options': [o.option_text for o in opts],
            'explanation': q.explanation
        })

    context = {
        'topic': material,
        'final_test': final_test,
        'questions_json': json.dumps(questions_payload, ensure_ascii=False),
        'total_questions': len(questions_payload),
    }
    return render(request, 'learning/finaltest.html', context)


@csrf_exempt
def submit_final_test_api(request, topic_id=None):
    """最終テストの解答提出API"""
    if request.method == 'POST':
        if topic_id:
            material = get_object_or_404(LearningMaterial, id=topic_id)
        else:
            material = LearningMaterial.objects.order_by("-last_used_at", "-id").first()

        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

        user_answers = data.get("answers", {})

        service = LearningApplicationService()
        final_test, _ = service.get_or_create_final_test(material)

        if request.user.is_authenticated:
            student = request.user
        else:
            student, _ = UsersUser.objects.get_or_create(id=1, defaults={'username': 'guest', 'email': 'guest@example.com', 'password_hash': 'hash'})

        attempt = service.submit_final_test_answers(
            student=student,
            final_test=final_test,
            user_answers=user_answers
        )

        return JsonResponse({
            'status': 'success',
            'score_percent': float(attempt.score_percent),
            'passed': attempt.passed,
            'attempt_number': attempt.attempt_number,
            'redirect_url': reverse('learning:dashboard')
        })

    return JsonResponse({'status': 'error'}, status=400)



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

    ai_text = None
    try:
        service = LearningApplicationService()
        if request.user.is_authenticated:
            student = request.user
        else:
            student, _ = UsersUser.objects.get_or_create(id=1, defaults={'username': 'guest'})

        reply_res = service.send_chat_message(
            student=student,
            thread_id=thread.id,
            user_message=user_content,
            scope=ChatScope.MATERIAL
        )
        if reply_res and hasattr(reply_res, 'content'):
            ai_text = reply_res.content
    except Exception as exc:
        logger.warning(f"Error calling AI chat service: {exc}")

    if not ai_text:
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


def _generate_fallback_cards(title: str, step_num: int) -> list:
    step_themes = {
        1: ("基礎概念とキーワード", "導入と基本用語", "📘"),
        2: ("基本ルールの理解と応用", "コア原則と構成", "⚡"),
        3: ("実践問題・ケーススタディ", "実践シナリオと応用", "💡"),
        4: ("高度な設定とトラブルシューティング", "高度な手法と問題解決", "⚙️"),
        5: ("総合理解と最終確認", "総まとめとスキルチェック", "🚀")
    }
    theme_title, theme_sub, default_icon = step_themes.get(step_num, (f"ステップ {step_num} の学習", "概要", "📘"))
    
    return [
        {
            'icon': default_icon,
            'title': f'{title} - {theme_title}',
            'content': f'【ステップ {step_num}】{title} における{theme_sub}を学習します。基本定義と重要なポイントをしっかり理解しましょう。',
            'diagram_title': f'{title} : {theme_title} の構造図',
        },
        {
            'icon': '⚡',
            'title': f'{title} の要点整理',
            'content': f'{title} のステップ {step_num} で押さえるべきポイントです。実際の演習や問題に当てはめて知識を定着させましょう。',
            'diagram_title': f'{title} : 処理フローチャート',
        },
    ]


def _generate_fallback_checkpoint(title: str, step_num: int) -> dict:
    questions_by_step = {
        1: (
            f"【ステップ 1】「{title}」における最も基本的な概念・目的は何ですか？",
            [
                ("基礎的な定義と核心となるプロセスの理解", True),
                ("応用段階のトラブルシューティング", False),
                ("過去の廃止された旧仕様の暗記", False),
                ("無関係な外部ツールの導入", False),
            ],
            f"「{title}」の導入部分（ステップ1）では、全体の基本となる定義と核心プロセスに注目しましょう。"
        ),
        2: (
            f"【ステップ 2】「{title}」の基本ルールおよび構成要素として正しいものはどれですか？",
            [
                ("正確な手順に従った構成要素の組み合わせ", True),
                ("ルールの無視と無計画な実行", False),
                ("静的データの完全な削除", False),
                ("一時的なキャッシュの初期化のみ", False),
            ],
            f"「{title}」の基本原則（ステップ2）は、正しい手順と構成要素の整合性に基づいています。"
        ),
        3: (
            f"【ステップ 3】「{title}」を実際の課題に適用する際、最も推奨されるアプローチはどれですか？",
            [
                ("具体的な事例・ケーススタディに沿った実践的検証", True),
                ("理論のみで実践を一切行わないアプローチ", False),
                ("過去のエラーログを全て無視すること", False),
                ("設定ファイルをランダムに変更すること", False),
            ],
            f"「{title}」の実践問題（ステップ3）では、具体例や実際の利用シナリオを意識するのが効果的です。"
        ),
        4: (
            f"【ステップ 4】「{title}」の高度な設定や問題発生時の対処法として最適なものはどれですか？",
            [
                ("原因の分析と最適化手法の段階的適用", True),
                ("問題の放置とログの削除", False),
                ("システムの再起動のみで対処を終わらせる", False),
                ("未検証のスクリプトを即座に本番実行する", False),
            ],
            f"「{title}」のトラブルシューティング（ステップ4）では、体系的な原因分析と最適な設定変更が鍵です。"
        ),
        5: (
            f"【ステップ 5】「{title}」の全体を通して、習得すべき総合的なゴールは何ですか？",
            [
                ("全体像の体系的理解と自立的な応用・解決能力", True),
                ("単一の用語のみの暗記", False),
                ("環境構築の途中断念", False),
                ("理論と実践の切り離し", False),
            ],
            f"「{title}」の最終確認（ステップ5）では、これまでのステップを総合した実践力・応用力をチェックします。"
        ),
    }

    q_text, opts_raw, hint_text = questions_by_step.get(
        step_num,
        (
            f"【ステップ {step_num}】「{title}」に関する理解度確認問題です。正しい説明はどれですか？",
            [
                (f"「{title}」の適切な理解と活用", True),
                ("誤った解釈に基づく操作", False),
                ("無関係な定義", False),
                ("不十分な確認", False),
            ],
            f"「{title}」のステップ {step_num} で学んだ内容を思い出して選択してください。"
        )
    )

    opt_ids = ['a', 'b', 'c', 'd']
    options = []
    for idx, (text, is_corr) in enumerate(opts_raw):
        options.append({
            'id': opt_ids[idx],
            'text': text,
            'is_correct': is_corr
        })

    return {
        'question': q_text,
        'options': options,
        'hint': hint_text,
    }


def lesson_card_view(request, topic_id, step_num=1):
    material = get_object_or_404(LearningMaterial, id=topic_id)
    service = LearningApplicationService()
    step, card_models, question_model, options, hint_model = service.get_or_create_step_content(material, step_num)

    icons = ['💾', '⚡', '💡', '📘', '🚀']
    cards = []
    for idx, c in enumerate(card_models):
        cards.append({
            'icon': icons[idx % len(icons)],
            'title': c.heading,
            'content': c.body,
            'diagram_title': f"{material.title} : 概念図" if idx == 0 else "",
        })

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

    service = LearningApplicationService()
    step, card_models, question_model, options, hint_model = service.get_or_create_step_content(material, step_num)

    opt_ids = ['a', 'b', 'c', 'd']
    formatted_options = []
    for idx, opt in enumerate(options[:4]):
        formatted_options.append({
            'id': opt_ids[idx],
            'text': opt.option_text,
            'is_correct': opt.is_correct,
        })

    checkpoint_data = {
        'question': question_model.question_text if question_model else f"【ステップ {step_num} クイズ】「{material.title}」に関する問題",
        'options': formatted_options,
        'hint': hint_model.hint_text if hint_model else (question_model.explanation if question_model else f"「{material.title}」のステップ {step_num} で学んだ内容に注目してください。"),
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

        # 2. 学習進捗率 (LearningMaterial.progress) を計算・保存する
        material = get_object_or_404(LearningMaterial, id=topic_id)
        completed_count = UserStepProgress.objects.filter(
            user=user,
            topic_id=topic_id,
            status=2
        ).count()
        progress_percentage = min(100, completed_count * 20)
        material.progress = progress_percentage
        material.last_used_at = timezone.now()
        material.save()

        # 3. Step 5 クリア時は Final Test（最終テスト）へ遷移するフラグとURLを返す
        if step_num >= 5:
            return JsonResponse({
                'status': 'success',
                'is_final': True,
                'redirect_url': reverse('learning:finaltest_topic', kwargs={'topic_id': topic_id})
            })


        # 4. Step 1〜4 クリア時は次のステップを「解放中 (status=1)」にする
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
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai.services.dto import ChatScope, ConceptDTO
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from apps.learning.models import LearningMaterial, UsersUser
from apps.learning.services import LearningApplicationService


def index(request):
    """
    Homepage view for the learning app.
    Displays project educational vision and current registered learning materials.
    """
    materials = LearningMaterial.objects.prefetch_related("goals").all()
    context = {
        "title": "AI cùng học tập — Level-up App",
        "materials": materials,
    }
    return render(request, "learning/index.html", context)


@csrf_exempt
def onboarding_view(request):
    """
    Onboarding View & API Endpoint.
    GET: Renders interactive AI Onboarding Chat UI.
    POST: Processes onboarding chat dialogue or material analysis trigger.
    """
    if request.method == "GET":
        return render(request, "learning/onboarding.html")

    try:
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

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
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def create_material_view(request):
    """
    Endpoint tạo LearningMaterial + gọi analyze_material.
    Input: {"title": "...", "content": "...", "goal_title": "..."}
    """
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        content = data.get("content", "")
        goal_title = data.get("goal_title", "")

        service = LearningApplicationService()
        material, analysis = service.process_and_create_material(title, content, goal_title)

        return JsonResponse({
            "status": "success",
            "material_id": material.id,
            "title": material.title,
            "concepts": [
                {"id": c.id, "title": c.title, "description": c.description}
                for c in analysis.concepts
            ],
            "suggested_skills": analysis.suggested_skills,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_path_view(request):
    """
    Endpoint sinh đợt learning path kế tiếp cho material.
    Input: {"material_id": 1, "concepts": [{"id": "c1", "title": "..."}, ...], "student_id": 1}
    """
    try:
        data = json.loads(request.body)
        material_id = data.get("material_id")
        concepts_raw = data.get("concepts", [])
        student_id = data.get("student_id")

        material = get_object_or_404(LearningMaterial, id=material_id)
        student = UsersUser.objects.filter(id=student_id).first() if student_id else None

        concepts = [
            ConceptDTO(id=c.get("id"), title=c.get("title"), description=c.get("description", ""))
            for c in concepts_raw
        ]

        service = LearningApplicationService()
        path_batch, steps = service.generate_and_save_learning_path_batch(
            material=material, concepts=concepts, student=student
        )

        return JsonResponse({
            "status": "success",
            "ordered_concept_ids": path_batch.ordered_concept_ids,
            "is_final_batch": path_batch.is_final_batch,
            "created_step_ids": [s.id for s in steps],
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)


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

        student = get_object_or_404(UsersUser, id=student_id)
        service = LearningApplicationService()

        attempt, next_action_res = service.submit_checkpoint_answer(
            student=student,
            question_id=question_id,
            selected_option_id=selected_option_id,
            hints_used=hints_used,
        )

        return JsonResponse({
            "status": "success",
            "is_correct": attempt.is_correct,
            "next_action": next_action_res.action.value,
            "needs_next_batch": next_action_res.needs_next_batch,
            "reasoning": next_action_res.reasoning,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)


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


@csrf_exempt
@require_http_methods(["POST"])
def chat_view(request):
    """
    Endpoint tương tác chat AI theo scope.
    Input: {"student_id": 1, "thread_id": 1, "message": "...", "scope": "material"}
    """
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        thread_id = data.get("thread_id")
        message = data.get("message", "")
        scope_str = data.get("scope", "material")

        scope = ChatScope(scope_str)
        student = get_object_or_404(UsersUser, id=student_id)

        service = LearningApplicationService()
        ai_msg = service.send_chat_message(
            student=student,
            thread_id=thread_id,
            user_message=message,
            scope=scope,
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
