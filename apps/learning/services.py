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
    QuizFinalTest,
    QuizFinalTestQuestion,
    QuizFinalTestOption,
    QuizTestAttempt,
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

    # -------------------------------------------------------------------------
    # 7. Dynamic DB Persistence & Caching for Steps, Cards, & Checkpoints
    # -------------------------------------------------------------------------

    @transaction.atomic
    def get_or_create_step_content(
        self, material: LearningMaterial, step_num: int
    ) -> Tuple[ProgressPathStep, List[ProgressLessonCard], Optional[QuizCheckpointQuestion], List[QuizCheckpointOption], Optional[QuizHint]]:
        """
        Retrieves ProgressPathStep, ProgressLessonCards, QuizCheckpointQuestion, options, and hint
        from database if they exist. If missing, triggers AI generation or fallback generator
        and persists all records into DB.
        """
        step_titles = {
            1: "基礎概念とキーワード",
            2: "基本ルールの理解と応用",
            3: "実践問題・ケーススタディ",
            4: "高度な設定とトラブルシューティング",
            5: "総合理解と最終確認",
        }
        step_title = step_titles.get(step_num, f"ステップ {step_num}")

        step, _ = ProgressPathStep.objects.get_or_create(
            material=material,
            order_index=step_num,
            defaults={"title": step_title},
        )

        existing_cards = list(ProgressLessonCard.objects.filter(step=step).order_by("order_index"))
        existing_question = QuizCheckpointQuestion.objects.filter(step=step).first()

        if existing_cards and existing_question:
            options = list(QuizCheckpointOption.objects.filter(question=existing_question))
            hint = QuizHint.objects.filter(question=existing_question, level=1).first()
            return step, existing_cards, existing_question, options, hint

        content = material.content or ""
        if not content:
            docs = material.documents.all()
            if docs.exists():
                content = "\n".join([d.name for d in docs])

        concept = ConceptDTO(
            id=f"step_{step_num}",
            title=f"{material.title} (Step {step_num})",
            description=content[:1000] if content else material.title,
        )

        # 1. Generate cards if not existing
        if not existing_cards:
            generated_cards = []
            try:
                lesson_dto = self.llm_service.generate_lesson(
                    concept=concept,
                    mastery_context={"step_num": step_num, "material_title": material.title},
                )
                if lesson_dto and lesson_dto.cards:
                    for idx, card_dto in enumerate(lesson_dto.cards):
                        c = ProgressLessonCard.objects.create(
                            step=step,
                            order_index=idx,
                            heading=card_dto.heading,
                            body=card_dto.body,
                        )
                        generated_cards.append(c)
                elif lesson_dto and lesson_dto.flashcards:
                    for idx, fc in enumerate(lesson_dto.flashcards):
                        c = ProgressLessonCard.objects.create(
                            step=step,
                            order_index=idx,
                            heading=fc.front,
                            body=fc.back,
                        )
                        generated_cards.append(c)
            except Exception:
                pass

            if not generated_cards:
                fallback_card_data = [
                    (
                        f"{material.title} - {step_title}",
                        f"【ステップ {step_num}】{material.title} における主要ポイントを学習します。基本定義と重要な概念をしっかり理解しましょう。"
                    ),
                    (
                        f"{material.title} の要点整理",
                        f"{material.title} のステップ {step_num} で押さえるべき重要事項です。実際の演習や問題に当てはめて知識を定着させましょう。"
                    )
                ]
                for idx, (h, b) in enumerate(fallback_card_data):
                    c = ProgressLessonCard.objects.create(
                        step=step,
                        order_index=idx,
                        heading=h,
                        body=b,
                    )
                    generated_cards.append(c)
            existing_cards = generated_cards

        # 2. Generate Checkpoint Question if not existing
        if not existing_question:
            try:
                lesson_dto = LessonDTO(
                    concept_id=f"step_{step_num}",
                    explanation=content[:500] if content else material.title,
                    example="",
                    key_points=[],
                    flashcards=[],
                    cards=[]
                )
                check_res = self.llm_service.generate_check_question(
                    concept=concept,
                    lesson=lesson_dto,
                    purpose=QuestionPurpose.CHECKPOINT
                )
                if check_res and check_res.questions and check_res.questions[0].options:
                    q_dto = check_res.questions[0]
                    existing_question = QuizCheckpointQuestion.objects.create(
                        step=step,
                        after_card_order=len(existing_cards) - 1,
                        question_text=q_dto.text,
                        explanation=q_dto.explanation or f"「{material.title}」のステップ {step_num} で学んだ内容に注目してください。"
                    )
                    for opt_dto in q_dto.options[:4]:
                        QuizCheckpointOption.objects.create(
                            question=existing_question,
                            option_text=opt_dto.text,
                            is_correct=bool(opt_dto.is_correct)
                        )
                    if not QuizCheckpointOption.objects.filter(question=existing_question, is_correct=True).exists():
                        first_opt = QuizCheckpointOption.objects.filter(question=existing_question).first()
                        if first_opt:
                            first_opt.is_correct = True
                            first_opt.save()

                    QuizHint.objects.create(
                        question=existing_question,
                        level=1,
                        hint_text=existing_question.explanation
                    )
            except Exception:
                pass

            if not existing_question:
                fb_questions = {
                    1: (
                        f"【ステップ 1】「{material.title}」における最も基本的な概念・目的は何ですか？",
                        [
                            ("基礎的な定義と核心となるプロセスの理解", True),
                            ("応用段階のトラブルシューティング", False),
                            ("過去の廃止された旧仕様の暗記", False),
                            ("無関係な外部ツールの導入", False),
                        ],
                        f"「{material.title}」の導入部分（ステップ1）では、全体の基本となる定義と核心プロセスに注目しましょう。"
                    ),
                    2: (
                        f"【ステップ 2】「{material.title}」の基本ルールおよび構成要素として正しいものはどれですか？",
                        [
                            ("正確な手順に従った構成要素の組み合わせ", True),
                            ("ルールの無視と無計画な実行", False),
                            ("静的データの完全な削除", False),
                            ("一時的なキャッシュの初期化のみ", False),
                        ],
                        f"「{material.title}」の基本原則（ステップ2）は、正しい手順と構成要素の整合性に基づいています。"
                    ),
                    3: (
                        f"【ステップ 3】「{material.title}」を実際の課題に適用する際、最も推奨されるアプローチはどれですか？",
                        [
                            ("具体的な事例・ケーススタディに沿った実践的検証", True),
                            ("理論のみで実践を一切行わないアプローチ", False),
                            ("過去のエラーログを全て無視すること", False),
                            ("設定ファイルをランダムに変更すること", False),
                        ],
                        f"「{material.title}」の実践問題（ステップ3）では、具体例や実際の利用シナリオを意識するのが効果的です。"
                    ),
                    4: (
                        f"【ステップ 4】「{material.title}」の高度な設定や問題発生時の対処法として最適なものはどれですか？",
                        [
                            ("原因の分析と最適化手法の段階的適用", True),
                            ("問題の放置とログの削除", False),
                            ("システムの再起動のみで対処を終わらせる", False),
                            ("未検証のスクリプトを即座に本番実行する", False),
                        ],
                        f"「{material.title}」のトラブルシューティング（ステップ4）では、体系的な原因分析と最適な設定変更が鍵です。"
                    ),
                    5: (
                        f"【ステップ 5】「{material.title}」の全体を通して、習得すべき総合的なゴールは何ですか？",
                        [
                            ("全体像の体系的理解と自立的な応用・解決能力", True),
                            ("単一の用語のみの暗記", False),
                            ("環境構築の途中断念", False),
                            ("理論と実践の切り離し", False),
                        ],
                        f"「{material.title}」の最終確認（ステップ5）では、これまでのステップを総合した実践力・応用力をチェックします。"
                    ),
                }

                q_text, opts_raw, hint_str = fb_questions.get(
                    step_num,
                    (
                        f"【ステップ {step_num}】「{material.title}」に関する理解度確認問題です。正しい説明はどれですか？",
                        [
                            (f"「{material.title}」の適切な理解と活用", True),
                            ("誤った解釈に基づく操作", False),
                            ("無関係な定義", False),
                            ("不十分な確認", False),
                        ],
                        f"「{material.title}」のステップ {step_num} で学んだ内容を思い出して選択してください。"
                    )
                )

                existing_question = QuizCheckpointQuestion.objects.create(
                    step=step,
                    after_card_order=len(existing_cards) - 1,
                    question_text=q_text,
                    explanation=hint_str,
                )
                for opt_text, is_corr in opts_raw:
                    QuizCheckpointOption.objects.create(
                        question=existing_question,
                        option_text=opt_text,
                        is_correct=is_corr,
                    )
                QuizHint.objects.create(
                    question=existing_question,
                    level=1,
                    hint_text=hint_str,
                )

        options = list(QuizCheckpointOption.objects.filter(question=existing_question))
        hint = QuizHint.objects.filter(question=existing_question, level=1).first()

        return step, existing_cards, existing_question, options, hint

    # -------------------------------------------------------------------------
    # 8. Final Test Engine & Persistence
    # -------------------------------------------------------------------------

    @transaction.atomic
    def get_or_create_final_test(
        self, material: LearningMaterial
    ) -> Tuple[QuizFinalTest, List[QuizFinalTestQuestion]]:
        """
        Retrieves QuizFinalTest and its questions/options for a LearningMaterial.
        If missing, triggers AI generation or fallback generator and persists all DB records.
        """
        final_test, _ = QuizFinalTest.objects.get_or_create(
            material=material,
            defaults={"pass_threshold": Decimal("80.00")}
        )

        questions = list(QuizFinalTestQuestion.objects.filter(final_test=final_test).order_by("order_index"))
        if questions:
            return final_test, questions

        fb_questions_data = [
            (
                f"「{material.title}」の全般における最も中心的なコンセプトは何ですか？",
                [
                    ("核心となる定義と基本構造の適切な理解", True),
                    ("無関係な旧システムの維持", False),
                    ("設定ファイルのランダム消去", False),
                    ("エラーメッセージの無視", False),
                ],
                f"「{material.title}」の全体を通して学んだ基本定義を思い出してください。"
            ),
            (
                f"「{material.title}」を安全かつ効率的に運用するための基本ルールはどれですか？",
                [
                    ("推奨される標準手順とパラメータ設計の遵守", True),
                    ("ドキュメントの非公開化とルールの無視", False),
                    ("アクセス権限の完全開放", False),
                    ("ログの自動削除設定", False),
                ],
                f"「{material.title}」における正しい設計・運用ルールの重要性がポイントです。"
            ),
            (
                f"「{material.title}」を実際の開発・学習課題に適用する際のベストプラクティスはどれですか？",
                [
                    ("段階的な検証とケーススタディに基づいた実践", True),
                    ("テストなしでの本番一括適用", False),
                    ("過去のコードを全て破棄すること", False),
                    ("例外処理の全削除", False),
                ],
                f"「{material.title}」の応用・実践問題における標準的なステップに注目してください。"
            ),
            (
                f"「{material.title}」で問題が発生した場合のトラブルシューティングとして最も効果的な方法はどれですか？",
                [
                    ("エラーの原因分析とログ・トレースに基づいた段階的修正", True),
                    ("システムの再インストールを無制限に繰り返す", False),
                    ("エラーコードの検索を放棄する", False),
                    ("古いバージョンへの無計画なダウングレード", False),
                ],
                f"「{material.title}」のトラブルシューティングにおける体系的な検証手順が鍵となります。"
            ),
            (
                f"「{material.title}」の習得によって得られる総合的な成果として適切なものはどれですか？",
                [
                    ("全体の体系的把握と自立的な問題解決能力の定着", True),
                    ("単一の用語の暗記のみ", False),
                    ("実行環境の破棄", False),
                    ("理論のみで実践できない状態", False),
                ],
                f"「{material.title}」の総合目標は、自立した応用力と問題解決能力の習得です。"
            ),
        ]

        created_questions = []
        for idx, (q_text, opts_raw, exp_text) in enumerate(fb_questions_data, 1):
            q_model = QuizFinalTestQuestion.objects.create(
                final_test=final_test,
                order_index=idx,
                question_text=q_text,
                explanation=exp_text,
            )
            for opt_text, is_corr in opts_raw:
                QuizFinalTestOption.objects.create(
                    question=q_model,
                    option_text=opt_text,
                    is_correct=is_corr,
                )
            created_questions.append(q_model)

        return final_test, created_questions

    @transaction.atomic
    def submit_final_test_answers(
        self,
        student: UsersUser,
        final_test: QuizFinalTest,
        user_answers: dict,
    ) -> QuizTestAttempt:
        """
        Evaluates final test answers, calculates score %, checks pass threshold (80%),
        records QuizTestAttempt, and updates material progress if passed.
        """
        questions = QuizFinalTestQuestion.objects.filter(final_test=final_test)
        total_questions = questions.count()
        if total_questions == 0:
            raise ValueError("Final Test に問題が存在しません")

        correct_count = 0
        for q in questions:
            opts = list(QuizFinalTestOption.objects.filter(question=q))
            selected = None

            user_ans = (
                user_answers.get(q.id)
                or user_answers.get(str(q.id))
                or user_answers.get(q.order_index)
                or user_answers.get(str(q.order_index))
                or user_answers.get(q.order_index - 1)
                or user_answers.get(str(q.order_index - 1))
            )

            if user_ans is not None:
                if isinstance(user_ans, int) and user_ans < len(opts):
                    selected = opts[user_ans]
                else:
                    selected = next((o for o in opts if str(o.id) == str(user_ans)), None)

            if selected and selected.is_correct:
                correct_count += 1

        score_percent = Decimal((correct_count / total_questions) * 100).quantize(Decimal("0.01"))
        passed = score_percent >= final_test.pass_threshold

        existing_attempts = QuizTestAttempt.objects.filter(student=student, final_test=final_test).count()
        attempt_number = existing_attempts + 1

        attempt = QuizTestAttempt.objects.create(
            student=student,
            final_test=final_test,
            score_percent=score_percent,
            passed=passed,
            attempt_number=attempt_number,
        )

        if passed:
            ProgressStudentMaterialProgress.objects.update_or_create(
                student=student,
                material=final_test.material,
                defaults={
                    "completion_percent": Decimal("100.00"),
                    "status": ProgressStudentMaterialProgress.MaterialStatus.COMPLETED,
                    "last_active_at": timezone.now(),
                }
            )

        return attempt


