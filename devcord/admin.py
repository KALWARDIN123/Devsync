from django.contrib import admin
from .models import (
    Team, TeamMember, Project, Task, DeveloperProfile,
    Standup, CodeReview, ActivityLog, AIInsight,
    TaskBoard, TaskColumn, AIInsightTracker, CodeReviewInbox
)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_type', 'creator', 'created_at']
    list_filter = ['team_type', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status', 'joined_at']
    search_fields = ['user__username', 'user__email', 'team__name']
    date_hierarchy = 'joined_at'
    readonly_fields = ['joined_at', 'last_active']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'project_type', 'status', 'created_at']
    list_filter = ['project_type', 'status', 'created_at']
    search_fields = ['name', 'description', 'team__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description', 'project__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'github_username', 'current_vibe', 'productivity_score']
    list_filter = ['current_vibe']
    search_fields = ['user__username', 'user__email', 'github_username']
    readonly_fields = ['last_vibe_update']

@admin.register(Standup)
class StandupAdmin(admin.ModelAdmin):
    list_display = ['developer', 'project', 'date', 'mood']
    list_filter = ['date', 'mood']
    search_fields = ['developer__username', 'project__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']

@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'author', 'reviewer', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'project', 'details', 'timestamp']
    list_filter = ['timestamp', 'action']
    search_fields = ['user__username', 'action', 'details', 'project__name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'tracker', 'created_at', 'updated_at']
    list_filter = ['insight_type', 'created_at']
    search_fields = ['title', 'description', 'code_snippet', 'suggestion']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TaskBoard)
class TaskBoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'created_at']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TaskColumn)
class TaskColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'order', 'created_at']
    list_filter = ['board']
    search_fields = ['name', 'description', 'board__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AIInsightTracker)
class AIInsightTrackerAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'created_at']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CodeReviewInbox)
class CodeReviewInboxAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'created_at']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
