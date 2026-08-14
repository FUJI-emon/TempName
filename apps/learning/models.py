from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


# 🟢 Topic モデル
class Topic(models.Model):
    title = models.CharField(max_length=200, verbose_name="トピック名")
    subject = models.CharField(max_length=20, verbose_name="教科", default='math')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        verbose_name = "トピック"
        verbose_name_plural = "トピック一覧"

    def __str__(self):
        return self.title


class LearningMaterial(models.Model):
    SUBJECT_CHOICES = [
        ('math', 'Math'),
        ('english', 'English'),
    ]

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
        ordering = ['-last_used_at']

    def days_ago(self):
        """最後に使った日から何日経過したかを自動計算"""
        if not self.last_used_at:
            return 0
        delta = timezone.now() - self.last_used_at
        return max(0, delta.days)

    def __str__(self):
        return self.title


class LearningGoal(models.Model):
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
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.material.title} -> {self.title}"


class UploadedDocument(models.Model):
    learning_material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.FileField(upload_to='documents/', verbose_name="ファイル")
    name = models.CharField(max_length=255, verbose_name="ファイル名")
    size = models.BigIntegerField(default=0, verbose_name="ファイルサイズ(Byte)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="アップロード日時")

    def file_size_str(self):
        """バイト数を MB または KB 表記に変換"""
        if self.size >= 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        elif self.size >= 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size} B"

    def __str__(self):
        return self.name


class ChatThread(models.Model):
    """チャットスレッド（対話の単位）"""
    learning_material = models.ForeignKey(
        'LearningMaterial', 
        on_delete=models.CASCADE, 
        related_name='chat_threads',
        null=True, 
        blank=True
    )
    title = models.CharField("スレッドタイトル", max_length=255, default="新しいチャット")
    created_at = models.DateTimeField("作成日時", default=timezone.now)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    """スレッド内の各メッセージ"""
    SENDER_CHOICES = (
        ('user', 'ユーザー'),
        ('ai', 'AIアシスタント'),
    )

    thread = models.ForeignKey(
        ChatThread, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.CharField("送信者", max_length=10, choices=SENDER_CHOICES)
    content = models.TextField("メッセージ内容")
    created_at = models.DateTimeField("送信日時", default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.content[:20]}"


# 🌟 ChatMessage から独立した正しく配置されたクラス
class UserStepProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    topic_id = models.IntegerField()
    step_num = models.IntegerField()
    
    # ステータス: 0=ロック, 1=解放中(挑戦可能), 2=完了
    status = models.IntegerField(default=0)
    
    # AIへのインプット用ログデータ
    mistake_count = models.IntegerField(default=0)       # 間違えた回数
    time_taken_seconds = models.IntegerField(default=0)  # 解答にかかった時間(秒)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'topic_id', 'step_num')