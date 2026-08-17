from decimal import Decimal
from typing import List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from apps.ai.services.dto import (
    AnalyzeMaterialResult,
    AnswerEvaluationResult,
    ChatMessageDTO,
    ChatReplyResult,
    ChatRole,
    ChatScope,
    ConceptDTO,
    HintResult,
    LearningContextDTO,
    LearningPathBatchResult,
    NextAction,
    NextActionResult,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from apps.ai.services.factory import get_llm_service
from apps.ai.services.orchestrator import LearningOrchestrator
from apps.learning.models import (
    AssessmentSkill,
    AssessmentSkillCheck,
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
    QuizHint,
    QuizOption,
    QuizQuestion,
    UsersUser,
)


class LearningApplicationService:
    """
    Application Service layer bridging Django ORM models and the AI Service Layer.
    Ensures AI Service Layer remains decoupled from Django models.
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or get_llm_service()
        self.orchestrator = LearningOrchestrator(llm_service=self.llm_service)

    def _get_primary_goal(self, material: LearningMaterial) -> LearningGoal:
        goal = material.goals.order_by("created_at").first()
        if goal:
            return goal
        return LearningGoal.objects.create(
            material=material,
            title=material.subject or material.title,
            description=f"Auto-generated goal for {material.title}",
        )

    def _upsert_concept(self, goal: LearningGoal, concept: ConceptDTO, order_index: int) -> LearningConcept:
        concept_model, _ = LearningConcept.objects.update_or_create(
            goal=goal,
            external_id=concept.id,
            defaults={
                "title": concept.title,
                "description": concept.description or "",
                "order_index": order_index,
            },
        )
        return concept_model

    @staticmethod
    def _concept_dto_from_model(concept: LearningConcept) -> ConceptDTO:
        return ConceptDTO(
            id=concept.external_id or str(concept.id),
            title=concept.title,
            description=concept.description or "",
        )

    def start_onboarding_conversation(
        self, user_message: str, uploaded_material: Optional[str] = None
    ):
        if not user_message or not user_message.strip():
            raise LLMEmptyInputError("user_message không được để trống")
        return self.llm_service.start_conversation(user_message, uploaded_material)

    @transaction.atomic
    def process_and_create_material(
        self, title: str, content: str, goal_title: str, user: Optional[UsersUser] = None
    ) -> Tuple[LearningMaterial, AnalyzeMaterialResult]:
        if not title or not title.strip():
            raise ValueError("Tiêu đề tài liệu không được để trống")
        if not content or not content.strip():
            raise LLMEmptyInputError("Nội dung tài liệu không được để trống")

        material = LearningMaterial.objects.create(
            user=user,
            title=title.strip(),
            content=content.strip(),
            last_used_at=timezone.now(),
            progress=0,
            subject=(goal_title.strip() if goal_title else title.strip())[:20],
        )

        analysis = self.llm_service.analyze_material(
            material_content=material.content,
            goal=goal_title.strip() if goal_title else title.strip(),
        )

        goal = LearningGoal.objects.create(
            material=material,
            title=goal_title.strip() if goal_title else title.strip(),
            description=f"Generated goal for {material.title}",
        )

        created_concepts: List[LearningConcept] = []
        for order_index, concept in enumerate(analysis.concepts, start=1):
            created_concepts.append(
                LearningConcept.objects.create(
                    goal=goal,
                    external_id=concept.id,
                    title=concept.title,
                    description=concept.description or "",
                    order_index=order_index,
                )
            )

        skill_names = analysis.suggested_skills or [concept.title for concept in analysis.concepts]
        for index, skill_name in enumerate(skill_names):
            if not created_concepts:
                break
            concept_ref = created_concepts[index % len(created_concepts)]
            AssessmentSkill.objects.create(concept=concept_ref, name=skill_name)

        return material, analysis

    @transaction.atomic
    def record_skill_checks(self, student: UsersUser, skill_ids_known: List[int]):
        for skill_id in skill_ids_known:
            try:
                skill = AssessmentSkill.objects.get(id=skill_id)
                AssessmentSkillCheck.objects.update_or_create(
                    student=student,
                    skill=skill,
                    defaults={"is_known": True},
                )
            except AssessmentSkill.DoesNotExist:
                continue

    @transaction.atomic
    def generate_and_save_learning_path_batch(
        self,
        material: LearningMaterial,
        concepts: List[ConceptDTO],
        student: Optional[UsersUser] = None,
        mastery_context: Optional[dict] = None,
        batch_size: int = 3,
    ) -> Tuple[LearningPathBatchResult, List[ProgressPathStep]]:
        mastery_ctx = mastery_context or {}
        goal = self._get_primary_goal(material)

        if not concepts:
            existing_concepts = LearningConcept.objects.filter(goal__material=material).order_by("order_index", "id")
            concepts = [
                ConceptDTO(
                    id=c.external_id or str(c.id),
                    title=c.title,
                    description=c.description or "",
                )
                for c in existing_concepts
            ]

        path_batch = self.llm_service.generate_learning_path(
            concepts=concepts,
            mastery_context=mastery_ctx,
            batch_size=batch_size,
        )

        created_steps: List[ProgressPathStep] = []
        existing_step_count = ProgressPathStep.objects.filter(material=material).count()
        concept_map = {c.id: c for c in concepts}
        concept_models = {
            concept.id: self._upsert_concept(goal, concept, idx + 1)
            for idx, concept in enumerate(concepts)
        }

        for idx, concept_id in enumerate(path_batch.ordered_concept_ids):
            concept = concept_map.get(
                concept_id, ConceptDTO(id=concept_id, title=f"Concept {concept_id}")
            )
            concept_model = concept_models.get(concept.id)
            if concept_model is None:
                concept_model = self._upsert_concept(goal, concept, idx + 1)
                concept_models[concept.id] = concept_model

            order_idx = existing_step_count + idx + 1
            step = ProgressPathStep.objects.filter(
                material=material,
                concept=concept_model,
            ).first()
            if step is None:
                step, _ = ProgressPathStep.objects.get_or_create(
                    material=material,
                    concept=concept_model,
                    defaults={
                        "order_index": order_idx,
                        "title": concept.title,
                        "status": "generated",
                    },
                )
            if step.concept_id != concept_model.id or step.title != concept.title:
                step.concept = concept_model
                step.title = concept.title
                step.status = step.status or "generated"
                step.save(update_fields=["concept", "title", "status"])

            lesson_model = ProgressLesson.objects.filter(step=step).first()
            if not lesson_model or not lesson_model.cards.exists():
                # Phase 1: Generate Lesson Content (Cards, Explanation, Example)
                lesson = self.llm_service.generate_lesson(concept, mastery_ctx)
                lesson_model, _ = ProgressLesson.objects.update_or_create(
                    step=step,
                    defaults={
                        "concept": concept_model,
                        "explanation": lesson.explanation,
                        "example": lesson.example,
                    },
                )

                for card_dto in lesson.cards:
                    ProgressLessonCard.objects.get_or_create(
                        lesson=lesson_model,
                        order_index=card_dto.order_index,
                        defaults={
                            "heading": card_dto.heading,
                            "body": card_dto.body,
                        },
                    )

                # Phase 2: Generate Quiz Questions (Checkpoint & Final Test) using generated Lesson Cards
                mid_card_order = max(0, (len(lesson.cards) // 2) - 1) if lesson.cards else 0
                checkpoint_res = self.llm_service.generate_check_question(
                    concept=concept,
                    lesson=lesson,
                    purpose=QuestionPurpose.CHECKPOINT,
                )
                for question_dto in checkpoint_res.questions:
                    q_model = QuizQuestion.objects.create(
                        lesson=lesson_model,
                        question_type=question_dto.purpose.value,
                        after_card_order=mid_card_order,
                        question_text=question_dto.text,
                        explanation=question_dto.explanation,
                    )
                    for opt_dto in question_dto.options:
                        QuizOption.objects.create(
                            question=q_model,
                            option_text=opt_dto.text,
                            is_correct=opt_dto.is_correct,
                        )

                last_card_order = max(0, len(lesson.cards) - 1) if lesson.cards else 0
                wrapup_res = self.llm_service.generate_check_question(
                    concept=concept,
                    lesson=lesson,
                    purpose=QuestionPurpose.LESSON_WRAPUP,
                )
                for question_dto in wrapup_res.questions:
                    q_model = QuizQuestion.objects.create(
                        lesson=lesson_model,
                        question_type=question_dto.purpose.value,
                        after_card_order=last_card_order,
                        question_text=question_dto.text,
                        explanation=question_dto.explanation,
                    )
                    for opt_dto in question_dto.options:
                        QuizOption.objects.create(
                            question=q_model,
                            option_text=opt_dto.text,
                            is_correct=opt_dto.is_correct,
                        )

            if student:
                initial_status = (
                    ProgressStudentStepStatus.StepStatus.UNLOCKED
                    if order_idx == 1
                    else ProgressStudentStepStatus.StepStatus.LOCKED
                )
                ProgressStudentStepStatus.objects.get_or_create(
                    student=student,
                    step=step,
                    defaults={"status": initial_status},
                )

            created_steps.append(step)

        if student:
            ProgressStudentMaterialProgress.objects.get_or_create(
                student=student,
                material=material,
                defaults={
                    "status": ProgressStudentMaterialProgress.MaterialStatus.IN_PROGRESS,
                    "completion_percent": Decimal("0.00"),
                    "last_active_at": timezone.now(),
                },
            )

        return path_batch, created_steps

    @transaction.atomic
    def submit_checkpoint_answer(
        self,
        student: UsersUser,
        question_id: int,
        selected_option_id: int,
        hints_used: int = 0,
    ) -> Tuple[QuizAttempt, NextActionResult]:
        try:
            question_model = QuizQuestion.objects.select_related(
                "lesson__step__material",
                "lesson__step__concept",
            ).get(id=question_id)
        except QuizQuestion.DoesNotExist:
            raise ValueError(f"Không tìm thấy câu hỏi với ID {question_id}")

        options = list(QuizOption.objects.filter(question=question_model))
        if not options:
            raise ValueError("Câu hỏi không có lựa chọn nào")

        selected_option = next((o for o in options if o.id == selected_option_id), None)
        if not selected_option:
            raise ValueError(f"Lựa chọn ID {selected_option_id} không hợp lệ")

        selected_index = options.index(selected_option)
        question_dto = QuestionDTO(
            text=question_model.question_text,
            options=[
                QuestionOptionDTO(text=o.option_text, is_correct=o.is_correct)
                for o in options
            ],
            explanation=question_model.explanation,
            purpose=QuestionPurpose.CHECKPOINT,
        )

        eval_result = self.llm_service.evaluate_answer(question_dto, selected_index)
        attempt = QuizAttempt.objects.create(
            student=student,
            question=question_model,
            selected_option=selected_option,
            is_correct=eval_result.is_correct,
            hints_used=hints_used,
        )

        step = question_model.lesson.step
        material = step.material
        concept = step.concept

        attempts = QuizAttempt.objects.filter(
            student=student, question__lesson__step=step
        ).order_by("created_at")
        eval_history = [
            AnswerEvaluationResult(
                is_correct=att.is_correct,
                misconception=None if att.is_correct else "Cần ôn tập thêm",
            )
            for att in attempts
        ]

        concept_dto = self._concept_dto_from_model(concept)
        next_action_res = self.llm_service.decide_next_action(concept_dto, eval_history)

        if eval_result.is_correct or next_action_res.action == NextAction.MOVE_NEXT:
            ProgressStudentStepStatus.objects.update_or_create(
                student=student,
                step=step,
                defaults={
                    "status": ProgressStudentStepStatus.StepStatus.COMPLETED,
                    "completed_at": timezone.now(),
                },
            )

            next_step = ProgressPathStep.objects.filter(
                material=material, order_index=step.order_index + 1
            ).first()
            if next_step:
                ProgressStudentStepStatus.objects.update_or_create(
                    student=student,
                    step=next_step,
                    defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED},
                )

        all_steps_count = ProgressPathStep.objects.filter(material=material).count()
        completed_steps_count = ProgressStudentStepStatus.objects.filter(
            student=student,
            step__material=material,
            status=ProgressStudentStepStatus.StepStatus.COMPLETED,
        ).count()

        completion_pct = Decimal("0.00")
        if all_steps_count > 0:
            completion_pct = (
                Decimal(completed_steps_count) / Decimal(all_steps_count) * Decimal("100.00")
            )

        material_status = (
            ProgressStudentMaterialProgress.MaterialStatus.COMPLETED
            if completion_pct >= Decimal("100.00")
            else ProgressStudentMaterialProgress.MaterialStatus.IN_PROGRESS
        )

        ProgressStudentMaterialProgress.objects.update_or_create(
            student=student,
            material=material,
            defaults={
                "completion_percent": round(completion_pct, 2),
                "status": material_status,
                "last_active_at": timezone.now(),
            },
        )

        if next_action_res.needs_next_batch:
            remaining_concepts = [
                self._concept_dto_from_model(step_item.concept)
                for step_item in ProgressPathStep.objects.filter(material=material).exclude(
                    id__in=ProgressStudentStepStatus.objects.filter(
                        student=student,
                        status=ProgressStudentStepStatus.StepStatus.COMPLETED,
                    ).values_list("step_id", flat=True)
                ).filter(
                    lesson__isnull=True,
                ).select_related("concept")
            ]
            if remaining_concepts:
                self.generate_and_save_learning_path_batch(
                    material=material,
                    concepts=remaining_concepts,
                    student=student,
                    batch_size=3,
                )

        return attempt, next_action_res

    def get_question_hint(
        self, question_id: int, level: int, previous_hints: Optional[List[str]] = None
    ) -> HintResult:
        try:
            q_model = QuizQuestion.objects.get(id=question_id)
        except QuizQuestion.DoesNotExist:
            raise ValueError(f"Không tìm thấy câu hỏi với ID {question_id}")

        options = list(QuizOption.objects.filter(question=q_model))
        question_dto = QuestionDTO(
            text=q_model.question_text,
            options=[
                QuestionOptionDTO(text=o.option_text, is_correct=o.is_correct)
                for o in options
            ],
            explanation=q_model.explanation,
            purpose=QuestionPurpose.CHECKPOINT,
        )

        hint_result = self.orchestrator.get_hint(
            question=question_dto,
            level=level,
            previous_hints=previous_hints or [],
        )

        QuizHint.objects.get_or_create(
            question=q_model,
            level=level,
            defaults={"hint_text": hint_result.text},
        )

        return hint_result

    @transaction.atomic
    def send_chat_message(
        self,
        student: UsersUser,
        thread_id: int,
        user_message: str,
        scope: ChatScope,
        learning_context: Optional[LearningContextDTO] = None,
    ) -> ChatMessage:
        if not user_message or not user_message.strip():
            raise LLMEmptyInputError("user_message không được để trống")

        try:
            thread = ChatThread.objects.get(id=thread_id, student=student)
        except ChatThread.DoesNotExist:
            raise ValueError(f"Không tìm thấy thread {thread_id} của student")

        ChatMessage.objects.create(
            thread=thread,
            role=ChatMessage.Role.STUDENT,
            content=user_message.strip(),
        )

        db_messages = ChatMessage.objects.filter(thread=thread).order_by("created_at")
        history_dtos = [
            ChatMessageDTO(
                role=ChatRole.STUDENT if msg.role == ChatMessage.Role.STUDENT else ChatRole.AI,
                content=msg.content,
            )
            for msg in db_messages
        ]

        reply_result = self.llm_service.chat_reply(
            history=history_dtos,
            new_message=user_message.strip(),
            scope=scope,
            learning_context=learning_context,
        )

        if scope == ChatScope.QUIZ:
            current_q = (
                getattr(learning_context, "current_question", None)
                if learning_context
                else None
            )
            # Guardrail is already enforced by the AI adapter; this extra check is kept here
            # to preserve the service-level contract if the adapter is swapped out.
            if current_q is not None:
                from apps.ai.services.guardrail import assert_no_leak_chat

                assert_no_leak_chat(reply_result.reply, current_q)

        ai_message = ChatMessage.objects.create(
            thread=thread,
            role=ChatMessage.Role.AI,
            content=reply_result.reply,
        )

        return ai_message

    def create_chat_thread(
        self,
        student: UsersUser,
        scope: ChatScope,
        scope_id: int,
    ) -> ChatThread:
        if scope == ChatScope.GOAL:
            scope_type = ChatThread.ScopeType.GOAL
        elif scope == ChatScope.MATERIAL:
            scope_type = ChatThread.ScopeType.MATERIAL
        elif scope == ChatScope.QUIZ:
            scope_type = ChatThread.ScopeType.CHECKPOINT_QUESTION
        else:
            raise ValueError(f"Unsupported chat scope: {scope}")

        thread, _ = ChatThread.objects.get_or_create(
            student=student,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        return thread

    def get_thread_messages(
        self,
        student: UsersUser,
        thread_id: int,
    ) -> List[ChatMessage]:
        try:
            thread = ChatThread.objects.get(id=thread_id, student=student)
        except ChatThread.DoesNotExist:
            raise ValueError(f"Không tìm thấy thread {thread_id} của student")

        return list(ChatMessage.objects.filter(thread=thread).order_by("created_at"))

    @transaction.atomic
    def delete_material(self, material_id: int, student_id: Optional[int] = None) -> bool:
        """
        Xóa một LearningMaterial cùng tất cả các dữ liệu liên quan (Goals, Concepts, Steps, Lessons, Quizzes, Progress, ChatThreads).
        """
        try:
            if student_id:
                material = LearningMaterial.objects.get(pk=material_id, user_id=student_id)
            else:
                material = LearningMaterial.objects.get(pk=material_id)
        except LearningMaterial.DoesNotExist:
            return False

        goal_ids = list(material.goals.values_list("id", flat=True))

        from django.db.models import Q
        ChatThread.objects.filter(
            Q(scope_type=ChatThread.ScopeType.MATERIAL, scope_id=material.id) |
            Q(scope_type=ChatThread.ScopeType.GOAL, scope_id__in=goal_ids)
        ).delete()

        material.delete()
        return True

