from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase, Client
from django.urls import reverse

from apps.ai.services.dto import (
    AnswerEvaluationResult,
    ChatScope,
    ConceptDTO,
    HintResult,
    LearningPathBatchResult,
    NextAction,
    NextActionResult,
    QuestionPurpose,
)
from apps.ai.services.exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from apps.ai.services.fake import FakeLLMService
from apps.learning.models import (
    AssessmentSkill,
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
    QuizOption,
    QuizQuestion,
    UsersUser,
)
from apps.learning.services import LearningApplicationService


class Phase3ServicesTestCase(TestCase):
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
        material, analysis = self.service.process_and_create_material(
            title="Physics 12 - Waves",
            content="Wave lesson content...",
            goal_title="Understand waves",
        )

        self.assertIsNotNone(material.id)
        self.assertEqual(material.title, "Physics 12 - Waves")
        self.assertEqual(LearningGoal.objects.filter(material=material).count(), 1)
        self.assertGreater(LearningConcept.objects.count(), 0)
        self.assertGreater(AssessmentSkill.objects.count(), 0)
        self.assertGreater(len(analysis.concepts), 0)

    def test_process_and_create_material_invalid_input(self):
        with self.assertRaises(ValueError):
            self.service.process_and_create_material(title="", content="valid", goal_title="g")
        with self.assertRaises(LLMEmptyInputError):
            self.service.process_and_create_material(title="title", content="", goal_title="g")

    def test_generate_and_save_learning_path_batch_success(self):
        material = LearningMaterial.objects.create(
            title="Algebra 12",
            content="Functions and graphs",
            subject="Math",
        )
        concepts = [
            ConceptDTO(id="c1", title="Function monotonicity"),
            ConceptDTO(id="c2", title="Extrema"),
            ConceptDTO(id="c3", title="Asymptotes"),
        ]

        batch_res, steps = self.service.generate_and_save_learning_path_batch(
            material=material,
            concepts=concepts,
            student=self.student,
            batch_size=3,
        )

        self.assertEqual(len(steps), 3)
        self.assertFalse(batch_res.is_final_batch is None)
        self.assertEqual(ProgressPathStep.objects.filter(material=material).count(), 3)

        for idx, step in enumerate(steps, start=1):
            self.assertEqual(step.order_index, idx)
            lesson = step.lesson
            self.assertIsNotNone(lesson)
            cards = list(lesson.cards.order_index_list if hasattr(lesson.cards, "order_index_list") else lesson.cards.order_by("order_index"))
            self.assertGreater(len(cards), 0)
            self.assertEqual(cards[0].order_index, 1)

            checkpoints = QuizQuestion.objects.filter(lesson=lesson, question_type="checkpoint")
            self.assertGreater(checkpoints.count(), 0)
            for cp in checkpoints:
                self.assertIsNotNone(cp.after_card_order)
                self.assertGreaterEqual(cp.after_card_order, 1)

            final_exams = QuizQuestion.objects.filter(lesson=lesson, question_type="lesson_wrapup")
            self.assertGreater(final_exams.count(), 0)
            for fe in final_exams:
                self.assertIsNone(fe.after_card_order)

        prog = ProgressStudentMaterialProgress.objects.get(student=self.student, material=material)
        self.assertEqual(
            prog.status,
            ProgressStudentMaterialProgress.MaterialStatus.IN_PROGRESS,
        )

    def test_phase1_regeneration_no_duplicates(self):
        material = LearningMaterial.objects.create(
            title="Physics 12",
            content="Optics content...",
            subject="Physics",
        )
        concepts = [
            ConceptDTO(id="c1", title="Reflection"),
            ConceptDTO(id="c2", title="Refraction"),
            ConceptDTO(id="c3", title="Diffraction"),
        ]

        batch1, steps1 = self.service.generate_and_save_learning_path_batch(
            material=material, concepts=concepts, student=self.student, batch_size=3
        )
        step_count_1 = ProgressPathStep.objects.filter(material=material).count()
        card_count_1 = ProgressLessonCard.objects.count()
        question_count_1 = QuizQuestion.objects.count()

        batch2, steps2 = self.service.generate_and_save_learning_path_batch(
            material=material, concepts=concepts, student=self.student, batch_size=3
        )
        step_count_2 = ProgressPathStep.objects.filter(material=material).count()
        card_count_2 = ProgressLessonCard.objects.count()
        question_count_2 = QuizQuestion.objects.count()

        self.assertEqual(step_count_1, step_count_2)
        self.assertEqual(card_count_1, card_count_2)
        self.assertEqual(question_count_1, question_count_2)

    def test_submit_checkpoint_answer_updates_progress(self):
        material = LearningMaterial.objects.create(
            title="Chemistry 12",
            content="Esters and lipids",
            subject="Chemistry",
        )
        goal = LearningGoal.objects.create(material=material, title="Chemistry 12")
        concept = LearningConcept.objects.create(
            goal=goal,
            external_id="c1",
            title="Esters",
            order_index=1,
        )
        step = ProgressPathStep.objects.create(
            material=material,
            concept=concept,
            order_index=1,
            title="Esters",
        )
        lesson = ProgressLesson.objects.create(
            step=step,
            concept=concept,
            explanation="Lesson explanation",
            example="Lesson example",
        )
        q = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="checkpoint",
            after_card_order=0,
            question_text="What smell do esters have?",
            explanation="Fruity smell",
        )
        opt_correct = QuizOption.objects.create(
            question=q, option_text="Fruity smell", is_correct=True
        )
        QuizOption.objects.create(question=q, option_text="Pungent", is_correct=False)

        attempt, next_action_res = self.service.submit_checkpoint_answer(
            student=self.student,
            question_id=q.id,
            selected_option_id=opt_correct.id,
        )

        self.assertTrue(attempt.is_correct)
        self.assertEqual(attempt.selected_option, opt_correct)

        step_status = ProgressStudentStepStatus.objects.get(student=self.student, step=step)
        self.assertEqual(step_status.status, ProgressStudentStepStatus.StepStatus.COMPLETED)

        mat_prog = ProgressStudentMaterialProgress.objects.get(student=self.student, material=material)
        self.assertEqual(mat_prog.completion_percent, Decimal("100.00"))
        self.assertTrue(next_action_res.action in {NextAction.MOVE_NEXT, NextAction.PRACTICE_MORE, NextAction.EXPLAIN_AGAIN, NextAction.SHOW_EXAMPLE})

    def test_submit_checkpoint_answer_invalid_option(self):
        material = LearningMaterial.objects.create(title="T1", content="C1", subject="S1")
        goal = LearningGoal.objects.create(material=material, title="T1")
        concept = LearningConcept.objects.create(goal=goal, external_id="c1", title="S1", order_index=1)
        step = ProgressPathStep.objects.create(material=material, concept=concept, order_index=1, title="S1")
        lesson = ProgressLesson.objects.create(step=step, concept=concept, explanation="E", example="X")
        q = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="checkpoint",
            after_card_order=0,
            question_text="Q?",
            explanation="E",
        )
        QuizOption.objects.create(question=q, option_text="Opt", is_correct=True)

        with self.assertRaises(ValueError):
            self.service.submit_checkpoint_answer(
                student=self.student,
                question_id=q.id,
                selected_option_id=9999,
            )

    def test_needs_next_batch_triggers_path_generation(self):
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

        material = LearningMaterial.objects.create(title="Mat", content="Cont", subject="Sub")
        goal = LearningGoal.objects.create(material=material, title="Mat")
        concept1 = LearningConcept.objects.create(goal=goal, external_id="c1", title="S1", order_index=1)
        concept2 = LearningConcept.objects.create(goal=goal, external_id="c2", title="S2", order_index=2)
        step1 = ProgressPathStep.objects.create(material=material, concept=concept1, order_index=1, title="S1")
        ProgressPathStep.objects.create(material=material, concept=concept2, order_index=2, title="S2")
        lesson1 = ProgressLesson.objects.create(step=step1, concept=concept1, explanation="E", example="X")
        q = QuizQuestion.objects.create(
            lesson=lesson1,
            question_type="checkpoint",
            after_card_order=0,
            question_text="Q",
            explanation="E",
        )
        opt = QuizOption.objects.create(question=q, option_text="A", is_correct=True)

        attempt, next_action_res = service.submit_checkpoint_answer(
            student=self.student, question_id=q.id, selected_option_id=opt.id
        )

        self.assertTrue(attempt.is_correct)
        self.assertTrue(next_action_res.needs_next_batch)
        self.assertTrue(mock_llm.generate_learning_path.called)
        self.assertEqual(ProgressPathStep.objects.filter(material=material).count(), 2)
        self.assertTrue(ProgressLesson.objects.filter(step=ProgressPathStep.objects.get(material=material, concept=concept2)).exists())

    def test_get_question_hint_guardrail_enforcement(self):
        material = LearningMaterial.objects.create(title="Mat", content="Cont", subject="Sub")
        goal = LearningGoal.objects.create(material=material, title="Mat")
        concept = LearningConcept.objects.create(goal=goal, external_id="c1", title="S1", order_index=1)
        step = ProgressPathStep.objects.create(material=material, concept=concept, order_index=1, title="S1")
        lesson = ProgressLesson.objects.create(step=step, concept=concept, explanation="E", example="X")
        q = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="checkpoint",
            after_card_order=0,
            question_text="What is speed?",
            explanation="E",
        )
        QuizOption.objects.create(question=q, option_text="v = lambda * f", is_correct=True)

        hint_res = self.service.get_question_hint(question_id=q.id, level=1)
        self.assertIsNotNone(hint_res.text)

        leaking_llm = MagicMock()
        leaking_llm.generate_hint.return_value = HintResult(level=1, text="Answer is v = lambda * f")
        service_leaking = LearningApplicationService(llm_service=leaking_llm)

        with self.assertRaises(LLMInvalidResponseError):
            service_leaking.get_question_hint(question_id=q.id, level=1)

    def test_send_chat_message(self):
        thread = ChatThread.objects.create(
            student=self.student,
            scope_type=ChatThread.ScopeType.MATERIAL,
            scope_id=1,
        )

        ai_msg = self.service.send_chat_message(
            student=self.student,
            thread_id=thread.id,
            user_message="Explain the concept",
            scope=ChatScope.MATERIAL,
        )

        self.assertEqual(ai_msg.role, ChatMessage.Role.AI)
        self.assertEqual(ChatMessage.objects.filter(thread=thread).count(), 2)

    def test_llm_service_error_handling(self):
        failing_llm = MagicMock()
        failing_llm.analyze_material.side_effect = LLMServiceError("OpenRouter timeout")
        service_failing = LearningApplicationService(llm_service=failing_llm)

        with self.assertRaises(LLMServiceError):
            service_failing.process_and_create_material(title="T", content="C", goal_title="G")


class Phase3ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = UsersUser.objects.create(
            username="viewstudent",
            email="view@example.com",
            password_hash="pw",
            display_name="View Student",
        )
        session = self.client.session
        session["user_id"] = self.student.id
        session.save()

    def test_onboarding_view(self):
        response = self.client.post(
            reverse("learning:onboarding"),
            data={"user_message": "I want to study math"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_create_material_view(self):
        response = self.client.post(
            reverse("learning:create_material"),
            data={
                "title": "Biology 12",
                "content": "Genetics content...",
                "goal_title": "Understand genetics",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("material_id", data)

    def test_get_hint_view(self):
        material = LearningMaterial.objects.create(title="M", content="C", subject="S")
        goal = LearningGoal.objects.create(material=material, title="M")
        concept = LearningConcept.objects.create(goal=goal, external_id="c1", title="S", order_index=1)
        step = ProgressPathStep.objects.create(material=material, concept=concept, order_index=1, title="S")
        lesson = ProgressLesson.objects.create(step=step, concept=concept, explanation="E", example="X")
        q = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="checkpoint",
            after_card_order=0,
            question_text="Q?",
            explanation="E",
        )
        QuizOption.objects.create(question=q, option_text="Lựa chọn 1", is_correct=True)

        url = reverse("learning:get_hint", kwargs={"question_id": q.id, "level": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("hint", data)

    def test_get_step_quiz_view(self):
        material = LearningMaterial.objects.create(title="Math Material", content="Calculus", subject="Math")
        goal = LearningGoal.objects.create(material=material, title="Math Goal")
        concept = LearningConcept.objects.create(goal=goal, external_id="c1", title="Limits", order_index=1)
        step = ProgressPathStep.objects.create(material=material, concept=concept, order_index=1, title="Limits Step")
        lesson = ProgressLesson.objects.create(step=step, concept=concept, explanation="Exp", example="Ex")
        card1 = ProgressLessonCard.objects.create(lesson=lesson, order_index=1, heading="Card 1", body="Body 1")
        card2 = ProgressLessonCard.objects.create(lesson=lesson, order_index=2, heading="Card 2", body="Body 2")

        q_cp = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="checkpoint",
            after_card_order=1,
            question_text="Checkpoint Q?",
            explanation="Explanation CP",
        )
        opt_cp = QuizOption.objects.create(question=q_cp, option_text="Option CP 1", is_correct=True)

        q_wrap = QuizQuestion.objects.create(
            lesson=lesson,
            question_type="lesson_wrapup",
            after_card_order=None,
            question_text="Final Exam Q?",
            explanation="Explanation Final",
        )
        opt_wrap = QuizOption.objects.create(question=q_wrap, option_text="Option Final 1", is_correct=True)

        url = reverse("learning:get_step_quiz", kwargs={"step_id": step.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["step_id"], step.id)
        self.assertEqual(data["lesson"]["id"], lesson.id)
        self.assertEqual(len(data["lesson"]["cards"]), 2)
        self.assertEqual(len(data["checkpoints"]), 1)
        self.assertEqual(data["checkpoints"][0]["after_card_order"], 1)
        self.assertEqual(len(data["final_exam"]), 1)
        self.assertIsNone(data["final_exam"][0]["after_card_order"])

