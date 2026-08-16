from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from apps.learning.models import LearningMaterial, LearningGoal, UsersUser, ProgressStudentMaterialProgress


class LearningModelTestCase(TestCase):
    def setUp(self):
        self.user = UsersUser.objects.create(
            username="testuser",
            email="test@example.com",
            password_hash=make_password("password123"),
            display_name="Test User"
        )
        self.material = LearningMaterial.objects.create(
            user=self.user,
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
        response = client.get(reverse("learning:index"))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_access_returns_401(self):
        client = Client()
        response = client.get(reverse("learning:list_courses"))
        self.assertEqual(response.status_code, 401)

    def test_user_data_isolation(self):
        user_a = UsersUser.objects.create(
            username="user_a",
            email="usera@example.com",
            password_hash=make_password("pass_a")
        )
        user_b = UsersUser.objects.create(
            username="user_b",
            email="userb@example.com",
            password_hash=make_password("pass_b")
        )

        mat_a = LearningMaterial.objects.create(
            user=user_a,
            title="Course A",
            content="Content A"
        )
        ProgressStudentMaterialProgress.objects.create(student=user_a, material=mat_a)

        client_a = Client()
        session_a = client_a.session
        session_a["user_id"] = user_a.id
        session_a.save()

        res_a = client_a.get(reverse("learning:list_courses"))
        self.assertEqual(res_a.status_code, 200)
        courses_a = res_a.json().get("courses", [])
        self.assertEqual(len(courses_a), 1)
        self.assertEqual(courses_a[0]["title"], "Course A")

        client_b = Client()
        session_b = client_b.session
        session_b["user_id"] = user_b.id
        session_b.save()

        res_b = client_b.get(reverse("learning:list_courses"))
        self.assertEqual(res_b.status_code, 200)
        courses_b = res_b.json().get("courses", [])
        self.assertEqual(len(courses_b), 0)
