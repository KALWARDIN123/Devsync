from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Team, Project, Task, DeveloperProfile, Standup, CodeReview
from .serializers import (
    TeamSerializer, ProjectSerializer, TaskSerializer,
    DeveloperProfileSerializer, StandupSerializer, CodeReviewSerializer
)
from .tasks import (
    process_standup_summary,
    process_code_review,
    analyze_team_activity,
    process_feature_planning
)

# Team Views
class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    template_name = 'devcord/team_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.members.add(self.request.user)  # Add the creator as a team member
        return response

# Profile View
class ProfileView(LoginRequiredMixin, UpdateView):
    model = DeveloperProfile
    template_name = 'devcord/profile.html'
    fields = ['avatar', 'bio', 'github_username', 'linkedin_url', 'twitter_username']
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user.developer_profile

# Settings View
class SettingsView(LoginRequiredMixin, UpdateView):
    model = DeveloperProfile
    template_name = 'devcord/settings.html'
    fields = ['email_notifications', 'slack_notifications', 'theme_preference']
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return self.request.user.developer_profile

# Registration View
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # Log the user in after registration
        return response

# Template Views
class DashboardView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'devcord/dashboard.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.filter(members=self.request.user)
        context['tasks'] = Task.objects.filter(assigned_to=self.request.user)
        return context

class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'devcord/team_detail.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.all()
        context['members'] = self.object.members.all()
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'devcord/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = self.object.tasks.all()
        context['standups'] = self.object.standups.all().order_by('-date')[:5]
        return context

# AI-Powered Views
@login_required
def submit_code_review(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        language = request.POST.get('language', 'python')
        
        review = CodeReview.objects.create(
            task=None,  # Optional: Link to a task
            reviewer=request.user,
            code_snippet=code
        )
        
        # Trigger async code review
        process_code_review.delay(review.id)
        
        return JsonResponse({
            'status': 'processing',
            'review_id': review.id
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def submit_standup(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        yesterday = request.POST.get('yesterday_work')
        today = request.POST.get('today_plan')
        blockers = request.POST.get('blockers')
        mood = request.POST.get('mood', 'good')
        
        standup = Standup.objects.create(
            developer=request.user,
            project_id=project_id,
            yesterday_work=yesterday,
            today_plan=today,
            blockers=blockers,
            mood=mood
        )
        
        # Trigger async standup summary generation
        process_standup_summary.delay(standup.id)
        
        return JsonResponse({
            'status': 'processing',
            'standup_id': standup.id
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def check_ai_status(request, model_type, item_id):
    """
    Check the status of an AI-processed item (standup or code review).
    """
    if model_type == 'standup':
        item = get_object_or_404(Standup, id=item_id)
        ready = bool(item.ai_summary)
        data = item.ai_summary if ready else None
    elif model_type == 'code-review':
        item = get_object_or_404(CodeReview, id=item_id)
        ready = bool(item.ai_suggestions)
        data = item.ai_suggestions if ready else None
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid model type'})
    
    return JsonResponse({
        'status': 'ready' if ready else 'processing',
        'data': data
    })

@login_required
def update_team_vibe(request, team_id):
    """
    Manually trigger a team vibe analysis.
    """
    team = get_object_or_404(Team, id=team_id)
    
    # Ensure user is a member of the team
    if request.user not in team.members.all():
        return JsonResponse({
            'status': 'error',
            'message': 'Not authorized'
        })
    
    # Trigger async team analysis
    analyze_team_activity.delay(team.id)
    
    return JsonResponse({'status': 'processing'})

@login_required
def plan_feature(request):
    """
    Generate an AI-powered feature plan.
    """
    if request.method == 'POST':
        idea = request.POST.get('idea')
        if not idea:
            return JsonResponse({
                'status': 'error',
                'message': 'No idea provided'
            })
        
        # Process feature plan asynchronously
        task = process_feature_planning.delay(idea)
        
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# API Viewsets
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)

    @action(detail=True, methods=['post'])
    def update_vibe(self, request, pk=None):
        team = self.get_object()
        analyze_team_activity.delay(team.id)
        return Response({'status': 'processing'})

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(project__team__members=self.request.user)

class DeveloperProfileViewSet(viewsets.ModelViewSet):
    queryset = DeveloperProfile.objects.all()
    serializer_class = DeveloperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeveloperProfile.objects.filter(user=self.request.user)

class StandupViewSet(viewsets.ModelViewSet):
    queryset = Standup.objects.all()
    serializer_class = StandupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Standup.objects.filter(developer=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_summary(self, request, pk=None):
        standup = self.get_object()
        process_standup_summary.delay(standup.id)
        return Response({'status': 'processing'})

class CodeReviewViewSet(viewsets.ModelViewSet):
    queryset = CodeReview.objects.all()
    serializer_class = CodeReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CodeReview.objects.filter(reviewer=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_review(self, request, pk=None):
        review = self.get_object()
        process_code_review.delay(review.id)
        return Response({'status': 'processing'})

# Task Views
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'devcord/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)

@login_required
def create_standup_view(request):
    if request.method == 'POST':
        # Handle form submission
        return JsonResponse({'status': 'success'})
    return render(request, 'devcord/modals/create_standup.html')

@login_required
def code_review_view(request):
    if request.method == 'POST':
        # Handle form submission
        return JsonResponse({'status': 'success'})
    return render(request, 'devcord/modals/code_review.html')

@login_required
def create_task_view(request):
    if request.method == 'POST':
        # Handle form submission
        return JsonResponse({'status': 'success'})
    return render(request, 'devcord/modals/create_task.html')

@login_required
def team_vibe_view(request):
    if request.method == 'POST':
        # Handle form submission
        return JsonResponse({'status': 'success'})
    return render(request, 'devcord/modals/team_vibe.html')

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams created by the user
        context['created_teams'] = Team.objects.filter(creator=user)
        
        # Get teams where user is a member (excluding teams they created)
        context['member_teams'] = Team.objects.filter(members=user).exclude(creator=user)
        
        return context
