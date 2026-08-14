import os
import unittest
from dotenv import load_dotenv

from django.test import TestCase

from apps.ai.services.adapters.openrouter import OpenRouterAdapter
from apps.ai.services.dto import (
    AnswerEvaluationResult,
    ChatMessageDTO,
    ChatRole,
    ChatScope,
    ConceptDTO,
    LessonDTO,
    NextAction,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from apps.ai.services.guardrail import find_leaked_answer

from apps.ai.services.exceptions import LLMServiceError

load_dotenv()

RUN_INTEGRATION = bool(os.getenv("OPENROUTER_API_KEY"))


@unittest.skipUnless(RUN_INTEGRATION, "Không có OPENROUTER_API_KEY — skip integration test")
class OpenRouterIntegrationTest(TestCase):
    """Gọi API thật — KHÔNG chạy trong CI trừ khi có API key, dùng để test toàn bộ các method của OpenRouterAdapter."""

    def setUp(self):
        try:
            self.adapter = OpenRouterAdapter()
        except LLMServiceError as exc:
            self.skipTest(f"OpenRouter adapter setup error: {exc}")

    def _call_safe(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LLMServiceError as exc:
            if "429" in str(exc) or "Rate limit" in str(exc):
                self.skipTest(f"OpenRouter API rate limit exceeded: {exc}")
            raise

    def test_start_conversation(self):
        result = self._call_safe(
            self.adapter.start_conversation,
            user_message="Tôi muốn ôn tập chương Sóng cơ lớp 12",
            uploaded_material=None,
        )
        self.assertIsNotNone(result.reply)
        self.assertTrue(isinstance(result.ready_to_analyze, bool))


    def test_analyze_material_returns_concepts(self):
        result = self._call_safe(
            self.adapter.analyze_material,
            material_content="Sóng cơ học là dao động lan truyền trong môi trường vật chất...",
            goal="Học sinh hiểu và tính được bước sóng, tần số, vận tốc truyền sóng.",
        )
        self.assertGreater(len(result.concepts), 0)
        self.assertIsInstance(result.concepts[0], ConceptDTO)

    def test_generate_learning_path(self):
        concepts = [
            ConceptDTO(id="c1", title="Định nghĩa sóng cơ"),
            ConceptDTO(id="c2", title="Phương trình sóng"),
            ConceptDTO(id="c3", title="Giao thoa sóng"),
            ConceptDTO(id="c4", title="Sóng dừng"),
        ]
        result = self._call_safe(self.adapter.generate_learning_path, concepts=concepts, mastery_context={}, batch_size=3)
        self.assertGreater(len(result.ordered_concept_ids), 0)
        self.assertLessEqual(len(result.ordered_concept_ids), 3)

    def test_generate_lesson(self):
        concept = ConceptDTO(id="c1", title="Bước sóng và Tần số", description="Khái niệm bước sóng, tần số và chu kỳ sóng")
        lesson = self._call_safe(self.adapter.generate_lesson, concept=concept, mastery_context={})
        self.assertEqual(lesson.concept_id, "c1")
        self.assertTrue(len(lesson.explanation) > 0)
        self.assertIsInstance(lesson.key_points, list)

    def test_generate_check_question(self):
        concept = ConceptDTO(id="c1", title="Bước sóng và Tần số")
        lesson = LessonDTO(
            concept_id="c1",
            explanation="Bước sóng λ là khoảng cách giữa 2 điểm gần nhất trên cùng một phương truyền sóng dao động cùng pha. Công thức v = λ * f.",
            example="Một sóng cơ có tần số 50Hz, bước sóng 0.8m thì vận tốc truyền sóng là 40m/s.",
            key_points=["v = λ * f", "λ = v / f"],
            flashcards=[],
            cards=[],
        )
        result = self._call_safe(
            self.adapter.generate_check_question,
            concept=concept,
            lesson=lesson,
            purpose=QuestionPurpose.CHECKPOINT,
        )
        self.assertGreater(len(result.questions), 0)
        q = result.questions[0]
        self.assertTrue(any(opt.is_correct for opt in q.options))

    def test_evaluate_answer(self):
        question = QuestionDTO(
            text="Công thức tính vận tốc truyền sóng theo bước sóng λ và tần số f là gì?",
            options=[
                QuestionOptionDTO(text="v = λ × f", is_correct=True),
                QuestionOptionDTO(text="v = λ / f", is_correct=False),
            ],
            explanation="v = λ * f",
            purpose=QuestionPurpose.CHECKPOINT,
        )
        # Test trả lời đúng (index 0)
        eval_correct = self._call_safe(self.adapter.evaluate_answer, question=question, selected_option_index=0)
        self.assertTrue(eval_correct.is_correct)

        # Test trả lời sai (index 1)
        eval_incorrect = self._call_safe(self.adapter.evaluate_answer, question=question, selected_option_index=1)
        self.assertFalse(eval_incorrect.is_correct)

    def test_decide_next_action(self):
        concept = ConceptDTO(id="c1", title="Sóng cơ")
        eval_history = [
            AnswerEvaluationResult(is_correct=False, misconception="Nhầm v = λ / f"),
            AnswerEvaluationResult(is_correct=False, misconception="Chưa thuộc công thức"),
        ]
        result = self._call_safe(self.adapter.decide_next_action, concept=concept, evaluation_history=eval_history)
        self.assertIn(
            result.action,
            [NextAction.EXPLAIN_AGAIN, NextAction.SHOW_EXAMPLE, NextAction.PRACTICE_MORE, NextAction.MOVE_NEXT],
        )

    def test_generate_hint_never_leaks_real_answer(self):
        from apps.ai.services.exceptions import LLMInvalidResponseError

        question = QuestionDTO(
            text="Công thức tính vận tốc truyền sóng theo bước sóng λ và tần số f?",
            options=[
                QuestionOptionDTO(text="v = λ × f", is_correct=True),
                QuestionOptionDTO(text="v = λ / f", is_correct=False),
            ],
            explanation="v = λ × f",
            purpose=QuestionPurpose.CHECKPOINT,
        )
        try:
            hint = self._call_safe(self.adapter.generate_hint, question, level=2, previous_hints=[])
            leaked = find_leaked_answer(hint.text, question)
            self.assertIsNone(leaked, f"Real API leak đáp án: {hint.text!r}")
        except LLMInvalidResponseError:
            # Guardrail tại adapter phát hiện leak và chặn thành công
            pass


    def test_chat_reply(self):
        history = [
            ChatMessageDTO(role=ChatRole.STUDENT, content="Chào bạn!"),
            ChatMessageDTO(role=ChatRole.AI, content="Chào em, em muốn học về chủ đề gì?"),
        ]
        result = self._call_safe(
            self.adapter.chat_reply,
            history=history,
            new_message="Giải thích giúp mình khái niệm giao thoa sóng là gì?",
            scope=ChatScope.MATERIAL,
        )
        self.assertTrue(len(result.reply) > 0)