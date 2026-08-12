from django.db import models
from django.utils import timezone

class LearningMaterial(models.Model):
    SUBJECT_CHOICES = [
        ('math', 'Math'),
        ('english', 'English'),
    ]
    """
    Represents educational materials/assignments uploaded or input by students or teachers.
    Example: Django documentation chapter, Python basics notes, exercise requirements.
    """
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='math', verbose_name="教科")
    title = models.CharField(max_length=200, verbose_name="タイトル")
    content = models.TextField(verbose_name="学習教材本文 / 課題内容")
    progress = models.IntegerField(default=0, verbose_name="進捗率(%)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    last_used_at = models.DateTimeField(default=timezone.now, verbose_name="最終利用日時")

    class Meta:
        verbose_name = "学習教材"
        verbose_name_plural = "学習教材一覧"
        ordering = ['-created_at']

    def days_ago(self):
        """最後に使った日から何日経過したかを自動計算"""
        if not self.last_used_at:
            return 0
        delta = timezone.now() - self.last_used_at
        return max(0, delta.days)
    
    def __str__(self):
        return self.title


class LearningGoal(models.Model):
    """
    Represents a specific learning objective derived from a LearningMaterial.
    "What the teacher wants the student to be able to do."
    """
    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name="関連教材"
    )
    title = models.CharField(max_length=200, verbose_name="学習目標")
    description = models.TextField(blank=True, verbose_name="目標の詳細・達成基準")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        verbose_name = "学習目標"
        verbose_name_plural = "学習目標一覧"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.material.title} -> {self.title}"
