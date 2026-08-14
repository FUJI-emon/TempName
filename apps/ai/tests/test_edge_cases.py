from django.test import TestCase

from apps.ai.services.dto import ConceptDTO, QuestionDTO, QuestionOptionDTO, QuestionPurpose
from apps.ai.services.exceptions import LLMEmptyInputError
from apps.ai.services.fake import FakeLLMService


class EdgeCaseTest(TestCase):
    def setUp(self):
        self.service = FakeLLMService()

    def test_analyze_material_rejects_empty_content(self):
        with self.assertRaises(LLMEmptyInputError):
            self.service.analyze_material(material_content="", goal="Học X")

    def test_analyze_material_rejects_whitespace_only_content(self):
        with self.assertRaises(LLMEmptyInputError):
            self.service.analyze_material(material_content="   \n  ", goal="Học X")

    def test_generate_learning_path_with_empty_concepts_returns_empty_final_batch(self):
        result = self.service.generate_learning_path([], {}, batch_size=3)
        self.assertEqual(result.ordered_concept_ids, [])
        self.assertTrue(result.is_final_batch)

    def test_decide_next_action_with_empty_history_moves_next(self):
        concept = ConceptDTO(id="c1", title="Test")
        result = self.service.decide_next_action(concept, [])
        self.assertEqual(result.concept_id, "c1")

    def test_evaluate_answer_with_out_of_range_index_raises(self):
        question = QuestionDTO(
            text="Q?",
            options=[QuestionOptionDTO(text="A", is_correct=True)],
            explanation="",
            purpose=QuestionPurpose.CHECKPOINT,
        )
        with self.assertRaises(IndexError):
            self.service.evaluate_answer(question, selected_option_index=5)