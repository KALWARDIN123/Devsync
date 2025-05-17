from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Team, Project, Task, DeveloperProfile, Standup, CodeReview

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class DeveloperProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DeveloperProfile
        fields = ('id', 'user', 'bio', 'github_username', 'current_vibe',
                 'productivity_score', 'skills', 'last_vibe_update')

class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'created_at', 'members', 'vibe_score')

class ProjectSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='team',
        write_only=True
    )

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'team', 'team_id',
                 'created_at', 'due_date', 'status')

class TaskSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True
    )
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'project', 'project_id',
                 'assigned_to', 'assigned_to_id', 'created_at', 'due_date',
                 'status', 'priority')

class StandupSerializer(serializers.ModelSerializer):
    developer = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True
    )

    class Meta:
        model = Standup
        fields = ('id', 'developer', 'project', 'project_id', 'date',
                 'yesterday_work', 'today_plan', 'blockers', 'mood',
                 'ai_summary', 'created_at')

class CodeReviewSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        source='task',
        write_only=True
    )
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = CodeReview
        fields = ('id', 'task', 'task_id', 'reviewer', 'code_snippet',
                 'ai_suggestions', 'status', 'created_at', 'updated_at') 