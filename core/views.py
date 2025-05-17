"""
Core views for the DevSync project.
"""
from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from redis import Redis
from redis.exceptions import RedisError

@never_cache
@require_GET
def health_check(request):
    """
    Health check endpoint for monitoring service health.
    Checks:
    - Database connection
    - Redis connection
    - Application status
    """
    health = {
        'status': 'healthy',
        'services': {
            'database': True,
            'redis': True,
            'application': True
        },
        'details': {}
    }

    # Check database
    try:
        connections['default'].cursor()
    except Exception as e:
        health['status'] = 'unhealthy'
        health['services']['database'] = False
        health['details']['database_error'] = str(e)

    # Check Redis
    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
    except RedisError as e:
        health['status'] = 'unhealthy'
        health['services']['redis'] = False
        health['details']['redis_error'] = str(e)
    except Exception as e:
        health['status'] = 'unhealthy'
        health['services']['redis'] = False
        health['details']['redis_error'] = str(e)

    # Add version info
    health['version'] = getattr(settings, 'VERSION', 'unknown')
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code) 