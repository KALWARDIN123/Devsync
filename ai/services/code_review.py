"""
AI service for code review functionality.
"""
import json
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import openai
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI

def rate_limit(key_prefix: str, limit: int = 10, period: int = 60) -> Callable:
    """
    Rate limiting decorator.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = f"rate_limit:{key_prefix}:{int(time.time()) // period}"
            count = cache.get(cache_key, 0)
            
            if count >= limit:
                raise Exception(f"Rate limit exceeded. Try again in {period} seconds.")
            
            cache.set(cache_key, count + 1, period)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass

class RateLimitError(AIServiceError):
    """Rate limit exceeded."""
    pass

class APIError(AIServiceError):
    """OpenAI API error."""
    pass

class CodeReviewService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    @rate_limit(key_prefix="code_review", limit=10, period=60)
    def analyze_code(self, code: str, context: Optional[Dict] = None) -> Dict:
        """
        Analyze code using OpenAI's GPT model with retries and error handling.
        
        Args:
            code: The code to analyze
            context: Optional context about the code (language, framework, etc.)
        
        Returns:
            Dict containing analysis results
            
        Raises:
            AIServiceError: If the analysis fails after retries
        """
        context = context or {}
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                system_message = self._build_system_message(context)
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Please review this code and provide feedback:\n\n{code}"}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                feedback = response.choices[0].message.content
                return {
                    'status': 'success',
                    'feedback': feedback,
                    'suggestions': self._parse_suggestions(feedback),
                    'security_issues': self._extract_security_issues(feedback),
                    'performance_issues': self._extract_performance_issues(feedback),
                    'best_practices': self._extract_best_practices(feedback),
                }

            except openai.RateLimitError as e:
                raise RateLimitError("OpenAI rate limit exceeded. Please try again later.") from e
                
            except openai.APIError as e:
                last_error = e
                attempt += 1
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff
                continue
                
            except Exception as e:
                raise AIServiceError(f"Unexpected error during code analysis: {str(e)}") from e

        raise APIError(f"Failed to analyze code after {self.max_retries} attempts. Last error: {str(last_error)}")

    def _build_system_message(self, context: Dict) -> str:
        """Build system message based on context."""
        base_message = "You are a senior software engineer performing a code review."
        
        if context.get('language'):
            base_message += f"\nThe code is written in {context['language']}."
        if context.get('framework'):
            base_message += f"\nIt uses the {context['framework']} framework."
        
        base_message += """
        Please analyze the code for:
        1. Security vulnerabilities
        2. Performance issues
        3. Best practices violations
        4. Code style issues
        5. Potential bugs
        
        Format your response with clear sections:
        - Security Issues
        - Performance Concerns
        - Best Practices
        - Style Guide Violations
        - Suggested Improvements
        """
        
        return base_message

    def _parse_suggestions(self, feedback: str) -> List[str]:
        """Parse feedback for actionable suggestions."""
        suggestions = []
        current_section = None
        
        for line in feedback.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.endswith(':') and line[:-1].upper() == line[:-1]:
                current_section = line[:-1]
                continue
                
            if line.startswith('-') or line.startswith('*'):
                suggestions.append({
                    'section': current_section,
                    'suggestion': line[1:].strip()
                })
                
        return suggestions

    def _extract_security_issues(self, feedback: str) -> List[str]:
        """Extract security-related issues from feedback."""
        return self._extract_section(feedback, 'Security Issues')

    def _extract_performance_issues(self, feedback: str) -> List[str]:
        """Extract performance-related issues from feedback."""
        return self._extract_section(feedback, 'Performance Concerns')

    def _extract_best_practices(self, feedback: str) -> List[str]:
        """Extract best practices from feedback."""
        return self._extract_section(feedback, 'Best Practices')

    def _extract_section(self, feedback: str, section_name: str) -> List[str]:
        """Extract items from a specific section of the feedback."""
        issues = []
        in_section = False
        
        for line in feedback.split('\n'):
            line = line.strip()
            
            if not line:
                continue
                
            if line.upper() == section_name.upper() + ':':
                in_section = True
                continue
                
            if in_section:
                if line.endswith(':') and line[:-1].upper() == line[:-1]:
                    break
                if line.startswith('-') or line.startswith('*'):
                    issues.append(line[1:].strip())
                    
        return issues

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit='10/m'
)
def async_code_review(self, code: str, context: Optional[Dict] = None) -> Dict:
    """
    Asynchronous task for code review with retries and rate limiting.
    """
    try:
        service = CodeReviewService()
        return service.analyze_code(code, context)
    except (RateLimitError, APIError) as exc:
        raise self.retry(exc=exc)
    except Exception as exc:
        # Log the error but don't retry on unexpected errors
        print(f"Unexpected error in async_code_review: {str(exc)}")
        raise 