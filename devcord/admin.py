from django.contrib import admin
from .models import Team, Project, Task, DeveloperProfile, Standup, CodeReview

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'vibe_score')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'status', 'created_at', 'due_date')
    list_filter = ('status', 'team')
    search_fields = ('name', 'description')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
    raw_id_fields = ('assigned_to',)

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'github_username', 'current_vibe', 'productivity_score')
    list_filter = ('current_vibe',)
    search_fields = ('user__username', 'github_username', 'bio')

@admin.register(Standup)
class StandupAdmin(admin.ModelAdmin):
    list_display = ('developer', 'project', 'date', 'mood')
    list_filter = ('date', 'mood', 'project')
    search_fields = ('developer__username', 'yesterday_work', 'today_plan')
    raw_id_fields = ('developer', 'project')

@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ('task', 'reviewer', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('task__title', 'code_snippet')
    raw_id_fields = ('task', 'reviewer')
