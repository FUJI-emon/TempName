from django.test import TestCase, Client
from django.urls import reverse
from .models import LearningMaterial, LearningGoal, UserStepProgress


class LearningModelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.material = LearningMaterial.objects.create(
            subject="math",
            title="Django基礎講座",
            content="MVTパターン、ルーティング、ORマッピングの基礎を学習します。",
            progress=0
        )
        self.goal = LearningGoal.objects.create(
            material=self.material,
            title="DjangoのMVTパターンを自分で説明できるようになる",
            description="Model, View, Templateのそれぞれの役割を理解すること。"
        )

    def test_material_creation(self):
        self.assertEqual(str(self.material), "Django基礎講座")
        self.assertEqual(self.material.goals.count(), 1)

    def test_goal_creation(self):
        self.assertIn("Django基礎講座", str(self.goal))
        self.assertEqual(self.goal.material, self.material)

    def test_homepage_view(self):
        response = self.client.get(reverse('learning:index'))
        self.assertEqual(response.status_code, 200)

    def test_complete_step_api_progress_calculation(self):
        """Item 1: Verify complete_step_api updates LearningMaterial.progress accurately"""
        url = reverse('learning:complete_step_api', kwargs={'topic_id': self.material.id, 'step_num': 1})
        response = self.client.post(url, content_type='application/json', data={'mistakes': 0, 'time_taken': 15})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), {'status': 'success', 'is_final': False, 'next_step': 2})

        self.material.refresh_from_db()
        self.assertEqual(self.material.progress, 20)

        # Complete step 2
        url_step2 = reverse('learning:complete_step_api', kwargs={'topic_id': self.material.id, 'step_num': 2})
        response_step2 = self.client.post(url_step2, content_type='application/json', data={'mistakes': 0, 'time_taken': 20})
        self.assertEqual(response_step2.status_code, 200)

        self.material.refresh_from_db()
        self.assertEqual(self.material.progress, 40)

    def test_path_map_sync_progress(self):
        """Item 1: Verify path_map_view synchronizes LearningMaterial.progress"""
        UserStepProgress.objects.create(topic_id=self.material.id, step_num=1, status=2)
        UserStepProgress.objects.create(topic_id=self.material.id, step_num=2, status=2)

        url = reverse('learning:path_map', kwargs={'topic_id': self.material.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.material.refresh_from_db()
        self.assertEqual(self.material.progress, 40)

    def test_dynamic_lesson_card_view(self):
        """Item 3: Verify dynamic lesson card generation references material title"""
        url = reverse('learning:lesson_card', kwargs={'topic_id': self.material.id, 'step_num': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django基礎講座")

    def test_dynamic_lesson_checkpoint_view(self):
        """Item 3: Verify dynamic lesson checkpoint view references material title"""
        url = reverse('learning:lesson_checkpoint', kwargs={'topic_id': self.material.id, 'step_num': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django基礎講座")

    def test_db_persistence_and_caching_for_steps(self):
        """Verify step content, cards, checkpoint questions, options, and hints are persisted and cached in DB"""
        from .models import ProgressPathStep, ProgressLessonCard, QuizCheckpointQuestion, QuizCheckpointOption, QuizHint

        # Initial state: no steps or questions exist
        self.assertEqual(ProgressPathStep.objects.filter(material=self.material).count(), 0)

        # Call lesson_card view for Step 1
        url_card = reverse('learning:lesson_card', kwargs={'topic_id': self.material.id, 'step_num': 1})
        res_card = self.client.get(url_card)
        self.assertEqual(res_card.status_code, 200)

        # Check DB records created
        step = ProgressPathStep.objects.filter(material=self.material, order_index=1).first()
        self.assertIsNotNone(step)
        cards_count = ProgressLessonCard.objects.filter(step=step).count()
        self.assertGreaterEqual(cards_count, 1)

        # Call lesson_checkpoint view for Step 1
        url_cp = reverse('learning:lesson_checkpoint', kwargs={'topic_id': self.material.id, 'step_num': 1})
        res_cp = self.client.get(url_cp)
        self.assertEqual(res_cp.status_code, 200)

        question = QuizCheckpointQuestion.objects.filter(step=step).first()
        self.assertIsNotNone(question)
        options_count = QuizCheckpointOption.objects.filter(question=question).count()
        self.assertEqual(options_count, 4)
        hint = QuizHint.objects.filter(question=question, level=1).first()
        self.assertIsNotNone(hint)

        # Second call to lesson_card and lesson_checkpoint should reuse DB records (caching)
        res_card_2 = self.client.get(url_card)
        res_cp_2 = self.client.get(url_cp)
        self.assertEqual(res_card_2.status_code, 200)
        self.assertEqual(res_cp_2.status_code, 200)

        # Count should remain unchanged
        self.assertEqual(ProgressPathStep.objects.filter(material=self.material).count(), 1)
        self.assertEqual(ProgressLessonCard.objects.filter(step=step).count(), cards_count)
        self.assertEqual(QuizCheckpointQuestion.objects.filter(step=step).count(), 1)

    def test_final_test_view_and_submission(self):
        """Verify QuizFinalTest creation, question loading, and submission evaluation in DB"""
        from .models import QuizFinalTest, QuizFinalTestQuestion, QuizTestAttempt

        url = reverse('learning:finaltest_topic', kwargs={'topic_id': self.material.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check DB records
        final_test = QuizFinalTest.objects.filter(material=self.material).first()
        self.assertIsNotNone(final_test)
        questions_count = QuizFinalTestQuestion.objects.filter(final_test=final_test).count()
        self.assertGreaterEqual(questions_count, 5)

        # Submit answers to API
        submit_url = reverse('learning:submit_final_test_api', kwargs={'topic_id': self.material.id})
        user_answers = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
        res = self.client.post(submit_url, content_type='application/json', data={'answers': user_answers})
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('score_percent', json_data)
        self.assertTrue(json_data['passed'])

        # Verify QuizTestAttempt persisted in DB
        attempt = QuizTestAttempt.objects.filter(final_test=final_test).first()
        self.assertIsNotNone(attempt)
        self.assertTrue(attempt.passed)

    def test_dashboard_analytics_calculation(self):
        """Verify dashboard analytics (XP, average progress, completed steps count) calculations"""
        UserStepProgress.objects.create(topic_id=self.material.id, step_num=1, status=2)
        UserStepProgress.objects.create(topic_id=self.material.id, step_num=2, status=2)
        self.material.progress = 40
        self.material.save()

        response = self.client.get(reverse('learning:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_steps_count'], 2)
        self.assertEqual(response.context['total_xp'], 200)
        self.assertEqual(response.context['avg_progress'], 40)

    def test_admin_models_registered(self):
        """Verify all learning models are registered in Django Admin site"""
        from django.contrib import admin
        from .models import LearningMaterial, LearningGoal, UploadedDocument, ProgressPathStep, QuizFinalTest, ChatThread

        self.assertIn(LearningMaterial, admin.site._registry)
        self.assertIn(LearningGoal, admin.site._registry)
        self.assertIn(UploadedDocument, admin.site._registry)
        self.assertIn(ProgressPathStep, admin.site._registry)
        self.assertIn(QuizFinalTest, admin.site._registry)
        self.assertIn(ChatThread, admin.site._registry)






