from django.test import TestCase

from apps.ai.services.dto import ConceptDTO, NextAction, QuestionPurpose
from apps.ai.services.fake import FakeLLMService
from apps.ai.services.orchestrator import LearningOrchestrator


class LLMServiceContractTest(TestCase):
    def setUp(self):
        self.service = FakeLLMService()

    def test_generate_learning_path_batches_by_3(self):
        concepts = [ConceptDTO(id=f"c{i}", title=f"C{i}") for i in range(5)]
        result = self.service.generate_learning_path(concepts, {}, batch_size=3)
        self.assertEqual(len(result.ordered_concept_ids), 3)
        self.assertFalse(result.is_final_batch)

    def test_generate_lesson_has_no_questions(self):
        lesson = self.service.generate_lesson(ConceptDTO(id="c1", title="Test"), {})
        self.assertTrue(hasattr(lesson, "cards"))
        self.assertFalse(hasattr(lesson, "checkpoint_questions"))

    def test_generate_check_question_wrapup_has_more_questions(self):
        concept = ConceptDTO(id="c1", title="Test")
        lesson = self.service.generate_lesson(concept, {})
        checkpoint = self.service.generate_check_question(concept, lesson, QuestionPurpose.CHECKPOINT)
        wrapup = self.service.generate_check_question(concept, lesson, QuestionPurpose.LESSON_WRAPUP)
        self.assertLess(len(checkpoint.questions), len(wrapup.questions))

    def test_decide_next_action_explains_again_when_mostly_wrong(self):
        from apps.ai.services.dto import AnswerEvaluationResult
        concept = ConceptDTO(id="c1", title="Test")
        history = [AnswerEvaluationResult(is_correct=False) for _ in range(4)]
        result = self.service.decide_next_action(concept, history)
        self.assertEqual(result.action, NextAction.EXPLAIN_AGAIN)


class OrchestratorTest(TestCase):
    def setUp(self):
        self.orchestrator = LearningOrchestrator(llm_service=FakeLLMService())

    def test_full_lesson_flow_moves_next_when_correct(self):
        concept = ConceptDTO(id="c1", title="Test concept")
        session = self.orchestrator.start_lesson(concept, mastery_context={})
        question = self.orchestrator.get_checkpoint_question(session)

        correct_index = next(
            i for i, o in enumerate(question.options) if o.is_correct
        )
        decision = self.orchestrator.submit_checkpoint_answer(session, question, correct_index)
        self.assertIn(decision.action, [NextAction.MOVE_NEXT, NextAction.PRACTICE_MORE])