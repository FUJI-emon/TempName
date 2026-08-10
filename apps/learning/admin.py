from django.contrib import admin
from .models import LearningMaterial, LearningGoal


class LearningGoalInline(admin.TabularInline):
    model = LearningGoal
    extra = 1


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal_count', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    inlines = [LearningGoalInline]

    def goal_count(self, obj):
        return obj.goals.count()
    goal_count.short_description = "学習目標数"


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'material', 'created_at')
    list_filter = ('material',)
    search_fields = ('title', 'description')
