from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'teams', views.TeamViewSet, basename='team')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'profiles', views.DeveloperProfileViewSet, basename='profile')
router.register(r'standups', views.StandupViewSet, basename='standup')
router.register(r'code-reviews', views.CodeReviewViewSet, basename='code-review')

# URL patterns
urlpatterns = [
    # Authentication URLs
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # User Profile URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    
    # Dashboard URL
    path('', views.dashboard, name='dashboard'),
    
    # Activity URLs
    path('activity/', views.ActivityListView.as_view(), name='activity-list'),
    path('refresh-insights/', views.refresh_insights, name='refresh-insights'),
    
    # Team URLs
    path('teams/', views.TeamListView.as_view(), name='team-list'),
    path('teams/create/', views.create_team, name='team-create'),
    path('teams/<int:team_id>/edit/', views.team_edit, name='team-edit'),
    path('teams/<int:team_id>/delete/', views.team_delete, name='team-delete'),
    path('teams/<int:team_id>/invite/', views.team_invite, name='team-invite'),
    path('teams/join/', views.join_team, name='team-join'),
    path('teams/<int:team_id>/members/<int:member_id>/remove/', views.remove_team_member, name='remove-team-member'),
    path('teams/<int:team_id>/', views.team_detail, name='team-detail'),
    
    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/create/', views.create_project, name='project-create'),
    path('projects/create/<int:team_id>/', views.create_project, name='project-create-team'),
    path('projects/<int:project_id>/', views.project_detail, name='project-detail'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='project-edit'),
    path('projects/<int:project_id>/archive/', views.archive_project, name='project-archive'),
    
    # Task URLs
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.create_task, name='create-task'),
    path('tasks/<int:task_id>/', views.task_detail, name='task-detail'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='task-edit'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='task-complete'),
    path('tasks/<int:task_id>/assign/<int:user_id>/', views.assign_task, name='task-assign'),
    
    # Code Review URLs
    path('code-reviews/', views.CodeReviewListView.as_view(), name='code-review-list'),
    path('code-reviews/create/', views.create_code_review, name='create-code-review'),
    path('code-reviews/<int:review_id>/', views.CodeReviewDetailView.as_view(), name='code-review-detail'),
    path('code-reviews/<int:review_id>/edit/', views.edit_code_review, name='code-review-edit'),
    path('code-reviews/<int:review_id>/approve/', views.approve_code_review, name='code-review-approve'),
    path('code-reviews/<int:review_id>/request-changes/', views.request_code_review_changes, name='code-review-request-changes'),
    path('code-reviews/<int:review_id>/assign/<int:user_id>/', views.assign_code_review, name='code-review-assign'),
    path('code-reviews/<int:review_id>/comment/', views.add_code_review_comment, name='code-review-comment'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/teams/<int:team_id>/members/', views.get_team_members, name='api-team-members'),
] 