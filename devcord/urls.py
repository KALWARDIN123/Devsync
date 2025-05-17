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
    
    # Team URLs
    path('teams/create/', views.TeamCreateView.as_view(), name='team-create'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('teams/', views.TeamListView.as_view(), name='team-list'),
    
    # Task URLs
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.create_task_view, name='create-task'),
    
    # Activity URLs
    path('standups/create/', views.create_standup_view, name='create-standup'),
    path('code-review/', views.code_review_view, name='code-review'),
    path('team-vibe/', views.team_vibe_view, name='team-vibe'),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # Template URLs
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
] 