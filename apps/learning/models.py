from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class UsersUser(models.Model):
    username = models.CharField(max_length=150, unique=True, null=False)
    email = models.CharField(max_length=254, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    display_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_user"


class LearningMaterial(models.Model):
    user = models.ForeignKey(
        UsersUser, on_delete=models.CASCADE, related_name="materials", null=True, blank=True
    )
    title = models.CharField(max_length=200, null=False)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(default=timezone.now)
    progress = models.IntegerField(default=0)
    subject = models.CharField(max_length=20, default="")

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


class LearningConcept(models.Model):
    goal = models.ForeignKey(
        LearningGoal, on_delete=models.CASCADE, related_name="concepts", null=False
    )
    external_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, null=False)
    description = models.TextField(blank=True, null=True)
    order_index = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "learning_concept"
        constraints = [
            models.UniqueConstraint(
                fields=["goal", "external_id"],
                name="learning_concept_goal_id_external_id_key",
            )
        ]


class AssessmentSkill(models.Model):
    concept = models.ForeignKey(
        LearningConcept, on_delete=models.CASCADE, related_name="skills", null=False
    )
    name = models.CharField(max_length=200, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_skill"


class AssessmentSkillCheck(models.Model):
    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    skill = models.ForeignKey(AssessmentSkill, on_delete=models.CASCADE, null=False)
    is_known = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessment_skill_check"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "skill"],
                name="assessment_skill_check_student_id_skill_id_key",
            )
        ]


class ProgressPathStep(models.Model):
    material = models.ForeignKey(LearningMaterial, on_delete=models.CASCADE, null=False)
    concept = models.ForeignKey(LearningConcept, on_delete=models.CASCADE, null=False)
    order_index = models.IntegerField(null=False)
    title = models.CharField(max_length=200, null=False)
    status = models.CharField(max_length=20, default="generated")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_path_step"
        constraints = [
            models.UniqueConstraint(
                fields=["material", "concept"],
                name="progress_path_step_material_id_concept_id_key",
            ),
            models.UniqueConstraint(
                fields=["material", "order_index"],
                name="progress_path_step_material_id_order_index_key",
            )
        ]


class ProgressLesson(models.Model):
    step = models.OneToOneField(
        ProgressPathStep, on_delete=models.CASCADE, related_name="lesson", null=False
    )
    concept = models.ForeignKey(LearningConcept, on_delete=models.CASCADE, null=False)
    explanation = models.TextField(null=False)
    example = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_lesson"


class ProgressLessonCard(models.Model):
    lesson = models.ForeignKey(
        ProgressLesson, on_delete=models.CASCADE, related_name="cards", null=False
    )
    order_index = models.IntegerField(null=False)
    heading = models.CharField(max_length=200, null=False)
    body = models.TextField(null=False)

    class Meta:
        db_table = "progress_lesson_card"
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "order_index"],
                name="progress_lesson_card_lesson_id_order_index_key",
            )
        ]


class ProgressStudentStepStatus(models.Model):
    class StepStatus(models.TextChoices):
        LOCKED = "locked", "Locked"
        UNLOCKED = "unlocked", "Unlocked"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    step = models.ForeignKey(ProgressPathStep, on_delete=models.CASCADE, null=False)
    status = models.CharField(
        max_length=20,
        choices=StepStatus.choices,
        default=StepStatus.LOCKED,
        null=False,
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progress_student_step_status"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "step"],
                name="progress_student_step_status_student_id_step_id_key",
            )
        ]


class ProgressStudentMaterialProgress(models.Model):
    class MaterialStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    material = models.ForeignKey(LearningMaterial, on_delete=models.CASCADE, null=False)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progress_student_material_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "material"],
                name="progress_student_material_progress_student_id_material_id_key",
            )
        ]


class QuizQuestion(models.Model):
    lesson = models.ForeignKey(
        ProgressLesson, on_delete=models.CASCADE, related_name="questions", null=False
    )
    question_type = models.CharField(max_length=30, null=False)
    after_card_order = models.IntegerField(blank=True, null=True)
    question_text = models.TextField(null=False)
    explanation = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_question"


class QuizOption(models.Model):
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, related_name="options", null=False
    )
    option_text = models.CharField(max_length=500, null=False)
    is_correct = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = "quiz_option"


class QuizHint(models.Model):
    class HintLevel(models.IntegerChoices):
        LEVEL_1 = 1, "Level 1"
        LEVEL_2 = 2, "Level 2"
        LEVEL_3 = 3, "Level 3"

    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, null=False
    )
    level = models.IntegerField(choices=HintLevel.choices, null=False)
    hint_text = models.TextField(null=False)

    class Meta:
        db_table = "quiz_hint"
        constraints = [
            models.UniqueConstraint(
                fields=["question", "level"], name="quiz_hint_question_id_level_key"
            )
        ]


class QuizAttempt(models.Model):
    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, related_name="attempts", null=False
    )
    selected_option = models.ForeignKey(
        QuizOption, on_delete=models.SET_NULL, blank=True, null=True
    )
    is_correct = models.BooleanField(null=False)
    hints_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_attempt"


class ChatThread(models.Model):
    class ScopeType(models.TextChoices):
        MATERIAL = "material", "Material"
        GOAL = "goal", "Goal"
        CHECKPOINT_QUESTION = "checkpoint_question", "Checkpoint Question"

    student = models.ForeignKey(UsersUser, on_delete=models.CASCADE, null=False)
    scope_type = models.CharField(max_length=30, choices=ScopeType.choices, null=False)
    scope_id = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_thread"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "scope_type", "scope_id"],
                name="chat_thread_student_scope_unique",
            )
        ]


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


QuizCheckpointQuestion = QuizQuestion
QuizCheckpointOption = QuizOption
QuizCheckpointAttempt = QuizAttempt
