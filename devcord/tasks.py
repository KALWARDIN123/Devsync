from celery import shared_task
from .ai_utils import (
    generate_standup_summary,
    review_code,
    generate_feature_plan,
    analyze_team_vibe
)
from .models import Standup, CodeReview, Task, Team
from django.utils import timezone
from typing import List, Dict, Any

@shared_task
def process_standup_summary(standup_id: int) -> None:
    """
    Generate an AI summary for a standup and update the record.
    """
    try:
        standup = Standup.objects.get(id=standup_id)
        # Get relevant commits and tasks
        commits = []  # TODO: Integrate with GitHub API
        tasks = Task.objects.filter(
            assigned_to=standup.developer,
            project=standup.project
        ).values('title', 'status')

        summary = generate_standup_summary(
            commits=commits,
            tasks=list(tasks),
            mood=standup.mood
        )
        
        standup.ai_summary = summary
        standup.save()
    except Standup.DoesNotExist:
        print(f"Standup {standup_id} not found")

@shared_task
def process_code_review(review_id: int) -> None:
    """
    Generate an AI code review and update the record.
    """
    try:
        code_review = CodeReview.objects.get(id=review_id)
        result = review_code(
            code=code_review.code_snippet,
            language="python"  # TODO: Add language detection
        )
        
        code_review.ai_suggestions = result
        code_review.save()
    except CodeReview.DoesNotExist:
        print(f"Code review {review_id} not found")

@shared_task
def analyze_team_activity(team_id: int) -> None:
    """
    Analyze team activity and update the team's vibe score.
    """
    try:
        team = Team.objects.get(id=team_id)
        
        # Get recent messages and activities
        messages = []  # TODO: Integrate with chat system
        activities = []  # TODO: Get from activity log
        
        result = analyze_team_vibe(messages, activities)
        
        team.vibe_score = result['vibe_score']
        team.save()
    except Team.DoesNotExist:
        print(f"Team {team_id} not found")

@shared_task
def process_feature_planning(idea: str) -> Dict[str, Any]:
    """
    Generate an AI-powered feature plan.
    """
    return generate_feature_plan(idea)

@shared_task
def daily_team_analysis() -> None:
    """
    Daily task to analyze all teams' activities and update vibe scores.
    """
    for team in Team.objects.all():
        analyze_team_activity.delay(team.id) 