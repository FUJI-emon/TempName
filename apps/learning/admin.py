from django.contrib import admin
from .models import (
    Topic,
    UserStepProgress,
    UsersUser,
    LearningMaterial,
    LearningGoal,
    UploadedDocument,
    AssessmentSkill,
    AssessmentSkillCheck,
    ProgressPathStep,
    ProgressLessonCard,
    ProgressStudentStepStatus,
    ProgressStudentMaterialProgress,
    QuizCheckpointQuestion,
    QuizCheckpointOption,
    QuizHint,
    QuizCheckpointAttempt,
    QuizFinalTest,
    QuizFinalTestQuestion,
    QuizFinalTestOption,
    QuizTestAttempt,
    ChatThread,
    ChatMessage,
)


class LearningGoalInline(admin.TabularInline):
    model = LearningGoal
    extra = 1


class UploadedDocumentInline(admin.TabularInline):
    model = UploadedDocument
    extra = 1


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "progress", "goal_count", "document_count", "created_at", "last_used_at")
    list_filter = ("subject", "created_at")
    search_fields = ("title", "content")
    inlines = [LearningGoalInline, UploadedDocumentInline]

    def goal_count(self, obj):
        return obj.goals.count()
    goal_count.short_description = "学習目標数"

    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = "資料数"


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "material", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description")


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "learning_material", "size", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("name",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "created_at")
    list_filter = ("subject", "created_at")
    search_fields = ("title",)


@admin.register(UserStepProgress)
class UserStepProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "topic_id", "step_num", "status", "mistake_count", "time_taken_seconds", "updated_at")
    list_filter = ("status", "step_num", "updated_at")
    search_fields = ("topic_id",)


@admin.register(UsersUser)
class UsersUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "display_name", "created_at")
    search_fields = ("username", "email", "display_name")


class ProgressLessonCardInline(admin.StackedInline):
    model = ProgressLessonCard
    extra = 1


@admin.register(ProgressPathStep)
class ProgressPathStepAdmin(admin.ModelAdmin):
    list_display = ("title", "material", "order_index", "created_at")
    list_filter = ("order_index", "created_at")
    search_fields = ("title",)
    inlines = [ProgressLessonCardInline]


@admin.register(ProgressLessonCard)
class ProgressLessonCardAdmin(admin.ModelAdmin):
    list_display = ("heading", "step", "order_index", "created_at")
    search_fields = ("heading", "body")


class QuizCheckpointOptionInline(admin.TabularInline):
    model = QuizCheckpointOption
    extra = 2


class QuizHintInline(admin.TabularInline):
    model = QuizHint
    extra = 1


@admin.register(QuizCheckpointQuestion)
class QuizCheckpointQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "step", "after_card_order", "created_at")
    search_fields = ("question_text", "explanation")
    inlines = [QuizCheckpointOptionInline, QuizHintInline]


@admin.register(QuizCheckpointOption)
class QuizCheckpointOptionAdmin(admin.ModelAdmin):
    list_display = ("option_text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("option_text",)


@admin.register(QuizHint)
class QuizHintAdmin(admin.ModelAdmin):
    list_display = ("question", "level", "hint_text")
    list_filter = ("level",)


@admin.register(QuizCheckpointAttempt)
class QuizCheckpointAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "hints_used", "created_at")
    list_filter = ("is_correct", "hints_used", "created_at")


class QuizFinalTestQuestionInline(admin.StackedInline):
    model = QuizFinalTestQuestion
    extra = 1


@admin.register(QuizFinalTest)
class QuizFinalTestAdmin(admin.ModelAdmin):
    list_display = ("material", "pass_threshold", "created_at")
    inlines = [QuizFinalTestQuestionInline]


class QuizFinalTestOptionInline(admin.TabularInline):
    model = QuizFinalTestOption
    extra = 2


@admin.register(QuizFinalTestQuestion)
class QuizFinalTestQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "final_test", "order_index")
    search_fields = ("question_text", "explanation")
    inlines = [QuizFinalTestOptionInline]


@admin.register(QuizFinalTestOption)
class QuizFinalTestOptionAdmin(admin.ModelAdmin):
    list_display = ("option_text", "question", "is_correct")
    list_filter = ("is_correct",)


@admin.register(QuizTestAttempt)
class QuizTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "final_test", "score_percent", "passed", "attempt_number", "created_at")
    list_filter = ("passed", "created_at")


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 1


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "scope_type", "created_at", "updated_at")
    list_filter = ("scope_type", "created_at")
    search_fields = ("title",)
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "role", "sender", "content_preview", "created_at")
    list_filter = ("role", "sender", "created_at")

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = "内容プレビュー"

