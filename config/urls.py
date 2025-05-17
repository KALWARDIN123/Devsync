"""
URL configuration for DevSync project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from core.views import health_check

# API patterns
api_patterns = [
    path('auth/', include('rest_framework.urls')),
    path('chat/', include('chat.urls')),
    path('ai/', include('ai.urls')),
    path('analytics/', include('analytics.urls')),
    path('tasks/', include('tasks.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_patterns)),
    path('health/', health_check, name='health_check'),
    
    # Documentation
    path('docs/', TemplateView.as_view(
        template_name='docs/index.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='docs'),
]

if settings.DEBUG:
    # Debug toolbar
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
    
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 