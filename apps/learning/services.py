from typing import List, Optional, Tuple
from decimal import Decimal
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
    LessonDTO,
    NextAction,
    NextActionResult,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from apps.ai.services.exceptions import (
    LLMEmptyInputError,
    LLMInvalidResponseError,
    LLMServiceError,
)
from apps.ai.services.factory import get_llm_service
from apps.ai.services.guardrail import assert_no_leak, assert_no_leak_chat
from apps.ai.services.orchestrator import LearningOrchestrator, LessonSessionState
from apps.learning.models import (
    AssessmentSkill,
    AssessmentSkillCheck,
    ChatMessage,
    ChatThread,
    LearningGoal,
    LearningMaterial,
    ProgressLessonCard,
    ProgressPathStep,
    ProgressStudentMaterialProgress,
    ProgressStudentStepStatus,
    QuizCheckpointAttempt,
    QuizCheckpointOption,
    QuizCheckpointQuestion,
    QuizHint,
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

    # -------------------------------------------------------------------------
    # 1. Onboarding & Material Analysis
    # -------------------------------------------------------------------------

    def start_onboarding_conversation(
        self, user_message: str, uploaded_material: Optional[str] = None
    ):
        """Start or continue onboarding dialogue to detect goal or material."""
        if not user_message or not user_message.strip():
            raise LLMEmptyInputError("user_message không được để trống")
        return self.llm_service.start_conversation(user_message, uploaded_material)

    @transaction.atomic
    def process_and_create_material(
        self, title: str, content: str, goal_title: str
    ) -> Tuple[LearningMaterial, AnalyzeMaterialResult]:
        """
        Creates a LearningMaterial, invokes analyze_material(), and stores
        LearningGoal and AssessmentSkill objects in the database.
        """
        if not title or not title.strip():
            raise ValueError("Tiêu đề tài liệu không được để trống")
        if not content or not content.strip():
            raise LLMEmptyInputError("Nội dung tài liệu không được để trống")

        material = LearningMaterial.objects.create(
            title=title.strip(),
            content=content.strip(),
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

        for skill_name in analysis.suggested_skills:
            AssessmentSkill.objects.create(goal=goal, name=skill_name)

        if not analysis.suggested_skills and analysis.concepts:
            for concept in analysis.concepts:
                AssessmentSkill.objects.create(goal=goal, name=concept.title)

        return material, analysis

    # -------------------------------------------------------------------------
    # 2. Self-Check & Skill Assessment
    # -------------------------------------------------------------------------

    @transaction.atomic
    def record_skill_checks(
        self, student: UsersUser, skill_ids_known: List[int]
    ):
        """Record student self-check for skills."""
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

    # -------------------------------------------------------------------------
    # 3. Learning Path Generation & DB Persistence
    # -------------------------------------------------------------------------

    @transaction.atomic
    def generate_and_save_learning_path_batch(
        self,
        material: LearningMaterial,
        concepts: List[ConceptDTO],
        student: Optional[UsersUser] = None,
        mastery_context: Optional[dict] = None,
        batch_size: int = 3,
    ) -> Tuple[LearningPathBatchResult, List[ProgressPathStep]]:
        """
        Calls generate_learning_path, generates lessons, cards, and checkpoint questions,
        and saves them to database tables within a single atomic transaction.
        """
        mastery_ctx = mastery_context or {}
        path_batch = self.llm_service.generate_learning_path(
            concepts=concepts,
            mastery_context=mastery_ctx,
            batch_size=batch_size,
        )

        created_steps: List[ProgressPathStep] = []
        existing_step_count = ProgressPathStep.objects.filter(material=material).count()

        concept_map = {c.id: c for c in concepts}

        for idx, concept_id in enumerate(path_batch.ordered_concept_ids):
            concept = concept_map.get(
                concept_id, ConceptDTO(id=concept_id, title=f"Concept {concept_id}")
            )
            order_idx = existing_step_count + idx + 1

            step, _ = ProgressPathStep.objects.get_or_create(
                material=material,
                order_index=order_idx,
                defaults={"title": concept.title},
            )

            # Generate Lesson content
            lesson = self.llm_service.generate_lesson(concept, mastery_ctx)

            # Save Lesson Cards
            for card_dto in lesson.cards:
                ProgressLessonCard.objects.get_or_create(
                    step=step,
                    order_index=card_dto.order_index,
                    defaults={
                        "heading": card_dto.heading,
                        "body": card_dto.body,
                    },
                )

            # Generate and save Checkpoint Questions
            checkpoint_res = self.llm_service.generate_check_question(
                concept=concept,
                lesson=lesson,
                purpose=QuestionPurpose.CHECKPOINT,
            )

            last_card_order = len(lesson.cards) - 1 if lesson.cards else 0

            for question_dto in checkpoint_res.questions:
                q_model = QuizCheckpointQuestion.objects.create(
                    step=step,
                    after_card_order=last_card_order,
                    question_text=question_dto.text,
                    explanation=question_dto.explanation,
                )
                for opt_dto in question_dto.options:
                    QuizCheckpointOption.objects.create(
                        question=q_model,
                        option_text=opt_dto.text,
                        is_correct=opt_dto.is_correct,
                    )

            if student:
                # Step status setup
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
            # Update overall progress
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

    # -------------------------------------------------------------------------
    # 4. Checkpoint Answer Submission & Mastery Evaluation
    # -------------------------------------------------------------------------

    @transaction.atomic
    def submit_checkpoint_answer(
        self,
        student: UsersUser,
        question_id: int,
        selected_option_id: int,
        hints_used: int = 0,
    ) -> Tuple[QuizCheckpointAttempt, NextActionResult]:
        """
        Evaluates student answer choice, saves attempt, updates step status,
        determines next action, and triggers next path batch if required.
        """
        try:
            question_model = QuizCheckpointQuestion.objects.select_related("step__material").get(
                id=question_id
            )
        except QuizCheckpointQuestion.DoesNotExist:
            raise ValueError(f"Không tìm thấy câu hỏi với ID {question_id}")

        options = list(QuizCheckpointOption.objects.filter(question=question_model))
        if not options:
            raise ValueError("Câu hỏi không có lựa chọn nào")

        selected_option = next((o for o in options if o.id == selected_option_id), None)
        if not selected_option:
            raise ValueError(f"Lựa chọn ID {selected_option_id} không hợp lệ")

        selected_index = options.index(selected_option)

        # Convert to DTO
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

        attempt = QuizCheckpointAttempt.objects.create(
            student=student,
            question=question_model,
            selected_option=selected_option,
            is_correct=eval_result.is_correct,
            hints_used=hints_used,
        )

        step = question_model.step
        material = step.material

        # Collect evaluation history for this concept/step
        attempts = QuizCheckpointAttempt.objects.filter(
            student=student, question__step=step
        ).order_by("created_at")

        eval_history = [
            AnswerEvaluationResult(
                is_correct=att.is_correct,
                misconception=None if att.is_correct else "Cần ôn tập thêm",
            )
            for att in attempts
        ]

        concept_dto = ConceptDTO(id=str(step.id), title=step.title)
        next_action_res = self.llm_service.decide_next_action(concept_dto, eval_history)

        # Update step progress if correct / MOVE_NEXT
        if eval_result.is_correct or next_action_res.action == NextAction.MOVE_NEXT:
            ProgressStudentStepStatus.objects.update_or_create(
                student=student,
                step=step,
                defaults={
                    "status": ProgressStudentStepStatus.StepStatus.COMPLETED,
                    "completed_at": timezone.now(),
                },
            )

            # Unlock next step if present
            next_step = ProgressPathStep.objects.filter(
                material=material, order_index=step.order_index + 1
            ).first()

            if next_step:
                ProgressStudentStepStatus.objects.update_or_create(
                    student=student,
                    step=next_step,
                    defaults={"status": ProgressStudentStepStatus.StepStatus.UNLOCKED},
                )

        # Update material progress
        all_steps_count = ProgressPathStep.objects.filter(material=material).count()
        completed_steps_count = ProgressStudentStepStatus.objects.filter(
            student=student,
            step__material=material,
            status=ProgressStudentStepStatus.StepStatus.COMPLETED,
        ).count()

        completion_pct = Decimal("0.00")
        if all_steps_count > 0:
            completion_pct = Decimal(completed_steps_count) / Decimal(all_steps_count) * Decimal("100.00")

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

        # Handle needs_next_batch == True
        if next_action_res.needs_next_batch:
            remaining_concepts = [
                ConceptDTO(id=f"step_{s.id}", title=s.title)
                for s in ProgressPathStep.objects.filter(material=material).exclude(
                    id__in=ProgressStudentStepStatus.objects.filter(
                        student=student,
                        status=ProgressStudentStepStatus.StepStatus.COMPLETED,
                    ).values_list("step_id", flat=True)
                )
            ]
            if remaining_concepts:
                self.generate_and_save_learning_path_batch(
                    material=material,
                    concepts=remaining_concepts,
                    student=student,
                    batch_size=3,
                )

        return attempt, next_action_res

    # -------------------------------------------------------------------------
    # 5. Hint Generation with Guardrail
    # -------------------------------------------------------------------------

    def get_question_hint(
        self, question_id: int, level: int, previous_hints: Optional[List[str]] = None
    ) -> HintResult:
        """
        Generates hint for a checkpoint question, applying runtime guardrail to prevent answer leakage.
        """
        try:
            q_model = QuizCheckpointQuestion.objects.get(id=question_id)
        except QuizCheckpointQuestion.DoesNotExist:
            raise ValueError(f"Không tìm thấy câu hỏi với ID {question_id}")

        options = list(QuizCheckpointOption.objects.filter(question=q_model))
        question_dto = QuestionDTO(
            text=q_model.question_text,
            options=[
                QuestionOptionDTO(text=o.option_text, is_correct=o.is_correct)
                for o in options
            ],
            explanation=q_model.explanation,
            purpose=QuestionPurpose.CHECKPOINT,
        )

        prev_hints = previous_hints or []
        hint_result = self.orchestrator.get_hint(
            question=question_dto, level=level, previous_hints=prev_hints
        )

        # Ensure in DB
        QuizHint.objects.get_or_create(
            question=q_model,
            level=level,
            defaults={"hint_text": hint_result.text},
        )

        return hint_result

    # -------------------------------------------------------------------------
    # 6. Chat with Scope & Guardrail
    # -------------------------------------------------------------------------

    @transaction.atomic
    def send_chat_message(
        self,
        student: UsersUser,
        thread_id: int,
        user_message: str,
        scope: ChatScope,
        learning_context: Optional[LearningContextDTO] = None,
    ) -> ChatMessage:
        """
        Sends a user chat message, calls chat_reply, applies guardrail for QUIZ scope,
        and records both user & AI messages in the ChatThread.
        """
        if not user_message or not user_message.strip():
            raise LLMEmptyInputError("user_message không được để trống")

        try:
            thread = ChatThread.objects.get(id=thread_id, student=student)
        except ChatThread.DoesNotExist:
            raise ValueError(f"Không tìm thấy thread {thread_id} của student")

        # Record student message
        ChatMessage.objects.create(
            thread=thread,
            role=ChatMessage.Role.STUDENT,
            content=user_message.strip(),
        )

        # Load history DTOs
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

        # Guardrail check for QUIZ scope
        if scope == ChatScope.QUIZ:
            current_q = getattr(learning_context, "current_question", None) if learning_context else None
            assert_no_leak_chat(reply_result.reply, current_q)

        # Record AI reply message
        ai_message = ChatMessage.objects.create(
            thread=thread,
            role=ChatMessage.Role.AI,
            content=reply_result.reply,
        )

        return ai_message
