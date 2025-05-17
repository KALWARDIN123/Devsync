import os
from typing import List, Dict, Any
from openai import OpenAI
from django.conf import settings
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def handle_ai_errors(func):
    """Decorator to handle AI-related errors consistently."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"AI operation failed in {func.__name__}: {str(e)}")
            return {
                "error": True,
                "message": "AI operation failed. Please try again later.",
                "details": str(e) if settings.DEBUG else None
            }
    return wrapper

def get_ai_response(prompt: str, temperature: float = 0.7) -> str:
    """
    Get a response from OpenAI's API using the latest client.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        raise

@handle_ai_errors
def generate_standup_summary(commits: List[str], tasks: List[Dict[str, Any]], mood: str) -> Dict[str, Any]:
    """
    Generate an AI summary for a daily standup based on commits and tasks.
    """
    commits_text = '\\n'.join(commits)
    tasks_text = '\\n'.join([f"- {task['title']}: {task['status']}" for task in tasks])
    
    prompt = (
        f"Generate a concise daily standup summary based on the following information:\\n\\n"
        f"Commits:\\n{commits_text}\\n\\n"
        f"Tasks:\\n{tasks_text}\\n\\n"
        f"Developer's Mood: {mood}\\n\\n"
        f"Format the summary into:\\n"
        f"1. What was accomplished\\n"
        f"2. What's planned\\n"
        f"3. Any potential blockers\\n"
        f"4. Overall progress assessment"
    )
    summary = get_ai_response(prompt, temperature=0.5)
    return {"summary": summary, "error": False}

@handle_ai_errors
def review_code(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Generate an AI code review with suggestions and improvements.
    """
    prompt = (
        f"Review this {language} code and provide a structured analysis:\\n\\n"
        f"{language} code:\\n{code}\\n\\n"
        f"Please provide:\\n"
        f"1. Overall code quality assessment\\n"
        f"2. Potential bugs or issues\\n"
        f"3. Performance considerations\\n"
        f"4. Best practices suggestions\\n"
        f"5. Security concerns (if any)\\n"
        f"6. Specific improvement recommendations"
    )
    review = get_ai_response(prompt, temperature=0.3)
    
    severity = "low" if "no major issues" in review.lower() else "medium"
    return {
        "review": review,
        "severity": severity,
        "error": False
    }

@handle_ai_errors
def generate_feature_plan(idea: str) -> Dict[str, Any]:
    """
    Generate an AI-powered feature planning breakdown.
    """
    prompt = (
        f"Create a detailed feature planning breakdown for the following idea:\\n"
        f"{idea}\\n\\n"
        f"Please provide:\\n"
        f"1. User stories\\n"
        f"2. Technical requirements\\n"
        f"3. Implementation steps\\n"
        f"4. Potential challenges\\n"
        f"5. Estimated effort (in story points)"
    )
    plan = get_ai_response(prompt, temperature=0.4)
    
    return {
        "plan": plan,
        "type": "feature_plan",
        "error": False
    }

@handle_ai_errors
def analyze_team_vibe(messages: List[str], activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze team vibe based on messages and activities.
    """
    messages_text = '\\n'.join(messages)
    activities_text = '\\n'.join([f"- {activity['type']}: {activity['description']}" for activity in activities])
    
    prompt = (
        f"Analyze the team's vibe based on the following data:\\n\\n"
        f"Recent Messages:\\n{messages_text}\\n\\n"
        f"Activities:\\n{activities_text}\\n\\n"
        f"Provide:\\n"
        f"1. Overall team mood assessment\\n"
        f"2. Productivity indicators\\n"
        f"3. Collaboration quality\\n"
        f"4. Stress/workload balance\\n"
        f"5. Numeric vibe score (0-10)"
    )
    analysis = get_ai_response(prompt, temperature=0.4)
    
    # Extract numeric score from analysis
    try:
        score = float([line for line in analysis.split('\\n') if 'score' in line.lower()][0].split(':')[1].strip())
    except:
        score = 7.0  # Default score if parsing fails
        logger.warning("Could not parse vibe score from AI response, using default")
    
    return {
        "analysis": analysis,
        "vibe_score": score,
        "error": False
    } 