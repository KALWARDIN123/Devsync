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
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Team, Project, Task, DeveloperProfile, Standup, CodeReview, TeamMember, ActivityLog, AIInsight, TeamInvite, TaskBoard, TaskColumn, AIInsightTracker, CodeReviewInbox
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
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .forms import TeamForm, TeamMemberForm, ProjectForm, TeamCreateForm, TeamInviteForm, TaskForm, CodeReviewForm, ProfileEditForm, SettingsForm
from django.db.utils import IntegrityError
import json

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
    form_class = ProfileEditForm
    template_name = 'devcord/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user.developer_profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['teams_count'] = Team.objects.filter(members=user).count()
        context['projects_count'] = Project.objects.filter(team__members=user).distinct().count()
        context['code_reviews_count'] = CodeReview.objects.filter(Q(author=user) | Q(reviewer=user)).count()
        context['tasks_count'] = Task.objects.filter(assigned_to=user).count()
        context['user_obj'] = user
        return context

# Settings View
class SettingsView(LoginRequiredMixin, UpdateView):
    model = DeveloperProfile
    form_class = SettingsForm
    template_name = 'devcord/settings.html'
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return self.request.user.developer_profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

# Registration View
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create a DeveloperProfile for the new user
        DeveloperProfile.objects.create(user=self.object)
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

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a team member
    if not team.members.filter(id=request.user.id).exists():
        messages.error(request, 'You do not have permission to view this team.')
        return redirect('dashboard')
    
    # Get team projects
    projects = team.projects.all().select_related('team')
    
    # Get team members with their roles
    team_members = TeamMember.objects.filter(team=team).select_related('user')
    
    # Get recent activities
    activities = ActivityLog.objects.filter(
        Q(project__team=team) | Q(target_type='team', target_id=team.id)
    ).order_by('-timestamp')[:10]
    
    context = {
        'team': team,
        'projects': projects,
        'team_members': team_members,
        'activities': activities,
        'can_edit': team.members.filter(
            teammember__user=request.user,
            teammember__role__in=['admin', 'leader']
        ).exists()
    }
    return render(request, 'devcord/team_detail.html', context)

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

@login_required
def refresh_insights(request):
    """
    Refresh AI insights for the user's teams and projects.
    """
    # Get user's teams
    user_teams = request.user.teams.all()
    
    # Get AI insights
    ai_insights = AIInsight.objects.filter(
        Q(tracker__project__team__in=user_teams),
        insight_type__in=['code_quality', 'performance', 'security', 'best_practices']
    ).select_related('tracker', 'tracker__project')[:5]
    
    # Render only the insights content
    return render(request, 'devcord/partials/ai_insights.html', {
        'ai_insights': ai_insights
    })

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

@login_required
def dashboard(request):
    # Get user's teams
    user_teams = request.user.teams.all()
    
    # Get active projects for user's teams
    active_projects = Project.objects.filter(
        team__in=user_teams,
        status='active'
    ).select_related('team')
    
    # Get team members count
    team_members_count = TeamMember.objects.filter(
        team__in=user_teams
    ).values('user').distinct().count()
    
    # Get pending reviews
    pending_reviews = CodeReview.objects.filter(
        Q(project__team__in=user_teams) & 
        (Q(reviewer=request.user) | Q(author=request.user)),
        status='pending'
    ).select_related('project', 'author')
    
    # Get recent activities
    recent_activities = ActivityLog.objects.filter(
        Q(user__in=TeamMember.objects.filter(team__in=user_teams).values('user')) |
        Q(user=request.user)
    )[:10]
    
    # Get AI insights
    ai_insights = AIInsight.objects.filter(
        Q(tracker__project__team__in=user_teams),
        insight_type__in=['code_quality', 'performance', 'security', 'best_practices']
    ).select_related('tracker', 'tracker__project')[:5]
    
    context = {
        'active_projects': active_projects,
        'active_projects_count': active_projects.count(),
        'team_members_count': team_members_count,
        'pending_reviews_count': pending_reviews.count(),
        'recent_activities': recent_activities,
        'ai_insights': ai_insights,
        'recent_code_reviews': pending_reviews[:5],
    }
    
    # Check if user has any projects
    if not active_projects.exists():
        context['show_onboarding'] = True
    
    return render(request, 'devcord/dashboard.html', context)

@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            try:
                team = form.save(commit=False)
                team.creator = request.user
                team.save()
                
                # Add creator as team leader
                TeamMember.objects.create(
                    team=team,
                    user=request.user,
                    role='leader',
                    status='active'
                )
                
                # Create initial team invite code
                team.save()  # This will generate the invite code
                
                messages.success(request, f'Team "{team.name}" created successfully!')
                return redirect('team-invite', team_id=team.id)
            except IntegrityError:
                form.add_error('name', 'A team with this name already exists. Please choose a different name.')
    else:
        form = TeamCreateForm()
    
    return render(request, 'teams/team_create.html', {
        'form': form,
        'title': 'Create New Team'
    })

def send_team_invite_email(team, email, invite_code, request):
    """
    Send team invite email to the specified email address.
    """
    context = {
        'team_name': team.name,
        'invite_code': invite_code,
        'join_url': request.build_absolute_uri(reverse('team-join')),
        'team_description': team.description,
        'inviter_name': request.user.get_full_name() or request.user.username,
        'expires_in_days': 7  # This matches the expiration in TeamInvite model
    }
    
    # Render email content from template
    html_content = render_to_string('emails/team_invite.html', context)
    text_content = render_to_string('emails/team_invite.txt', context)
    
    # Send the email
    send_mail(
        subject=f'Invitation to join {team.name} on DevSync',
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_content,
        fail_silently=False
    )

@login_required
def team_invite(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team leader
    if not TeamMember.objects.filter(team=team, user=request.user, role='leader').exists():
        messages.error(request, 'You do not have permission to invite members.')
        return redirect('team-detail', team_id=team.id)
    
    if request.method == 'POST':
        form = TeamInviteForm(request.POST)
        if form.is_valid():
            emails = [email.strip() for email in form.cleaned_data['emails'].split(',')]
            
            for email in emails:
                # Create or update invite
                invite, created = TeamInvite.objects.get_or_create(
                    team=team,
                    email=email,
                    defaults={
                        'created_by': request.user,
                        'status': 'pending',
                        'invite_code': team.invite_code
                    }
                )
                
                if not created:
                    invite.status = 'pending'
                    invite.created_by = request.user
                    invite.save()
                
                # Send invitation email
                join_url = request.build_absolute_uri(reverse('team-join'))
                context = {
                    'team_name': team.name,
                    'team_description': team.description,
                    'inviter_name': request.user.get_full_name() or request.user.username,
                    'invite_code': team.invite_code,
                    'join_url': join_url,
                    'expires_in_days': 7  # Set invite expiration
                }
                
                # Render email templates
                html_message = render_to_string('emails/team_invite.html', context)
                text_message = render_to_string('emails/team_invite.txt', context)
                
                # Send email
                try:
                    send_mail(
                        subject=f'Invitation to join {team.name} on DevSync',
                        message=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.success(request, f'Invitation sent to {email}')
                except Exception as e:
                    messages.error(request, f'Failed to send invitation to {email}: {str(e)}')
            
            return redirect('team-invite', team_id=team.id)
    else:
        form = TeamInviteForm()
    
    # Get pending invites
    pending_invites = TeamInvite.objects.filter(
        team=team,
        status='pending'
    ).order_by('-created_at')
    
    # Get team members
    team_members = TeamMember.objects.filter(team=team).select_related('user')
    
    return render(request, 'teams/team_invite.html', {
        'form': form,
        'team': team,
        'pending_invites': pending_invites,
        'team_members': team_members,
        'title': f'Invite Members to {team.name}'
    })

@login_required
def join_team(request):
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code')
        if not invite_code:
            messages.error(request, 'Please provide an invite code.')
            return redirect('dashboard')
        
        try:
            team = Team.objects.get(invite_code=invite_code, is_active=True)
            invite = TeamInvite.objects.get(
                team=team,
                email=request.user.email,
                status='pending'
            )
            
            # Check if already a member
            if team.members.filter(id=request.user.id).exists():
                messages.info(request, 'You are already a member of this team.')
                return redirect('team_detail', team_id=team.id)
            
            # Add user as team member
            TeamMember.objects.create(
                team=team,
                user=request.user,
                role='member',
                status='active'
            )
            
            # Update invite status
            invite.status = 'accepted'
            invite.save()
            
            messages.success(request, f'Welcome to {team.name}!')
            return redirect('team_detail', team_id=team.id)
            
        except Team.DoesNotExist:
            messages.error(request, 'Invalid invite code.')
        except TeamInvite.DoesNotExist:
            messages.error(request, 'No pending invite found for your email.')
    
    return redirect('dashboard')

@login_required
def remove_team_member(request, team_id, member_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team leader
    if not team.members.filter(teammember__user=request.user, teammember__role='leader').exists():
        messages.error(request, 'You do not have permission to remove members.')
        return redirect('team_detail', team_id=team.id)
    
    try:
        member = TeamMember.objects.get(team=team, user_id=member_id)
        if member.role == 'leader':
            messages.error(request, 'Cannot remove team leader.')
            return redirect('team_detail', team_id=team.id)
        
        member.delete()
        messages.success(request, 'Team member removed successfully.')
    except TeamMember.DoesNotExist:
        messages.error(request, 'Member not found.')
    
    return redirect('team_detail', team_id=team.id)

@login_required
def add_team_members(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team admin
    if not TeamMember.objects.filter(team=team, user=request.user, role='admin').exists():
        messages.error(request, 'You do not have permission to add team members.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            
            from django.contrib.auth.models import User
            user = User.objects.get(email=email)
            
            # Create team member
            TeamMember.objects.create(
                user=user,
                team=team,
                role=role
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action=f'added {user.get_full_name()} as {role}',
                target_type='team',
                target_id=team.id,
                target_name=team.name
            )
            
            messages.success(request, f'{user.get_full_name()} has been added to the team!')
            return redirect('team_detail', team_id=team.id)
    else:
        form = TeamMemberForm()
    
    context = {
        'form': form,
        'team': team,
        'team_members': TeamMember.objects.filter(team=team).select_related('user')
    }
    return render(request, 'devcord/add_team_members.html', context)

@login_required
def create_project(request, team_id=None):
    if team_id:
        team = get_object_or_404(Team, id=team_id)
        if not TeamMember.objects.filter(team=team, user=request.user).exists():
            messages.error(request, 'You do not have permission to create projects for this team.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            
            # Handle project type
            project_type = request.POST.get('project_type')
            if project_type:
                project.project_type = project_type
            
            # Handle tags
            tags = request.POST.get('tags')
            if tags:
                try:
                    project.tags = json.loads(tags)
                except json.JSONDecodeError:
                    project.tags = []
            
            project.save()
            
            # Create default project modules
            create_default_project_modules(project)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=project,
                action='created project',
                details=f'Created project "{project.name}"'
            )
            
            messages.success(request, f'Project "{project.name}" has been created!')
            return redirect('project-detail', project_id=project.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {'team': team_id} if team_id else {}
        form = ProjectForm(user=request.user, initial=initial)
    
    context = {
        'form': form,
        'team': team if team_id else None,
        'title': 'Create New Project'
    }
    return render(request, 'devcord/project_form.html', context)

def create_default_project_modules(project):
    """Create default modules for a new project"""
    # Create default task board
    TaskBoard.objects.create(
        project=project,
        name='Issues & Tasks',
        description='Track project issues and tasks'
    )
    
    # Create default task columns
    columns = ['To Do', 'In Progress', 'Review', 'Done']
    for order, name in enumerate(columns):
        TaskColumn.objects.create(
            board=project.task_board,
            name=name,
            order=order
        )
    
    # Create default AI insights tracker
    AIInsightTracker.objects.create(
        project=project,
        name='AI Insights',
        description='Track AI-generated insights and suggestions'
    )
    
    # Create code review inbox
    CodeReviewInbox.objects.create(
        project=project,
        name='Code Reviews',
        description='Track and manage code review requests'
    )

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has permission to edit
    if not project.can_user_edit(request.user):
        messages.error(request, 'You do not have permission to edit this project.')
        return redirect('project-detail', project_id=project.id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            
            # Handle tags
            tags = request.POST.get('tags')
            if tags:
                try:
                    project.tags = json.loads(tags)
                except json.JSONDecodeError:
                    project.tags = []
            
            project.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=project,
                action='updated project',
                details=f'Updated project "{project.name}"'
            )
            
            messages.success(request, f'Project "{project.name}" has been updated!')
            return redirect('project-detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project, user=request.user)
        if project.tags:
            form.initial['tags'] = json.dumps(project.tags)
    
    context = {
        'form': form,
        'project': project,
        'title': f'Edit {project.name}'
    }
    return render(request, 'devcord/project_form.html', context)

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to project
    if not project.can_user_view(request.user):
        messages.error(request, 'You do not have permission to view this project.')
        return redirect('dashboard')
    
    # Get project activity
    activities = project.recent_activities
    
    # Get project tasks
    tasks = project.tasks.all().select_related('assigned_to')
    
    # Get code reviews
    code_reviews = project.code_reviews.all().select_related('author', 'reviewer')
    
    # Get team members
    team_members = project.team.members.all().select_related('user')
    
    context = {
        'project': project,
        'activities': activities,
        'tasks': tasks,
        'code_reviews': code_reviews,
        'team_members': team_members,
        'can_edit': project.can_user_edit(request.user),
        'task_stats': project.get_task_stats(),
        'review_stats': project.get_review_stats(),
        'member_stats': project.get_member_stats()
    }
    return render(request, 'devcord/project_detail.html', context)

@login_required
def archive_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has permission to archive
    if not project.can_user_edit(request.user):
        messages.error(request, 'You do not have permission to archive this project.')
        return redirect('project-detail', project_id=project.id)
    
    if request.method == 'POST':
        project.archive()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            project=project,
            action='archived project',
            details=f'Archived project "{project.name}"'
        )
        
        messages.success(request, f'Project "{project.name}" has been archived.')
        return redirect('project-list')
    
    return redirect('project-detail', project_id=project.id)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'devcord/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(
            team__members=self.request.user
        ).select_related('team').prefetch_related('team__members', 'tasks')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_teams = self.request.user.teams.all()
        
        context['active_projects'] = self.get_queryset().filter(status='active')
        context['completed_projects'] = self.get_queryset().filter(status='completed')
        context['archived_projects'] = self.get_queryset().filter(status='archived')
        context['user_teams'] = user_teams
        
        return context

# Code Review Views
class CodeReviewListView(LoginRequiredMixin, ListView):
    model = CodeReview
    template_name = 'devcord/code_review_list.html'
    context_object_name = 'code_reviews'

    def get_queryset(self):
        user = self.request.user
        return CodeReview.objects.filter(
            Q(author=user) | Q(reviewer=user)
        ).select_related('project', 'author', 'reviewer').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['pending_reviews'] = self.get_queryset().filter(status='pending')
        context['my_submissions'] = CodeReview.objects.filter(author=user).order_by('-created_at')
        context['to_review'] = CodeReview.objects.filter(reviewer=user, status='pending')
        return context

@login_required
def create_code_review(request):
    project_id = request.GET.get('project')
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        if not project.can_user_view(request.user):
            messages.error(request, 'You do not have permission to create code reviews for this project.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = CodeReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            
            # Ensure user has access to the project
            if not review.project.can_user_view(request.user):
                messages.error(request, 'You do not have permission to create code reviews for this project.')
                return redirect('dashboard')
            
            review.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=review.project,
                action='created code review',
                details=f'Created code review "{review.title}"'
            )
            
            messages.success(request, f'Code review "{review.title}" has been created!')
            return redirect('code-review-detail', review_id=review.id)
    else:
        initial = {'project': project_id} if project_id else {}
        form = CodeReviewForm(user=request.user, initial=initial)
        if project_id:
            form.fields['project'].queryset = Project.objects.filter(id=project_id)
    
    context = {
        'form': form,
        'title': 'Create New Code Review'
    }
    return render(request, 'devcord/code_review_form.html', context)

class CodeReviewDetailView(LoginRequiredMixin, DetailView):
    model = CodeReview
    template_name = 'devcord/code_review_detail.html'
    context_object_name = 'review'
    pk_url_kwarg = 'review_id'

    def get_queryset(self):
        user = self.request.user
        return CodeReview.objects.filter(
            Q(author=user) | Q(reviewer=user) | Q(project__team__members=user)
        ).select_related('project', 'author', 'reviewer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review = self.get_object()
        context['can_review'] = self.request.user == review.reviewer
        context['is_author'] = self.request.user == review.author
        context['project'] = review.project
        context['team'] = review.project.team
        return context

@login_required
def add_code_review_comment(request, review_id):
    review = get_object_or_404(CodeReview, id=review_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = review.comments.create(
                author=request.user,
                content=content
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='commented on code review',
                target_type='code-review',
                target_id=review.id,
                target_name=review.title
            )
            
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Comment content is required.')
    
    return redirect('code-review-detail', review_id=review.id)

@login_required
def approve_code_review(request, review_id):
    review = get_object_or_404(CodeReview, id=review_id)
    
    # Check if user is the assigned reviewer
    if request.user != review.reviewer:
        messages.error(request, 'You are not authorized to approve this review.')
        return redirect('code-review-detail', review_id=review.id)
    
    if request.method == 'POST':
        review.status = 'approved'
        review.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='approved code review',
            target_type='code-review',
            target_id=review.id,
            target_name=review.title
        )
        
        messages.success(request, 'Code review approved successfully.')
    
    return redirect('code-review-detail', review_id=review.id)

@login_required
def request_code_review_changes(request, review_id):
    review = get_object_or_404(CodeReview, id=review_id)
    
    # Check if user is the assigned reviewer
    if request.user != review.reviewer:
        messages.error(request, 'You are not authorized to request changes for this review.')
        return redirect('code-review-detail', review_id=review.id)
    
    if request.method == 'POST':
        review.status = 'changes_requested'
        review.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='requested changes on code review',
            target_type='code-review',
            target_id=review.id,
            target_name=review.title
        )
        
        messages.success(request, 'Changes requested successfully.')
    
    return redirect('code-review-detail', review_id=review.id)

@login_required
def edit_code_review(request, review_id):
    review = get_object_or_404(CodeReview, id=review_id)
    
    # Check if user has permission to edit
    if request.user != review.author and request.user != review.reviewer:
        messages.error(request, 'You do not have permission to edit this code review.')
        return redirect('code-review-detail', review_id=review.id)
    
    if request.method == 'POST':
        form = CodeReviewForm(request.POST, instance=review, user=request.user)
        if form.is_valid():
            review = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=review.project,
                action='updated code review',
                details=f'Updated code review "{review.title}"'
            )
            
            messages.success(request, f'Code review "{review.title}" has been updated!')
            return redirect('code-review-detail', review_id=review.id)
    else:
        form = CodeReviewForm(instance=review, user=request.user)
    
    context = {
        'form': form,
        'review': review,
        'title': f'Edit {review.title}'
    }
    return render(request, 'devcord/code_review_form.html', context)

class ActivityListView(LoginRequiredMixin, ListView):
    model = ActivityLog
    template_name = 'devcord/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        return ActivityLog.objects.filter(
            Q(user=self.request.user) |
            Q(target_type='team', target_id__in=self.request.user.teams.values_list('id', flat=True))
        ).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Activity History'
        return context

@login_required
def team_edit(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team leader
    if not TeamMember.objects.filter(team=team, user=request.user, role='leader').exists():
        messages.error(request, 'You do not have permission to edit this team.')
        return redirect('team-detail', team_id=team.id)
    
    if request.method == 'POST':
        form = TeamCreateForm(request.POST, instance=team)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Team "{team.name}" has been updated!')
                return redirect('team-detail', team_id=team.id)
            except IntegrityError:
                form.add_error('name', 'A team with this name already exists. Please choose a different name.')
    else:
        form = TeamCreateForm(instance=team)
    
    return render(request, 'teams/team_edit.html', {
        'form': form,
        'team': team,
        'title': f'Edit {team.name}'
    })

@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is team leader
    if not TeamMember.objects.filter(team=team, user=request.user, role='leader').exists():
        messages.error(request, 'You do not have permission to delete this team.')
        return redirect('team-detail', team_id=team.id)
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Team "{team_name}" has been deleted.')
        return redirect('team-list')
    
    return redirect('team-detail', team_id=team.id)

@login_required
def create_task(request):
    project_id = request.GET.get('project')
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        if not project.can_user_view(request.user):
            messages.error(request, 'You do not have permission to create tasks for this project.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            
            # Ensure user has access to the project
            if not task.project.can_user_view(request.user):
                messages.error(request, 'You do not have permission to create tasks for this project.')
                return redirect('dashboard')
            
            task.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=task.project,
                action='created task',
                details=f'Created task "{task.title}"'
            )
            
            messages.success(request, f'Task "{task.title}" has been created!')
            return redirect('project-detail', project_id=task.project.id)
    else:
        initial = {'project': project_id} if project_id else {}
        form = TaskForm(initial=initial)
        if project_id:
            form.fields['project'].queryset = Project.objects.filter(id=project_id)
    
    context = {
        'form': form,
        'title': 'Create New Task'
    }
    return render(request, 'devcord/task_form.html', context)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has access to task's project
    if not task.project.can_user_view(request.user):
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('dashboard')
    
    context = {
        'task': task,
        'can_edit': task.project.can_user_edit(request.user)
    }
    return render(request, 'devcord/task_detail.html', context)

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has permission to edit
    if not task.project.can_user_edit(request.user):
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('task-detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                project=task.project,
                action='updated task',
                details=f'Updated task "{task.title}"'
            )
            
            messages.success(request, f'Task "{task.title}" has been updated!')
            return redirect('task-detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Edit {task.title}'
    }
    return render(request, 'devcord/task_form.html', context)

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has access to task's project
    if not task.project.can_user_view(request.user):
        messages.error(request, 'You do not have permission to complete this task.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        task.complete(request.user)
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def assign_task(request, task_id, user_id):
    task = get_object_or_404(Task, id=task_id)
    user = get_object_or_404(User, id=user_id)
    
    # Check if user has permission to assign tasks
    if not task.project.can_user_edit(request.user):
        messages.error(request, 'You do not have permission to assign tasks.')
        return redirect('task-detail', task_id=task.id)
    
    # Check if assigned user is a team member
    if not task.project.team.members.filter(user=user).exists():
        messages.error(request, 'User is not a member of the project team.')
        return redirect('task-detail', task_id=task.id)
    
    if request.method == 'POST':
        task.assign_to(user)
        messages.success(request, f'Task assigned to {user.get_full_name()}')
        return redirect('task-detail', task_id=task.id)
    
    return redirect('task-detail', task_id=task.id)

@login_required
def assign_code_review(request, review_id, user_id):
    review = get_object_or_404(CodeReview, id=review_id)
    user = get_object_or_404(User, id=user_id)
    
    # Check if user has permission to assign reviewers
    if request.user != review.author and not review.project.can_user_edit(request.user):
        messages.error(request, 'You do not have permission to assign reviewers.')
        return redirect('code-review-detail', review_id=review.id)
    
    # Check if assigned user is a team member
    if not review.project.team.members.filter(id=user.id).exists():
        messages.error(request, 'User is not a member of the project team.')
        return redirect('code-review-detail', review_id=review.id)
    
    if request.method == 'POST':
        review.assign_reviewer(user)
        messages.success(request, f'Code review assigned to {user.get_full_name()}')
        return redirect('code-review-detail', review_id=review.id)
    
    return redirect('code-review-detail', review_id=review.id)

@login_required
def get_team_members(request, team_id):
    """API endpoint to get team members"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user has access to the team
    if not team.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    members = team.members.all().values('id', 'username', 'first_name', 'last_name')
    return JsonResponse(list(members), safe=False)
