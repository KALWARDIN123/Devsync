from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
from django.urls import reverse

class Team(models.Model):
    TEAM_TYPES = (
        ('individual', 'Individual'),
        ('group', 'Group'),
    )

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    team_type = models.CharField(max_length=20, choices=TEAM_TYPES, default='individual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    members = models.ManyToManyField(User, through='TeamMember', related_name='teams')
    invite_code = models.CharField(max_length=8, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('developer', 'Developer'),
        ('reviewer', 'Reviewer'),
    )

    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('away', 'Away'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team.name} ({self.role})"

class Project(models.Model):
    PROJECT_TYPES = (
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('fullstack', 'Full Stack'),
        ('mobile', 'Mobile App'),
        ('desktop', 'Desktop App'),
        ('data', 'Data Science'),
        ('other', 'Other')
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    )
    
    ROLE_CHOICES = (
        ('maintainer', 'Maintainer'),
        ('contributor', 'Contributor'),
        ('reviewer', 'Reviewer')
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')
    github_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.JSONField(default=list, blank=True, help_text='Project tags for categorization')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_project_analytics', 'Can view project analytics'),
            ('manage_project_members', 'Can manage project members'),
            ('archive_project', 'Can archive project'),
            ('submit_code_review', 'Can submit code for review'),
            ('review_code', 'Can review code submissions'),
            ('manage_tasks', 'Can manage project tasks')
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'project_id': self.id})

    @property
    def completion_percentage(self):
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return int((completed_tasks / total_tasks) * 100)

    @property
    def active_members(self):
        return self.team.members.filter(status='active')

    @property
    def recent_activities(self):
        return self.activities.order_by('-timestamp')[:10]

    def add_member(self, user, role='contributor'):
        """Add a user to the project team with a specific role"""
        if not self.team.members.filter(user=user).exists():
            TeamMember.objects.create(
                team=self.team,
                user=user,
                role=role
            )
        # Set project-specific role
        ProjectMember.objects.create(
            project=self,
            user=user,
            role=role
        )

    def remove_member(self, user):
        """Remove a user from the project team"""
        self.team.members.filter(user=user).delete()
        self.project_members.filter(user=user).delete()

    def archive(self):
        """Archive the project"""
        self.status = 'archived'
        self.save()

    def complete(self):
        """Mark the project as completed"""
        self.status = 'completed'
        self.save()

    def reactivate(self):
        """Reactivate an archived or completed project"""
        self.status = 'active'
        self.save()

    def can_user_edit(self, user):
        """Check if a user can edit this project"""
        return self.project_members.filter(
            user=user,
            role='maintainer'
        ).exists() or self.team.members.filter(
            user=user,
            role__in=['admin', 'leader']
        ).exists()

    def can_user_view(self, user):
        """Check if a user can view this project"""
        return self.team.members.filter(user=user).exists()

    def can_user_review_code(self, user):
        """Check if a user can review code"""
        return self.project_members.filter(
            user=user,
            role__in=['maintainer', 'reviewer']
        ).exists()

    def can_user_submit_review(self, user):
        """Check if a user can submit code for review"""
        return self.project_members.filter(
            user=user,
            role__in=['maintainer', 'contributor']
        ).exists()

    def get_task_stats(self):
        """Get project task statistics"""
        return {
            'total': self.tasks.count(),
            'completed': self.tasks.filter(status='completed').count(),
            'in_progress': self.tasks.filter(status='in_progress').count(),
            'pending': self.tasks.filter(status='pending').count()
        }

    def get_review_stats(self):
        """Get project code review statistics"""
        return {
            'total': self.code_reviews.count(),
            'approved': self.code_reviews.filter(status='approved').count(),
            'pending': self.code_reviews.filter(status='pending').count(),
            'changes_requested': self.code_reviews.filter(status='changes_requested').count()
        }

    def get_member_stats(self):
        """Get project member statistics"""
        return {
            'total': self.project_members.count(),
            'maintainers': self.project_members.filter(role='maintainer').count(),
            'contributors': self.project_members.filter(role='contributor').count(),
            'reviewers': self.project_members.filter(role='reviewer').count()
        }

    def log_activity(self, user, action, details=None):
        """Log a project activity"""
        ActivityLog.objects.create(
            user=user,
            project=self,
            action=action,
            details=details
        )

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('completed', 'Completed')
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('task-detail', kwargs={'task_id': self.id})

    def assign_to(self, user):
        """Assign the task to a user"""
        self.assigned_to = user
        self.save()
        self.project.log_activity(
            user=user,
            action='assigned task',
            details=f'Task "{self.title}" assigned to {user.get_full_name()}'
        )

    def complete(self, user):
        """Mark the task as completed"""
        self.status = 'completed'
        self.save()
        self.project.log_activity(
            user=user,
            action='completed task',
            details=f'Task "{self.title}" marked as completed'
        )

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
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested')
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='code_reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    github_pr_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('code-review-detail', kwargs={'review_id': self.id})

    def assign_reviewer(self, user):
        """Assign a reviewer to the code review"""
        self.reviewer = user
        self.save()
        self.project.log_activity(
            user=user,
            action='assigned as reviewer',
            details=f'Code review "{self.title}" assigned to {user.get_full_name()}'
        )

    def approve(self, user, comment=None):
        """Approve the code review"""
        self.status = 'approved'
        self.save()
        if comment:
            CodeReviewComment.objects.create(
                review=self,
                author=user,
                content=comment
            )
        self.project.log_activity(
            user=user,
            action='approved code review',
            details=f'Code review "{self.title}" approved'
        )

    def request_changes(self, user, comment):
        """Request changes for the code review"""
        self.status = 'changes_requested'
        self.save()
        CodeReviewComment.objects.create(
            review=self,
            author=user,
            content=comment
        )
        self.project.log_activity(
            user=user,
            action='requested changes',
            details=f'Changes requested for code review "{self.title}"'
        )

class CodeReviewComment(models.Model):
    review = models.ForeignKey(CodeReview, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.get_full_name()} on {self.review.title}'

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    target_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'project', 'team', 'code-review'
    target_id = models.IntegerField(blank=True, null=True)  # ID of the target object
    target_name = models.CharField(max_length=255, blank=True, null=True)  # Name of the target object
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        if self.target_name:
            return f'{self.user.get_full_name()} {self.action} {self.target_name} at {self.timestamp}'
        return f'{self.user.get_full_name()} {self.action} at {self.timestamp}'

class AIInsightTracker(models.Model):
    INSIGHT_TYPES = (
        ('code_quality', 'Code Quality'),
        ('performance', 'Performance'),
        ('security', 'Security'),
        ('best_practices', 'Best Practices'),
        ('other', 'Other')
    )

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='ai_tracker')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"

class AIInsight(models.Model):
    INSIGHT_TYPES = (
        ('code_quality', 'Code Quality'),
        ('performance', 'Performance'),
        ('security', 'Security'),
        ('best_practices', 'Best Practices'),
        ('other', 'Other')
    )

    tracker = models.ForeignKey(AIInsightTracker, on_delete=models.CASCADE, related_name='insights', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES, default='other')
    code_snippet = models.TextField(blank=True)
    suggestion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.tracker.project.name if self.tracker else 'No Project'}"

class TeamInvite(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired')
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invites')
    email = models.EmailField()
    invite_code = models.CharField(max_length=8)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Invite for {self.email} to {self.team.name}"

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_members')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=Project.ROLE_CHOICES, default='contributor')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['role', 'created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} in {self.project.name}"

class TaskBoard(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='task_board')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"

class TaskColumn(models.Model):
    board = models.ForeignKey(TaskBoard, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - {self.board.name}"

class CodeReviewInbox(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='review_inbox')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"

    def get_pending_reviews(self):
        """Get pending code reviews"""
        return self.project.code_reviews.filter(status='pending')

    def get_recent_reviews(self):
        """Get recent code reviews"""
        return self.project.code_reviews.order_by('-created_at')[:10]

    def get_review_stats(self):
        """Get code review statistics"""
        reviews = self.project.code_reviews
        return {
            'total': reviews.count(),
            'pending': reviews.filter(status='pending').count(),
            'approved': reviews.filter(status='approved').count(),
            'changes_requested': reviews.filter(status='changes_requested').count()
        }
