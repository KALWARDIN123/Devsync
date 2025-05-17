from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='teams')
    vibe_score = models.FloatField(default=0.0)  # Overall team morale score

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('completed', 'Completed'),
    ], default='planning')

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('completed', 'Completed'),
    ], default='todo')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')

    def __str__(self):
        return self.title

class DeveloperProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')
    bio = models.TextField(blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    current_vibe = models.CharField(max_length=20, choices=[
        ('great', 'Great!'),
        ('good', 'Good'),
        ('okay', 'Okay'),
        ('stressed', 'Stressed'),
        ('overwhelmed', 'Overwhelmed'),
    ], default='good')
    last_vibe_update = models.DateTimeField(auto_now=True)
    productivity_score = models.FloatField(default=0.0)
    skills = models.JSONField(default=list)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Standup(models.Model):
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standups')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='standups')
    date = models.DateField(default=timezone.now)
    yesterday_work = models.TextField()
    today_plan = models.TextField()
    blockers = models.TextField(blank=True)
    mood = models.CharField(max_length=20, choices=[
        ('great', 'Great!'),
        ('good', 'Good'),
        ('okay', 'Okay'),
        ('stressed', 'Stressed'),
        ('overwhelmed', 'Overwhelmed'),
    ], default='good')
    ai_summary = models.TextField(blank=True)  # AI-generated summary
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['developer', 'date']

    def __str__(self):
        return f"{self.developer.username}'s Standup - {self.date}"

class CodeReview(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='code_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    code_snippet = models.TextField()
    ai_suggestions = models.JSONField(default=list)  # AI-generated suggestions
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('needs_changes', 'Needs Changes'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Code Review for {self.task.title}"
