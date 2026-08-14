from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# =====================================================================
# 1. USERS
# =====================================================================


class UsersUser(models.Model):
    username = models.CharField(max_length=150, unique=True, null=False)
    email = models.CharField(max_length=254, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    display_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_user"


# =====================================================================
# 2. LEARNING
# =====================================================================


class LearningMaterial(models.Model):
    title = models.CharField(max_length=200, null=False)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "learning_material"


class LearningGoal(models.Model):
    material = models.ForeignKey(
        LearningMaterial, on_delete=models.CASCADE, related_name="goals", null=False
    )
    title = models.CharField(max_length=200, null=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.material.title})"

    class Meta:
        db_table = "learning_goal"



# =====================================================================
# 3. ASSESSMENT — Self-Check
# =====================================================================


class AssessmentSkill(models.Model):
    goal = models.ForeignKey(LearningGoal, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=200, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_skill"


class AssessmentSkillCheck(models.Model):
    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    skill = models.ForeignKey(
        AssessmentSkill, on_delete=models.CASCADE, null=False
    )
    is_known = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_skill_check"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "skill"], name="unique_student_skill"
            )
        ]


# =====================================================================
# 4. PROGRESS — Path Map & Progress Tracking
# =====================================================================


class ProgressPathStep(models.Model):
    material = models.ForeignKey(
        LearningMaterial, on_delete=models.CASCADE, null=False
    )
    order_index = models.IntegerField(null=False)
    title = models.CharField(max_length=200, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_path_step"
        constraints = [
            models.UniqueConstraint(
                fields=["material", "order_index"], name="unique_material_order"
            )
        ]


class ProgressLessonCard(models.Model):
    step = models.ForeignKey(
        ProgressPathStep, on_delete=models.CASCADE, null=False
    )
    order_index = models.IntegerField(null=False)
    heading = models.CharField(max_length=200, null=False)
    body = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_lesson_card"
        constraints = [
            models.UniqueConstraint(
                fields=["step", "order_index"], name="unique_step_order"
            )
        ]


class ProgressStudentStepStatus(models.Model):
    class StepStatus(models.TextChoices):
        LOCKED = "locked", "Locked"
        UNLOCKED = "unlocked", "Unlocked"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    step = models.ForeignKey(
        ProgressPathStep, on_delete=models.CASCADE, null=False
    )
    status = models.CharField(
        max_length=20,
        choices=StepStatus.choices,
        default=StepStatus.LOCKED,
        null=False,
    )
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "progress_student_step_status"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "step"], name="unique_student_step"
            )
        ]


class ProgressStudentMaterialProgress(models.Model):
    class MaterialStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    material = models.ForeignKey(
        LearningMaterial, on_delete=models.CASCADE, null=False
    )
    completion_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, null=False
    )
    status = models.CharField(
        max_length=20,
        choices=MaterialStatus.choices,
        default=MaterialStatus.NOT_STARTED,
        null=False,
    )
    last_active_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "progress_student_material_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "material"], name="unique_student_material"
            )
        ]


# =====================================================================
# 5. QUIZ — Checkpoints & Final Test
# =====================================================================


class QuizCheckpointQuestion(models.Model):
    step = models.ForeignKey(
        ProgressPathStep, on_delete=models.CASCADE, null=False
    )
    after_card_order = models.IntegerField(null=False)
    question_text = models.TextField(null=False)
    explanation = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_checkpoint_question"


class QuizCheckpointOption(models.Model):
    question = models.ForeignKey(
        QuizCheckpointQuestion, on_delete=models.CASCADE, null=False
    )
    option_text = models.CharField(max_length=500, null=False)
    is_correct = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = "quiz_checkpoint_option"


class QuizHint(models.Model):
    class HintLevel(models.IntegerChoices):
        LEVEL_1 = 1, "Level 1"
        LEVEL_2 = 2, "Level 2"
        LEVEL_3 = 3, "Level 3"

    question = models.ForeignKey(
        QuizCheckpointQuestion, on_delete=models.CASCADE, null=False
    )
    level = models.IntegerField(choices=HintLevel.choices, null=False)
    hint_text = models.TextField(null=False)

    class Meta:
        db_table = "quiz_hint"
        constraints = [
            models.UniqueConstraint(
                fields=["question", "level"], name="unique_question_hint_level"
            )
        ]


class QuizCheckpointAttempt(models.Model):
    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    question = models.ForeignKey(
        QuizCheckpointQuestion, on_delete=models.CASCADE, null=False
    )
    selected_option = models.ForeignKey(
        QuizCheckpointOption, on_delete=models.SET_NULL, blank=True, null=True
    )
    is_correct = models.BooleanField(null=False)
    hints_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_checkpoint_attempt"


class QuizFinalTest(models.Model):
    material = models.OneToOneField(
        LearningMaterial, on_delete=models.CASCADE, null=False
    )
    pass_threshold = models.DecimalField(
        max_digits=5, decimal_places=2, default=80.00, null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_final_test"


class QuizFinalTestQuestion(models.Model):
    final_test = models.ForeignKey(
        QuizFinalTest, on_delete=models.CASCADE, null=False
    )
    order_index = models.IntegerField(null=False)
    question_text = models.TextField(null=False)
    explanation = models.TextField(null=False)

    class Meta:
        db_table = "quiz_final_test_question"
        constraints = [
            models.UniqueConstraint(
                fields=["final_test", "order_index"],
                name="unique_final_test_order",
            )
        ]


class QuizFinalTestOption(models.Model):
    question = models.ForeignKey(
        QuizFinalTestQuestion, on_delete=models.CASCADE, null=False
    )
    option_text = models.CharField(max_length=500, null=False)
    is_correct = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = "quiz_final_test_option"


class QuizTestAttempt(models.Model):
    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    final_test = models.ForeignKey(
        QuizFinalTest, on_delete=models.CASCADE, null=False
    )
    score_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=False
    )
    passed = models.BooleanField(null=False)
    attempt_number = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_test_attempt"


# =====================================================================
# 6. CHAT — AI Assistant
# =====================================================================


class ChatThread(models.Model):
    class ScopeType(models.TextChoices):
        MATERIAL = "material", "Material"
        CHECKPOINT_QUESTION = "checkpoint_question", "Checkpoint Question"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    scope_type = models.CharField(
        max_length=30, choices=ScopeType.choices, null=False
    )
    scope_id = models.IntegerField(null=False)  # Application-level FK
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_thread"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        AI = "ai", "AI"

    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, null=False)
    role = models.CharField(max_length=10, choices=Role.choices, null=False)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message"