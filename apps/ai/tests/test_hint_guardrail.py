from django.test import TestCase

from apps.ai.services.dto import QuestionDTO, QuestionOptionDTO, QuestionPurpose
from apps.ai.services.exceptions import LLMInvalidResponseError
from apps.ai.services.fake import FakeLLMService
from apps.ai.services.guardrail import assert_no_leak, find_leaked_answer
from apps.ai.services.orchestrator import LearningOrchestrator


def _make_question():
    return QuestionDTO(
        text="Vận tốc truyền sóng được tính như thế nào?",
        options=[
            QuestionOptionDTO(
                text="Vận tốc truyền sóng bằng bước sóng nhân tần số",
                is_correct=True,
            ),
            QuestionOptionDTO(text="Vận tốc bằng bước sóng chia biên độ", is_correct=False),
        ],
        explanation="v = λ × f",
        purpose=QuestionPurpose.CHECKPOINT,
    )


class HintGuardrailTest(TestCase):
    def setUp(self):
        self.service = FakeLLMService()
        self.question = _make_question()

    def test_fake_service_hints_do_not_leak_across_all_levels(self):
        previous = []
        for level in range(1, 4):
            hint = self.service.generate_hint(self.question, level, previous)
            leaked = find_leaked_answer(hint.text, self.question)
            self.assertIsNone(leaked, f"Level {level} hint leak: {hint.text!r}")
            previous.append(hint.text)

    def test_direct_answer_copy_is_detected(self):
        hint_text = "Đáp án là: vận tốc truyền sóng bằng bước sóng nhân tần số"
        self.assertIsNotNone(find_leaked_answer(hint_text, self.question))

    def test_reordered_paraphrase_is_detected(self):
        # đảo thứ tự + chèn từ đệm, không copy nguyên văn nhưng vẫn leak nội dung
        hint_text = "thì em nhân tần số với bước sóng vào là ra vận tốc truyền sóng thôi"
        self.assertIsNotNone(find_leaked_answer(hint_text, self.question))

    def test_conceptual_hint_pointing_to_relation_is_not_flagged(self):
        hint_text = "Hãy nghĩ xem bước sóng và tần số liên quan với nhau như thế nào."
        self.assertIsNone(find_leaked_answer(hint_text, self.question))

    def test_assert_no_leak_raises_on_violation(self):
        with self.assertRaises(LLMInvalidResponseError):
            assert_no_leak("bước sóng nhân tần số ra vận tốc truyền sóng", self.question)

    def test_hint_levels_are_not_verbatim_duplicates(self):
        previous = []
        texts = []
        for level in range(1, 4):
            hint = self.service.generate_hint(self.question, level, previous)
            texts.append(hint.text)
            previous.append(hint.text)
        self.assertEqual(len(texts), len(set(texts)))

    def test_orchestrator_get_hint_retries_then_raises_if_still_leaking(self):
        """Giả lập 1 service luôn leak để test cơ chế retry-rồi-raise của orchestrator."""
        from apps.ai.services.dto import HintResult

        class AlwaysLeakingService(FakeLLMService):
            def generate_hint(self, question, level, previous_hints):
                return HintResult(
                    level=level,
                    text="vận tốc truyền sóng bằng bước sóng nhân tần số",
                )

        orchestrator = LearningOrchestrator(llm_service=AlwaysLeakingService())
        with self.assertRaises(LLMInvalidResponseError):
            orchestrator.get_hint(self.question, level=1, previous_hints=[])