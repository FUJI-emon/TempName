import json
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
    QuizAttempt,
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
        if not request.session.get("user_id") and not (hasattr(request, "user") and request.user and request.user.is_authenticated):
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
        student = get_current_student(request)

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

        material = None
        if str(material_id).lower() in ("latest", "0", "null", "undefined"):
            material = LearningMaterial.objects.filter(user=student).order_by("-id").first()
            if not material:
                material = LearningMaterial.objects.order_by("-id").first()
        else:
            try:
                mat_id_int = int(material_id)
                material = LearningMaterial.objects.filter(id=mat_id_int).first()
            except (ValueError, TypeError):
                material = None

            if not material:
                material = LearningMaterial.objects.order_by("-id").first()

        if not material:
            return JsonResponse({"status": "error", "message": "Không tìm thấy thông tin bài học."}, status=404)

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
        visible_limit = ((completed_steps_count // 3) + 1) * 3
        visible_step_list = step_list[:visible_limit]

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
            "steps": visible_step_list
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

        material = None
        if material_id:
            try:
                material = LearningMaterial.objects.filter(id=int(material_id)).first()
            except (ValueError, TypeError):
                material = None

        if not material:
            material = LearningMaterial.objects.order_by("-id").first()

        if not material:
            return JsonResponse({"status": "error", "message": "No learning material found."}, status=404)

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
            batch_size=3,
        )

        if steps:
            try:
                service.ensure_lesson_for_step(steps[0])
            except Exception:
                pass

        return JsonResponse({
            "status": "success",
            "material_id": material.id,
            "id": material.id,
            "ordered_concept_ids": path_batch.ordered_concept_ids,
            "is_final_batch": path_batch.is_final_batch,
            "created_step_ids": [s.id for s in steps],
            "steps": [
                {
                    "id": s.id,
                    "order_index": s.order_index,
                    "title": s.title,
                    "status": s.status,
                    "student_status": "unlocked" if s.order_index == 1 else "locked",
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
def submit_question_answer_view(request, question_id=None):
    """
    API nộp đáp án cho bất kỳ câu hỏi nào (Checkpoint hoặc Final Exam).
    POST /question/<question_id>/answer/
    Payload: {"student_id": 1, "option_id": 301} hoặc {"selected_option_id": 301}
    """
    try:
        data = json.loads(request.body)
        q_id = question_id or data.get("question_id")
        option_id = data.get("option_id") or data.get("selected_option_id")
        hints_used = data.get("hints_used", 0)

        if not q_id:
            return JsonResponse({"status": "error", "message": "question_id is required."}, status=400)
        if not option_id:
            return JsonResponse({"status": "error", "message": "option_id is required."}, status=400)

        student_id = data.get("student_id")
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
        result = service.submit_question_answer(
            student=student,
            question_id=int(q_id),
            selected_option_id=int(option_id),
            hints_used=int(hints_used),
        )

        return JsonResponse({
            "status": "success",
            "question_id": int(q_id),
            "selected_option_id": int(option_id),
            "is_correct": result["is_correct"],
            "explanation": result["explanation"],
            "question_type": result["question_type"],
            "step_id": result["step_id"],
            "step_status": result["step_status"],
            "step_completed": result["step_completed"],
            "next_step_unlocked": result["next_step_unlocked"],
            "new_batch_triggered": result.get("new_batch_triggered", False),
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_checkpoint_view(request):
    """
    Endpoint nộp đáp án checkpoint question (backward compatible).
    Input: {"student_id": 1, "question_id": 1, "selected_option_id": 2, "hints_used": 0}
    """
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        question_id = data.get("question_id")
        selected_option_id = data.get("selected_option_id") or data.get("option_id")
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
def get_hint_view(request, question_id, level):
    """
    API lấy gợi ý phân cấp cho 1 câu hỏi.
    GET /hint/<question_id>/<level>/
    """
    try:
        service = LearningApplicationService()
        hint_res = service.get_question_hint(question_id=int(question_id), level=int(level))
        return JsonResponse({
            "status": "success",
            "question_id": int(question_id),
            "level": hint_res.level,
            "hint": hint_res.text,
        })
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=404)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@require_http_methods(["GET"])
def get_student_learning_progress_view(request, student_id=None):
    """
    API lấy tiến trình học tập cá nhân hóa của học viên.
    GET /student/<student_id>/learning-progress/ hoặc GET /student/learning-progress/
    """
    try:
        s_id = student_id or request.GET.get("student_id")
        if not s_id:
            student = get_current_student(request)
            if not student:
                student = UsersUser.objects.filter(username="demo_student").first()
                if not student:
                    return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
        else:
            student = get_object_or_404(UsersUser, id=s_id)

        material_id = request.GET.get("material_id")
        mat_id_int = int(material_id) if material_id else None

        service = LearningApplicationService()
        progress_data = service.get_student_learning_progress(student=student, material_id=mat_id_int)
        return JsonResponse(progress_data)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {exc}"}, status=500)


@require_http_methods(["GET"])
def get_step_quiz_view(request, step_id):
    """
    Endpoint lấy toàn bộ cấu trúc lesson, cards, checkpoint questions, final exam questions và student_status cho 1 step.
    GET /step/<step_id>/quiz/
    """
    try:
        step = ProgressPathStep.objects.filter(id=step_id).first()
        if not step:
            step = ProgressPathStep.objects.order_by("-id").first()

        if not step:
            return JsonResponse({
                "status": "error",
                "message": f"Không tìm thấy PathStep nào trong hệ thống."
            }, status=404)

        service = LearningApplicationService()
        lesson_obj = service.ensure_lesson_for_step(step)

        cards = list(ProgressLessonCard.objects.filter(lesson=lesson_obj).order_by("order_index"))
        
        raw_kp = getattr(lesson_obj, "key_points", None)
        if isinstance(raw_kp, str):
            try: raw_kp = json.loads(raw_kp)
            except Exception: raw_kp = []
        kp_list = raw_kp if isinstance(raw_kp, list) else []

        raw_fc = getattr(lesson_obj, "flashcards", None)
        if isinstance(raw_fc, str):
            try: raw_fc = json.loads(raw_fc)
            except Exception: raw_fc = []
        fc_list = raw_fc if isinstance(raw_fc, list) else []

        lesson_data = {
            "id": lesson_obj.id,
            "explanation": lesson_obj.explanation or "",
            "example": lesson_obj.example or "",
            "key_points": kp_list,
            "flashcards": fc_list,
            "cards": [
                {
                    "id": c.id,
                    "order_index": c.order_index,
                    "heading": c.heading,
                    "body": c.body,
                }
                for c in cards
            ]
        }

        all_q_models = list(QuizQuestion.objects.filter(lesson=lesson_obj).order_by("id"))
        checkpoint_questions = []
        final_exam_questions = []
        all_questions_list = []

        for q in all_q_models:
            options = list(QuizOption.objects.filter(question=q))
            q_dict = {
                "id": q.id,
                "question_type": q.question_type,
                "after_card_order": q.after_card_order,
                "question_text": q.question_text,
                "explanation": q.explanation,
                "options": [
                    {
                        "id": opt.id,
                        "option_text": opt.option_text,
                        "is_correct": opt.is_correct,
                    }
                    for opt in options
                ]
            }
            all_questions_list.append(q_dict)
            if q.question_type == "checkpoint":
                checkpoint_questions.append(q_dict)
            elif q.question_type == "lesson_wrapup":
                final_exam_questions.append(q_dict)

        checkpoint_questions.sort(key=lambda x: (x["after_card_order"] if x["after_card_order"] is not None else 999, x["id"]))

        student = get_current_student(request)
        student_status = "unlocked" if step.order_index == 1 else "locked"
        if student:
            st = ProgressStudentStepStatus.objects.filter(student=student, step=step).first()
            if st:
                student_status = st.status

        return JsonResponse({
            "status": "success",
            "step_id": step.id,
            "order_index": step.order_index,
            "step_title": step.title,
            "student_status": student_status,
            "lesson": lesson_data,
            "checkpoints": checkpoint_questions,
            "final_exam": final_exam_questions,
            "questions": all_questions_list,
            "question": all_questions_list[0] if all_questions_list else None,
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
        from apps.learning.models import QuizHint, QuizQuestion
        q_model = QuizQuestion.objects.filter(id=question_id).first()
        if q_model:
            db_hint = QuizHint.objects.filter(question=q_model, level=int(level)).first()
            if db_hint:
                return JsonResponse({
                    "status": "success",
                    "level": int(level),
                    "hint": db_hint.hint_text,
                })

        service = LearningApplicationService()
        hint_res = service.get_question_hint(question_id=question_id, level=level)

        return JsonResponse({
            "status": "success",
            "level": hint_res.level,
            "hint": hint_res.text,
        })
    except Exception:
        return JsonResponse({
            "status": "success",
            "level": int(level),
            "hint": f"💡 Gợi ý Mức {level}: Hãy xem lại các khái niệm trọng tâm trong thẻ bài học và áp dụng công thức của Định luật 1 Newton.",
        })


@csrf_exempt
@require_http_methods(["POST"])
def submit_checkpoint_view(request):
    """
    Endpoint nộp đáp án câu hỏi Checkpoint hoặc Final Test đối chiếu 100% từ Database.
    Input (JSON): {"question_id": 1, "selected_option_id": 2, "hints_used": 0}
    """
    try:
        data = json.loads(request.body)
        question_id = data.get("question_id")
        selected_option_id = data.get("selected_option_id")
        hints_used = data.get("hints_used", 0)

        student = None
        student_id = data.get("student_id")
        if student_id:
            student = UsersUser.objects.filter(id=student_id).first()
        if not student:
            student = get_current_student(request)

        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        q_model = QuizQuestion.objects.filter(id=question_id).first()
        selected_opt = QuizOption.objects.filter(id=selected_option_id).first()

        is_correct = False
        explanation = q_model.explanation if (q_model and q_model.explanation) else "Xem lại kiến thức trọng tâm trong thẻ bài học."

        if selected_opt:
            is_correct = bool(selected_opt.is_correct)
            if not is_correct and q_model:
                correct_opt = QuizOption.objects.filter(question=q_model, is_correct=True).first()
                if correct_opt:
                    explanation = f"Đáp án đúng là ({correct_opt.option_text}). {explanation}"

        if q_model:
            QuizAttempt.objects.create(
                student=student,
                question=q_model,
                selected_option=selected_opt,
                is_correct=is_correct,
                hints_used=hints_used
            )

        step_completed = False
        next_step_unlocked = False
        if q_model and q_model.lesson and q_model.lesson.step:
            step = q_model.lesson.step
            if q_model.question_type == "lesson_wrapup" and is_correct:
                st, _ = ProgressStudentStepStatus.objects.get_or_create(
                    student=student,
                    step=step,
                    defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED}
                )
                st.status = ProgressStudentStepStatus.StepStatus.COMPLETED
                st.save()
                step_completed = True

                next_step = ProgressPathStep.objects.filter(
                    material=step.material,
                    order_index=step.order_index + 1
                ).first()
                if next_step:
                    next_st, _ = ProgressStudentStepStatus.objects.get_or_create(
                        student=student,
                        step=next_step,
                        defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED}
                    )
                    next_st.status = ProgressStudentStepStatus.StepStatus.UNLOCKED
                    next_st.save()
                    next_step_unlocked = True

        return JsonResponse({
            "status": "success",
            "is_correct": is_correct,
            "explanation": explanation,
            "question_type": q_model.question_type if q_model else "checkpoint",
            "step_completed": step_completed,
            "next_step_unlocked": next_step_unlocked,
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Lỗi chấm điểm: {exc}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_question_answer_view(request, question_id=None):
    """
    Endpoint nộp đáp án cho câu hỏi theo URL parameter /question/<question_id>/answer/.
    """
    try:
        if request.body:
            data = json.loads(request.body)
        else:
            data = {}

        q_id = question_id or data.get("question_id")
        selected_opt = data.get("option_id") or data.get("selected_option_id")
        hints = data.get("hints_used", 0)

        student = None
        student_id = data.get("student_id")
        if student_id:
            student = UsersUser.objects.filter(id=student_id).first()
        if not student:
            student = get_current_student(request)

        if not student:
            return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)

        q_model = QuizQuestion.objects.filter(id=q_id).first()
        selected_opt_model = QuizOption.objects.filter(id=selected_opt).first()

        is_correct = False
        explanation = q_model.explanation if (q_model and q_model.explanation) else "Xem lại kiến thức trọng tâm trong thẻ bài học."

        if selected_opt_model:
            is_correct = bool(selected_opt_model.is_correct)
            if not is_correct and q_model:
                correct_opt = QuizOption.objects.filter(question=q_model, is_correct=True).first()
                if correct_opt:
                    explanation = f"Đáp án đúng là ({correct_opt.option_text}). {explanation}"

        if q_model:
            QuizAttempt.objects.create(
                student=student,
                question=q_model,
                selected_option=selected_opt_model,
                is_correct=is_correct,
                hints_used=hints
            )

        step_completed = False
        next_step_unlocked = False
        if q_model and q_model.lesson and q_model.lesson.step:
            step = q_model.lesson.step
            if q_model.question_type == "lesson_wrapup" and is_correct:
                st, _ = ProgressStudentStepStatus.objects.get_or_create(
                    student=student,
                    step=step,
                    defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED}
                )
                st.status = ProgressStudentStepStatus.StepStatus.COMPLETED
                st.save()
                step_completed = True

                next_step = ProgressPathStep.objects.filter(
                    material=step.material,
                    order_index=step.order_index + 1
                ).first()
                if next_step:
                    next_st, _ = ProgressStudentStepStatus.objects.get_or_create(
                        student=student,
                        step=next_step,
                        defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED}
                    )
                    next_st.status = ProgressStudentStepStatus.StepStatus.UNLOCKED
                    next_st.save()
                    next_step_unlocked = True

        return JsonResponse({
            "status": "success",
            "is_correct": is_correct,
            "explanation": explanation,
            "question_type": q_model.question_type if q_model else "checkpoint",
            "step_completed": step_completed,
            "next_step_unlocked": next_step_unlocked,
        })
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc), "exc_type": type(exc).__name__}, status=500)


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
            "thread_id": ai_msg.thread.id if hasattr(ai_msg, "thread") else thread_id,
            "role": ai_msg.role,
            "content": ai_msg.content,
        })
    except (LLMEmptyInputError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except LLMInvalidResponseError as exc:
        return JsonResponse({"status": "error", "message": f"Guardrail blocked chat: {exc}"}, status=422)
    except LLMRateLimitError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=429)
    except LLMServiceError as exc:
        return JsonResponse({"status": "error", "message": f"LLM Error: {exc}"}, status=500)
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

        if hasattr(request.session, "flush"):
            request.session.flush()
        else:
            request.session.clear()
        request.session["user_id"] = user.id

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
        if hasattr(request.session, "flush"):
            request.session.flush()
        else:
            request.session.clear()
        request.session["user_id"] = user.id

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

    if user_id:
        user = UsersUser.objects.filter(id=user_id).first()
        if user:
            return user

    default_student = UsersUser.objects.first()
    if not default_student:
        default_student = UsersUser.objects.create(
            username="demo_student",
            display_name="Alex Miller",
            email="demo@example.com",
        )
    return default_student
