import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from apps.ai.services.dto import QuestionPurpose
from apps.learning.models import (
    AssessmentSkill,
    AssessmentSkillCheck,
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


class Phase3StudentProgressTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = UsersUser.objects.create(
            username="student_phase3",
            email="phase3@lumina.ai",
            password_hash="hash123",
            display_name="Phase3 Student",
        )
        self.material = LearningMaterial.objects.create(
            user=self.student,
            title="Đại Số & Giải Tích 12",
            content="Nội dung tổng quan Giải Tích 12",
            progress=0,
        )
        self.goal = LearningGoal.objects.create(
            material=self.material,
            title="Giải Tích 12 Goal",
        )
        self.concept1 = LearningConcept.objects.create(
            goal=self.goal,
            external_id="c1",
            title="Khái niệm Đạo Hàm",
            order_index=1,
        )
        self.concept2 = LearningConcept.objects.create(
            goal=self.goal,
            external_id="c2",
            title="Cực Trị Hàm Số",
            order_index=2,
        )

        self.skill1 = AssessmentSkill.objects.create(
            concept=self.concept1,
            name="Tính đạo hàm cơ bản",
        )

        # Step 1
        self.step1 = ProgressPathStep.objects.create(
            material=self.material,
            concept=self.concept1,
            order_index=1,
            title="Khái niệm Đạo Hàm",
            status="generated",
        )
        self.lesson1 = ProgressLesson.objects.create(
            step=self.step1,
            concept=self.concept1,
            explanation="Đạo hàm thể hiện tốc độ thay đổi",
            example="y = x^2 => y' = 2x",
        )
        self.card1_1 = ProgressLessonCard.objects.create(
            lesson=self.lesson1, order_index=1, heading="Card 1", body="Body 1"
        )
        self.card1_2 = ProgressLessonCard.objects.create(
            lesson=self.lesson1, order_index=2, heading="Card 2", body="Body 2"
        )

        # Checkpoint question for Step 1
        self.checkpoint_q = QuizQuestion.objects.create(
            lesson=self.lesson1,
            question_type=QuestionPurpose.CHECKPOINT.value,
            after_card_order=1,
            question_text="Đạo hàm của y = x^2 là gì?",
            explanation="Áp dụng công thức (x^n)' = n*x^(n-1)",
        )
        self.opt_cp_correct = QuizOption.objects.create(
            question=self.checkpoint_q, option_text="2x", is_correct=True
        )
        self.opt_cp_wrong = QuizOption.objects.create(
            question=self.checkpoint_q, option_text="x^2", is_correct=False
        )

        # Final Exam question for Step 1
        self.wrapup_q = QuizQuestion.objects.create(
            lesson=self.lesson1,
            question_type=QuestionPurpose.LESSON_WRAPUP.value,
            after_card_order=None,
            question_text="Tổng kết: Ý nghĩa hình học của đạo hàm?",
            explanation="Đạo hàm là hệ số góc của tiếp tuyến.",
        )
        self.opt_wu_correct = QuizOption.objects.create(
            question=self.wrapup_q, option_text="Hệ số góc tiếp tuyến", is_correct=True
        )
        self.opt_wu_wrong = QuizOption.objects.create(
            question=self.wrapup_q, option_text="Diện tích hình phẳng", is_correct=False
        )

        # Step 2
        self.step2 = ProgressPathStep.objects.create(
            material=self.material,
            concept=self.concept2,
            order_index=2,
            title="Cực Trị Hàm Số",
            status="generated",
        )
        self.lesson2 = ProgressLesson.objects.create(
            step=self.step2,
            concept=self.concept2,
            explanation="Khái niệm cực đại cực tiểu",
            example="f'(x) đổi dấu",
        )

        # Initial DB statuses
        ProgressStudentStepStatus.objects.create(
            student=self.student, step=self.step1, status=ProgressStudentStepStatus.StepStatus.UNLOCKED
        )
        ProgressStudentStepStatus.objects.create(
            student=self.student, step=self.step2, status=ProgressStudentStepStatus.StepStatus.LOCKED
        )

    def test_1_submit_correct_answer(self):
        """Test 1: Submit correct answer saves QuizAttempt and returns is_correct=True."""
        url = reverse("learning:submit_question_answer", kwargs={"question_id": self.checkpoint_q.id})
        payload = {"student_id": self.student.id, "option_id": self.opt_cp_correct.id}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_correct"])
        self.assertEqual(data["question_type"], "checkpoint")

        attempts = QuizAttempt.objects.filter(student=self.student, question=self.checkpoint_q)
        self.assertEqual(attempts.count(), 1)
        self.assertTrue(attempts.first().is_correct)

    def test_2_submit_incorrect_answer(self):
        """Test 2: Submit incorrect answer returns is_correct=False and explanation."""
        url = reverse("learning:submit_question_answer", kwargs={"question_id": self.checkpoint_q.id})
        payload = {"student_id": self.student.id, "option_id": self.opt_cp_wrong.id}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertFalse(data["is_correct"])
        self.assertIn("x^n", data["explanation"])

    def test_3_checkpoint_updates_mastery_does_not_complete_step(self):
        """Test 3: Checkpoint answer updates AssessmentSkillCheck but does NOT mark step COMPLETED."""
        service = LearningApplicationService()
        result = service.submit_question_answer(
            student=self.student,
            question_id=self.checkpoint_q.id,
            selected_option_id=self.opt_cp_correct.id,
        )

        self.assertTrue(result["is_correct"])
        self.assertFalse(result["step_completed"])

        # AssessmentSkillCheck updated
        skill_check = AssessmentSkillCheck.objects.filter(student=self.student, skill=self.skill1).first()
        self.assertIsNotNone(skill_check)
        self.assertTrue(skill_check.is_known)

        # Step 1 status remains UNLOCKED (not COMPLETED)
        st = ProgressStudentStepStatus.objects.get(student=self.student, step=self.step1)
        self.assertEqual(st.status, ProgressStudentStepStatus.StepStatus.UNLOCKED)

    def test_4_final_exam_completes_step_and_unlocks_next_step(self):
        """Test 4 & 5: Final Exam submission completes Step 1 and safely unlocks Step 2."""
        service = LearningApplicationService()
        result = service.submit_question_answer(
            student=self.student,
            question_id=self.wrapup_q.id,
            selected_option_id=self.opt_wu_correct.id,
        )

        self.assertTrue(result["step_completed"])
        self.assertTrue(result["next_step_unlocked"])

        # Check DB states
        st1 = ProgressStudentStepStatus.objects.get(student=self.student, step=self.step1)
        self.assertEqual(st1.status, ProgressStudentStepStatus.StepStatus.COMPLETED)

        st2 = ProgressStudentStepStatus.objects.get(student=self.student, step=self.step2)
        self.assertEqual(st2.status, ProgressStudentStepStatus.StepStatus.UNLOCKED)

        # Material progress updated
        mat_prog = ProgressStudentMaterialProgress.objects.get(student=self.student, material=self.material)
        self.assertEqual(mat_prog.completion_percent, Decimal("50.00"))

    def test_6_get_student_learning_progress_api(self):
        """Test 6: Progress API returns correct step statuses from DB."""
        url = reverse("learning:get_student_learning_progress", kwargs={"student_id": self.student.id})
        response = self.client.get(f"{url}?material_id={self.material.id}")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["steps"]), 2)
        self.assertEqual(data["steps"][0]["status"], "unlocked")
        self.assertEqual(data["steps"][1]["status"], "locked")

    def test_7_idempotency_and_retry_protection(self):
        """Test 7: Retrying questions creates multiple attempts without corrupting COMPLETED status or progress."""
        service = LearningApplicationService()
        # Complete Step 1
        service.submit_question_answer(self.student, self.wrapup_q.id, self.opt_wu_correct.id)
        st1 = ProgressStudentStepStatus.objects.get(student=self.student, step=self.step1)
        self.assertEqual(st1.status, ProgressStudentStepStatus.StepStatus.COMPLETED)

        # Retry checkpoint with wrong answer after completion
        service.submit_question_answer(self.student, self.checkpoint_q.id, self.opt_cp_wrong.id)

        # Step 1 MUST stay COMPLETED
        st1_after = ProgressStudentStepStatus.objects.get(student=self.student, step=self.step1)
        self.assertEqual(st1_after.status, ProgressStudentStepStatus.StepStatus.COMPLETED)

        # Material progress MUST stay 50.00%
        mat_prog = ProgressStudentMaterialProgress.objects.get(student=self.student, material=self.material)
        self.assertEqual(mat_prog.completion_percent, Decimal("50.00"))

        # 2 attempts recorded
        self.assertEqual(QuizAttempt.objects.filter(student=self.student).count(), 2)

    def test_8_dynamic_question_counts(self):
        """Test 8: Step with 0 wrapup questions completes when all questions attempted."""
        concept3 = LearningConcept.objects.create(
            goal=self.goal, external_id="c3", title="Concept 3", order_index=3
        )
        # Create Step 3 with 1 checkpoint and 0 wrapup questions
        step3 = ProgressPathStep.objects.create(
            material=self.material, concept=concept3, order_index=3, title="Step 3", status="generated"
        )
        lesson3 = ProgressLesson.objects.create(
            step=step3, concept=concept3, explanation="Explanation 3", example="Example 3"
        )
        q3 = QuizQuestion.objects.create(
            lesson=lesson3,
            question_type=QuestionPurpose.CHECKPOINT.value,
            after_card_order=1,
            question_text="Q3 text",
            explanation="Q3 exp",
        )
        opt3 = QuizOption.objects.create(question=q3, option_text="Opt3", is_correct=True)

        service = LearningApplicationService()
        res = service.submit_question_answer(self.student, q3.id, opt3.id)
        self.assertTrue(res["step_completed"])
