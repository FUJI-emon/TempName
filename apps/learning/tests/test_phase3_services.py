from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase, Client
from django.urls import reverse

from apps.ai.services.dto import (
    AnalyzeMaterialResult,
    AnswerEvaluationResult,
    ChatReplyResult,
    ChatScope,
    ConceptDTO,
    HintResult,
    LearningPathBatchResult,
    NextAction,
    NextActionResult,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from apps.ai.services.fake import FakeLLMService
from apps.learning.models import (
    AssessmentSkill,
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
    UsersUser,
)
from apps.learning.services import LearningApplicationService


class Phase3ServicesTestCase(TestCase):
    """Unit and Database interaction tests for Phase 3 integration."""

    def setUp(self):
        self.fake_llm = FakeLLMService()
        self.service = LearningApplicationService(llm_service=self.fake_llm)
        self.student = UsersUser.objects.create(
            username="teststudent",
            email="test@example.com",
            password_hash="hashed_pw",
            display_name="Test Student",
        )

    def test_process_and_create_material_success(self):
        """Test creating material, calling analyze_material, and persisting to DB."""
        material, analysis = self.service.process_and_create_material(
            title="Vật lý 12 - Sóng cơ",
            content="Nội dung bài học sóng cơ...",
            goal_title="Hiểu sóng cơ",
        )
        self.assertIsNotNone(material.id)
        self.assertEqual(material.title, "Vật lý 12 - Sóng cơ")
        self.assertEqual(LearningGoal.objects.filter(material=material).count(), 1)
        self.assertGreater(AssessmentSkill.objects.count(), 0)

    def test_process_and_create_material_invalid_input(self):
        """Test input validation for material creation."""
        with self.assertRaises(ValueError):
            self.service.process_and_create_material(title="", content="valid", goal_title="g")
        with self.assertRaises(LLMEmptyInputError):
            self.service.process_and_create_material(title="title", content="", goal_title="g")

    def test_generate_and_save_learning_path_batch_success(self):
        """Test generating learning path batch and writing steps/cards/questions to DB."""
        material = LearningMaterial.objects.create(
            title="Đại số 12", content="Hàm số và đồ thị"
        )
        concepts = [
            ConceptDTO(id="c1", title="Đơn điệu của hàm số"),
            ConceptDTO(id="c2", title="Cực trị hàm số"),
        ]

        batch_res, steps = self.service.generate_and_save_learning_path_batch(
            material=material,
            concepts=concepts,
            student=self.student,
            batch_size=2,
        )

        self.assertEqual(len(steps), 2)
        self.assertEqual(ProgressPathStep.objects.filter(material=material).count(), 2)
        self.assertGreater(ProgressLessonCard.objects.filter(step=steps[0]).count(), 0)
        self.assertGreater(QuizCheckpointQuestion.objects.filter(step=steps[0]).count(), 0)

        # Check progress initialization
        prog = ProgressStudentMaterialProgress.objects.get(
            student=self.student, material=material
        )
        self.assertEqual(prog.status, ProgressStudentMaterialProgress.MaterialStatus.IN_PROGRESS)

    def test_submit_checkpoint_answer_updates_progress(self):
        """Test submitting checkpoint answer and updating student progress."""
        material = LearningMaterial.objects.create(
            title="Hoá học 12", content="Este - Lipit"
        )
        step = ProgressPathStep.objects.create(
            material=material, order_index=1, title="Khái niệm Este"
        )
        q = QuizCheckpointQuestion.objects.create(
            step=step,
            after_card_order=0,
            question_text="Este có mùi đặc trưng gì?",
            explanation="Mùi thơm hoa quả",
        )
        opt_correct = QuizCheckpointOption.objects.create(
            question=q, option_text="Mùi thơm hoa quả", is_correct=True
        )
        opt_wrong = QuizCheckpointOption.objects.create(
            question=q, option_text="Mùi hắc", is_correct=False
        )

        attempt, next_action_res = self.service.submit_checkpoint_answer(
            student=self.student,
            question_id=q.id,
            selected_option_id=opt_correct.id,
        )

        self.assertTrue(attempt.is_correct)
        self.assertEqual(attempt.selected_option, opt_correct)

        # Check step status completed
        step_status = ProgressStudentStepStatus.objects.get(
            student=self.student, step=step
        )
        self.assertEqual(step_status.status, ProgressStudentStepStatus.StepStatus.COMPLETED)

        # Check material completion percent
        mat_prog = ProgressStudentMaterialProgress.objects.get(
            student=self.student, material=material
        )
        self.assertEqual(mat_prog.completion_percent, Decimal("100.00"))

    def test_submit_checkpoint_answer_invalid_option(self):
        """Test submitting non-existent option ID raises ValueError."""
        material = LearningMaterial.objects.create(title="T1", content="C1")
        step = ProgressPathStep.objects.create(material=material, order_index=1, title="S1")
        q = QuizCheckpointQuestion.objects.create(step=step, after_card_order=0, question_text="Q?", explanation="E")
        QuizCheckpointOption.objects.create(question=q, option_text="Opt", is_correct=True)

        with self.assertRaises(ValueError):
            self.service.submit_checkpoint_answer(
                student=self.student,
                question_id=q.id,
                selected_option_id=9999,
            )

    def test_needs_next_batch_triggers_path_generation(self):
        """Test that when decide_next_action returns needs_next_batch=True, next batch is processed."""
        mock_llm = MagicMock()
        mock_llm.evaluate_answer.return_value = AnswerEvaluationResult(is_correct=True)
        mock_llm.decide_next_action.return_value = NextActionResult(
            action=NextAction.MOVE_NEXT, concept_id="c1", needs_next_batch=True
        )
        mock_llm.generate_learning_path.return_value = LearningPathBatchResult(
            ordered_concept_ids=["c2"], is_final_batch=True
        )
        mock_llm.generate_lesson.return_value = self.fake_llm.generate_lesson(
            ConceptDTO(id="c2", title="C2"), {}
        )
        mock_llm.generate_check_question.return_value = self.fake_llm.generate_check_question(
            ConceptDTO(id="c2", title="C2"), None, QuestionPurpose.CHECKPOINT
        )

        service = LearningApplicationService(llm_service=mock_llm)

        material = LearningMaterial.objects.create(title="Mat", content="Cont")
        step1 = ProgressPathStep.objects.create(material=material, order_index=1, title="S1")
        step2 = ProgressPathStep.objects.create(material=material, order_index=2, title="S2")

        q = QuizCheckpointQuestion.objects.create(step=step1, after_card_order=0, question_text="Q", explanation="E")
        opt = QuizCheckpointOption.objects.create(question=q, option_text="A", is_correct=True)

        attempt, next_action_res = service.submit_checkpoint_answer(
            student=self.student, question_id=q.id, selected_option_id=opt.id
        )

        self.assertTrue(next_action_res.needs_next_batch)
        # Verify generate_learning_path was called for next batch
        self.assertTrue(mock_llm.generate_learning_path.called)

    def test_get_question_hint_guardrail_enforcement(self):
        """Test that get_question_hint generates hint safely and raises LLMInvalidResponseError if answer leaks."""
        material = LearningMaterial.objects.create(title="Mat", content="Cont")
        step = ProgressPathStep.objects.create(material=material, order_index=1, title="S1")
        q = QuizCheckpointQuestion.objects.create(
            step=step, after_card_order=0, question_text="Vận tốc v tính bằng gì?", explanation="E"
        )
        QuizCheckpointOption.objects.create(question=q, option_text="v = lambda * f", is_correct=True)

        # Test normal safe hint
        hint_res = self.service.get_question_hint(question_id=q.id, level=1)
        self.assertIsNotNone(hint_res.text)

        # Test leaking hint raises LLMInvalidResponseError
        leaking_llm = MagicMock()
        leaking_llm.generate_hint.return_value = HintResult(level=1, text="Đáp án chính là v = lambda * f")
        service_leaking = LearningApplicationService(llm_service=leaking_llm)

        with self.assertRaises(LLMInvalidResponseError):
            service_leaking.get_question_hint(question_id=q.id, level=1)

    def test_send_chat_message_quiz_scope_guardrail(self):
        """Test chat message handling and guardrail on QUIZ scope."""
        thread = ChatThread.objects.create(
            student=self.student,
            scope_type=ChatThread.ScopeType.MATERIAL,
            scope_id=1,
        )

        ai_msg = self.service.send_chat_message(
            student=self.student,
            thread_id=thread.id,
            user_message="Giải thích giúp mình khái niệm sóng cơ",
            scope=ChatScope.MATERIAL,
        )

        self.assertEqual(ai_msg.role, ChatMessage.Role.AI)
        self.assertEqual(ChatMessage.objects.filter(thread=thread).count(), 2)

    def test_llm_service_error_handling(self):
        """Test LLM service failure propagation."""
        failing_llm = MagicMock()
        failing_llm.analyze_material.side_effect = LLMServiceError("Kết nối OpenRouter bị timeout")
        service_failing = LearningApplicationService(llm_service=failing_llm)

        with self.assertRaises(LLMServiceError):
            service_failing.process_and_create_material(
                title="T", content="C", goal_title="G"
            )


class Phase3ViewsTestCase(TestCase):
    """HTTP view endpoint tests for Phase 3."""

    def setUp(self):
        self.client = Client()
        self.student = UsersUser.objects.create(
            username="viewstudent",
            email="view@example.com",
            password_hash="pw",
            display_name="View Student",
        )

    def test_onboarding_view(self):
        response = self.client.post(
            reverse("learning:onboarding"),
            data={"user_message": "Tôi muốn học Toán 12"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")

    def test_create_material_view(self):
        response = self.client.post(
            reverse("learning:create_material"),
            data={
                "title": "Sinh học 12",
                "content": "Di truyền học quần thể...",
                "goal_title": "Nắm vững di truyền",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("material_id", json_data)

    def test_get_hint_view(self):
        material = LearningMaterial.objects.create(title="M", content="C")
        step = ProgressPathStep.objects.create(material=material, order_index=1, title="S")
        q = QuizCheckpointQuestion.objects.create(step=step, after_card_order=0, question_text="Q?", explanation="E")
        QuizCheckpointOption.objects.create(question=q, option_text="A", is_correct=True)

        url = reverse("learning:get_hint", kwargs={"question_id": q.id, "level": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("hint", json_data)
