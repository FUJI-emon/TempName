from django.test import TestCase, Client
from django.urls import reverse
from .models import LearningMaterial, LearningGoal


class LearningModelTestCase(TestCase):
    def setUp(self):
        self.material = LearningMaterial.objects.create(
            title="Django基礎講座",
            content="MVTパターン、ルーティング、ORマッピングの基礎を学習します。"
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
        client = Client()
        response = client.get(reverse('learning:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WebApp Title")

