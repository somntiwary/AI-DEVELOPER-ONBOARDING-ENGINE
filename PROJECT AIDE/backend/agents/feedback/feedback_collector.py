"""
Feedback Collector
==================
Collects, validates, and stores user feedback from onboarding experiences.
Tracks satisfaction, identifies failure points, and categorizes feedback types.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    SATISFACTION = "satisfaction"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"
    SUCCESS_STORY = "success_story"
    FAILURE_ANALYSIS = "failure_analysis"

class FeedbackSeverity(Enum):
    """Severity levels for feedback."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class UserFeedback:
    """Structured feedback data model."""
    feedback_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    feedback_type: FeedbackType
    severity: FeedbackSeverity
    rating: Optional[int] = None  # 1-5 scale
    title: str = ""
    description: str = ""
    context: Dict[str, Any] = None
    agent_involved: Optional[str] = None
    step_failed: Optional[str] = None
    suggested_fix: Optional[str] = None
    user_experience: Optional[str] = None
    tags: List[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.tags is None:
            self.tags = []

class FeedbackCollector:
    """
    Collects and manages user feedback from AIDE onboarding experiences.
    Provides structured data collection, validation, and storage.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.feedback_dir = self.project_path / "backend" / "feedback_data"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize feedback storage
        self.feedback_file = self.feedback_dir / "feedback.json"
        self.analytics_file = self.feedback_dir / "analytics.json"
        
        # Load existing feedback
        self.feedback_data = self._load_feedback_data()
        self.analytics_data = self._load_analytics_data()

    def _load_feedback_data(self) -> List[Dict[str, Any]]:
        """Load existing feedback data from storage."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load feedback data: {e}")
        return []

    def _load_analytics_data(self) -> Dict[str, Any]:
        """Load analytics data from storage."""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load analytics data: {e}")
        return {
            "total_feedback": 0,
            "satisfaction_scores": [],
            "common_issues": {},
            "agent_performance": {},
            "improvement_areas": [],
            "last_updated": datetime.now().isoformat()
        }

    def _save_feedback_data(self):
        """Save feedback data to storage."""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save feedback data: {e}")

    def _save_analytics_data(self):
        """Save analytics data to storage."""
        try:
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")

    def collect_feedback(
        self,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        description: str,
        rating: Optional[int] = None,
        title: str = "",
        severity: FeedbackSeverity = FeedbackSeverity.MEDIUM,
        agent_involved: Optional[str] = None,
        step_failed: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        user_experience: Optional[str] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Collect and store user feedback.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Session identifier for the onboarding experience
            feedback_type: Type of feedback being provided
            description: Detailed description of the feedback
            rating: Optional rating (1-5 scale)
            title: Optional title for the feedback
            severity: Severity level of the feedback
            agent_involved: Which agent was involved in the issue
            step_failed: Which step in the onboarding process failed
            suggested_fix: User's suggested fix for the issue
            user_experience: Description of user's overall experience
            tags: Optional tags for categorization
            context: Additional context data
            
        Returns:
            feedback_id: Unique identifier for the collected feedback
        """
        feedback_id = str(uuid.uuid4())
        
        # Validate rating if provided
        if rating is not None and not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        # Create feedback object
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            feedback_type=feedback_type,
            severity=severity,
            rating=rating,
            title=title,
            description=description,
            context=context or {},
            agent_involved=agent_involved,
            step_failed=step_failed,
            suggested_fix=suggested_fix,
            user_experience=user_experience,
            tags=tags or []
        )
        
        # Convert to dict and store
        feedback_dict = asdict(feedback)
        feedback_dict['timestamp'] = feedback.timestamp.isoformat()
        feedback_dict['feedback_type'] = feedback.feedback_type.value
        feedback_dict['severity'] = feedback.severity.value
        
        self.feedback_data.append(feedback_dict)
        self._save_feedback_data()
        
        # Update analytics
        self._update_analytics(feedback_dict)
        
        logger.info(f"Collected feedback {feedback_id} from user {user_id}")
        return feedback_id

    def collect_satisfaction_survey(
        self,
        user_id: str,
        session_id: str,
        overall_rating: int,
        onboarding_time_minutes: int,
        agents_used: List[str],
        most_helpful_agent: Optional[str] = None,
        least_helpful_agent: Optional[str] = None,
        would_recommend: bool = True,
        additional_comments: str = ""
    ) -> str:
        """
        Collect structured satisfaction survey data.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            overall_rating: Overall satisfaction rating (1-5)
            onboarding_time_minutes: Time taken for onboarding
            agents_used: List of agents that were used
            most_helpful_agent: Which agent was most helpful
            least_helpful_agent: Which agent was least helpful
            would_recommend: Whether user would recommend AIDE
            additional_comments: Additional comments from user
            
        Returns:
            feedback_id: Unique identifier for the survey
        """
        context = {
            "onboarding_time_minutes": onboarding_time_minutes,
            "agents_used": agents_used,
            "most_helpful_agent": most_helpful_agent,
            "least_helpful_agent": least_helpful_agent,
            "would_recommend": would_recommend,
            "survey_type": "satisfaction"
        }
        
        description = f"Onboarding completed in {onboarding_time_minutes} minutes. "
        if most_helpful_agent:
            description += f"Most helpful: {most_helpful_agent}. "
        if least_helpful_agent:
            description += f"Least helpful: {least_helpful_agent}. "
        if additional_comments:
            description += f"Comments: {additional_comments}"
        
        return self.collect_feedback(
            user_id=user_id,
            session_id=session_id,
            feedback_type=FeedbackType.SATISFACTION,
            description=description,
            rating=overall_rating,
            title="Onboarding Satisfaction Survey",
            severity=FeedbackSeverity.LOW,
            context=context,
            tags=["survey", "satisfaction", "onboarding"]
        )

    def collect_failure_analysis(
        self,
        user_id: str,
        session_id: str,
        agent_involved: str,
        step_failed: str,
        error_message: str,
        user_actions: List[str],
        suggested_fix: Optional[str] = None,
        severity: FeedbackSeverity = FeedbackSeverity.HIGH
    ) -> str:
        """
        Collect detailed failure analysis data.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_involved: Which agent failed
            step_failed: Which step failed
            error_message: Error message or description
            user_actions: List of actions user took before failure
            suggested_fix: Optional suggested fix
            severity: Severity of the failure
            
        Returns:
            feedback_id: Unique identifier for the failure analysis
        """
        context = {
            "error_message": error_message,
            "user_actions": user_actions,
            "failure_type": "agent_failure"
        }
        
        description = f"Agent {agent_involved} failed at step '{step_failed}'. "
        description += f"Error: {error_message}. "
        description += f"User actions: {', '.join(user_actions)}"
        
        return self.collect_feedback(
            user_id=user_id,
            session_id=session_id,
            feedback_type=FeedbackType.FAILURE_ANALYSIS,
            description=description,
            title=f"Failure Analysis: {agent_involved}",
            severity=severity,
            agent_involved=agent_involved,
            step_failed=step_failed,
            suggested_fix=suggested_fix,
            context=context,
            tags=["failure", "analysis", agent_involved]
        )

    def _update_analytics(self, feedback_dict: Dict[str, Any]):
        """Update analytics data based on new feedback."""
        self.analytics_data["total_feedback"] += 1
        
        # Update satisfaction scores
        if feedback_dict.get("rating"):
            self.analytics_data["satisfaction_scores"].append(feedback_dict["rating"])
        
        # Update common issues
        agent = feedback_dict.get("agent_involved", "unknown")
        if agent not in self.analytics_data["agent_performance"]:
            self.analytics_data["agent_performance"][agent] = {
                "total_feedback": 0,
                "failures": 0,
                "successes": 0,
                "avg_rating": 0
            }
        
        agent_perf = self.analytics_data["agent_performance"][agent]
        agent_perf["total_feedback"] += 1
        
        if feedback_dict["feedback_type"] == "failure_analysis":
            agent_perf["failures"] += 1
        else:
            agent_perf["successes"] += 1
        
        # Update average rating
        if feedback_dict.get("rating"):
            current_avg = agent_perf["avg_rating"]
            total_rated = len([f for f in self.feedback_data if f.get("rating")])
            agent_perf["avg_rating"] = ((current_avg * (total_rated - 1)) + feedback_dict["rating"]) / total_rated
        
        # Update common issues
        issue_key = f"{agent}:{feedback_dict.get('step_failed', 'unknown')}"
        if issue_key not in self.analytics_data["common_issues"]:
            self.analytics_data["common_issues"][issue_key] = 0
        self.analytics_data["common_issues"][issue_key] += 1
        
        self.analytics_data["last_updated"] = datetime.now().isoformat()
        self._save_analytics_data()

    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of feedback for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_feedback = [
            f for f in self.feedback_data
            if datetime.fromisoformat(f["timestamp"]) >= cutoff_date
        ]
        
        if not recent_feedback:
            return {"message": "No feedback in the specified period"}
        
        # Calculate summary statistics
        total_feedback = len(recent_feedback)
        satisfaction_ratings = [f["rating"] for f in recent_feedback if f.get("rating")]
        avg_rating = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0
        
        # Count by type
        feedback_types = {}
        for f in recent_feedback:
            ftype = f["feedback_type"]
            feedback_types[ftype] = feedback_types.get(ftype, 0) + 1
        
        # Count by agent
        agent_feedback = {}
        for f in recent_feedback:
            agent = f.get("agent_involved", "unknown")
            agent_feedback[agent] = agent_feedback.get(agent, 0) + 1
        
        return {
            "period_days": days,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "feedback_by_type": feedback_types,
            "feedback_by_agent": agent_feedback,
            "satisfaction_ratings": satisfaction_ratings,
            "recent_feedback": recent_feedback[-10:]  # Last 10 feedback items
        }

    def get_agent_performance(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for agents."""
        if agent_name:
            return self.analytics_data["agent_performance"].get(agent_name, {})
        return self.analytics_data["agent_performance"]

    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for improvement based on feedback analysis."""
        recommendations = []
        
        # Analyze common issues
        common_issues = self.analytics_data["common_issues"]
        sorted_issues = sorted(common_issues.items(), key=lambda x: x[1], reverse=True)
        
        for issue, count in sorted_issues[:5]:  # Top 5 issues
            agent, step = issue.split(":", 1)
            recommendations.append({
                "type": "common_issue",
                "priority": "high" if count > 5 else "medium",
                "description": f"Agent '{agent}' frequently fails at step '{step}' ({count} times)",
                "suggestion": f"Review and improve {agent} agent's handling of '{step}' step",
                "affected_agent": agent,
                "frequency": count
            })
        
        # Analyze low-rated agents
        agent_performance = self.analytics_data["agent_performance"]
        for agent, perf in agent_performance.items():
            if perf["avg_rating"] < 3.0 and perf["total_feedback"] > 2:
                recommendations.append({
                    "type": "low_rating",
                    "priority": "high",
                    "description": f"Agent '{agent}' has low average rating ({perf['avg_rating']:.2f})",
                    "suggestion": f"Investigate and improve {agent} agent's performance",
                    "affected_agent": agent,
                    "current_rating": perf["avg_rating"]
                })
        
        return recommendations

    def resolve_feedback(self, feedback_id: str, resolution_notes: str) -> bool:
        """Mark feedback as resolved with resolution notes."""
        for feedback in self.feedback_data:
            if feedback["feedback_id"] == feedback_id:
                feedback["resolved"] = True
                feedback["resolution_notes"] = resolution_notes
                self._save_feedback_data()
                logger.info(f"Resolved feedback {feedback_id}")
                return True
        return False
