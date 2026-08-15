import json
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai.services.dto import ChatScope, ConceptDTO
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from apps.learning.models import LearningMaterial, UsersUser
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
    if filename not in FRONTEND_PAGES and filename != "navigation.js":
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
