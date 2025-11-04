"""
Analytics Engine
================
Analyzes feedback data to identify patterns, trends, and improvement opportunities.
Provides insights for continuous learning and system optimization.
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FeedbackAnalytics:
    """
    Advanced analytics engine for feedback data analysis.
    Identifies patterns, trends, and improvement opportunities.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.feedback_file = self.project_path / "backend" / "feedback_data" / "feedback.json"
        self.analytics_file = self.project_path / "backend" / "feedback_data" / "analytics.json"
        
        # Load data
        self.feedback_data = self._load_feedback_data()
        self.analytics_data = self._load_analytics_data()

    def _load_feedback_data(self) -> List[Dict[str, Any]]:
        """Load feedback data from storage."""
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
        return {}

    def analyze_satisfaction_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze satisfaction trends over time."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent feedback with ratings
        recent_feedback = [
            f for f in self.feedback_data
            if datetime.fromisoformat(f["timestamp"]) >= cutoff_date and f.get("rating")
        ]
        
        if not recent_feedback:
            return {"message": "No satisfaction data available for the period"}
        
        # Group by day
        daily_ratings = defaultdict(list)
        for feedback in recent_feedback:
            date = datetime.fromisoformat(feedback["timestamp"]).date()
            daily_ratings[date].append(feedback["rating"])
        
        # Calculate daily averages
        daily_averages = {}
        for date, ratings in daily_ratings.items():
            daily_averages[str(date)] = {
                "average": round(sum(ratings) / len(ratings), 2),
                "count": len(ratings),
                "ratings": ratings
            }
        
        # Calculate overall statistics
        all_ratings = [f["rating"] for f in recent_feedback]
        overall_avg = round(sum(all_ratings) / len(all_ratings), 2)
        
        # Calculate trend
        sorted_dates = sorted(daily_averages.keys())
        if len(sorted_dates) >= 2:
            first_half = sorted_dates[:len(sorted_dates)//2]
            second_half = sorted_dates[len(sorted_dates)//2:]
            
            first_avg = np.mean([daily_averages[d]["average"] for d in first_half])
            second_avg = np.mean([daily_averages[d]["average"] for d in second_half])
            trend = "improving" if second_avg > first_avg else "declining" if second_avg < first_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "period_days": days,
            "overall_average": overall_avg,
            "total_ratings": len(all_ratings),
            "trend": trend,
            "daily_averages": daily_averages,
            "rating_distribution": dict(Counter(all_ratings))
        }

    def analyze_agent_performance(self) -> Dict[str, Any]:
        """Analyze performance of individual agents."""
        agent_stats = defaultdict(lambda: {
            "total_feedback": 0,
            "satisfaction_ratings": [],
            "failure_count": 0,
            "success_count": 0,
            "common_issues": Counter(),
            "response_times": [],
            "user_satisfaction": 0
        })
        
        for feedback in self.feedback_data:
            agent = feedback.get("agent_involved", "unknown")
            stats = agent_stats[agent]
            
            stats["total_feedback"] += 1
            
            # Track ratings
            if feedback.get("rating"):
                stats["satisfaction_ratings"].append(feedback["rating"])
            
            # Track failures vs successes
            if feedback["feedback_type"] == "failure_analysis":
                stats["failure_count"] += 1
                if feedback.get("step_failed"):
                    stats["common_issues"][feedback["step_failed"]] += 1
            else:
                stats["success_count"] += 1
            
            # Track response times if available
            if feedback.get("context", {}).get("response_time"):
                stats["response_times"].append(feedback["context"]["response_time"])
        
        # Calculate derived metrics
        agent_performance = {}
        for agent, stats in agent_stats.items():
            if stats["total_feedback"] == 0:
                continue
                
            avg_rating = np.mean(stats["satisfaction_ratings"]) if stats["satisfaction_ratings"] else 0
            success_rate = stats["success_count"] / stats["total_feedback"] if stats["total_feedback"] > 0 else 0
            avg_response_time = np.mean(stats["response_times"]) if stats["response_times"] else 0
            
            agent_performance[agent] = {
                "total_feedback": stats["total_feedback"],
                "average_rating": round(avg_rating, 2),
                "success_rate": round(success_rate, 2),
                "failure_rate": round(1 - success_rate, 2),
                "average_response_time": round(avg_response_time, 2),
                "common_issues": dict(stats["common_issues"].most_common(5)),
                "rating_distribution": dict(Counter(stats["satisfaction_ratings"])),
                "performance_score": self._calculate_performance_score(avg_rating, success_rate, stats["total_feedback"])
            }
        
        return agent_performance

    def _calculate_performance_score(self, avg_rating: float, success_rate: float, total_feedback: int) -> float:
        """Calculate a composite performance score for an agent."""
        # Weight factors
        rating_weight = 0.4
        success_weight = 0.4
        volume_weight = 0.2
        
        # Normalize rating (1-5 scale to 0-1)
        normalized_rating = (avg_rating - 1) / 4 if avg_rating > 0 else 0
        
        # Normalize volume (more feedback = more reliable score)
        volume_factor = min(total_feedback / 10, 1.0)  # Cap at 1.0 for 10+ feedback items
        
        # Calculate composite score
        score = (
            rating_weight * normalized_rating +
            success_weight * success_rate +
            volume_weight * volume_factor
        )
        
        return round(score, 2)

    def identify_improvement_areas(self) -> List[Dict[str, Any]]:
        """Identify specific areas that need improvement."""
        improvements = []
        
        # Analyze agent performance
        agent_performance = self.analyze_agent_performance()
        
        for agent, perf in agent_performance.items():
            # Low performance score
            if perf["performance_score"] < 0.6:
                improvements.append({
                    "type": "low_performance",
                    "priority": "high",
                    "agent": agent,
                    "description": f"Agent '{agent}' has low performance score ({perf['performance_score']})",
                    "metrics": {
                        "average_rating": perf["average_rating"],
                        "success_rate": perf["success_rate"],
                        "total_feedback": perf["total_feedback"]
                    },
                    "recommendations": [
                        "Review agent implementation for bugs",
                        "Improve error handling and user guidance",
                        "Add more comprehensive testing",
                        "Consider user experience improvements"
                    ]
                })
            
            # High failure rate
            if perf["failure_rate"] > 0.3:
                improvements.append({
                    "type": "high_failure_rate",
                    "priority": "high",
                    "agent": agent,
                    "description": f"Agent '{agent}' has high failure rate ({perf['failure_rate']:.2%})",
                    "common_issues": perf["common_issues"],
                    "recommendations": [
                        "Investigate common failure points",
                        "Improve error handling for identified issues",
                        "Add better user guidance for problematic steps",
                        "Implement fallback mechanisms"
                    ]
                })
            
            # Low satisfaction ratings
            if perf["average_rating"] < 3.0 and perf["total_feedback"] > 2:
                improvements.append({
                    "type": "low_satisfaction",
                    "priority": "medium",
                    "agent": agent,
                    "description": f"Agent '{agent}' has low user satisfaction ({perf['average_rating']})",
                    "rating_distribution": perf["rating_distribution"],
                    "recommendations": [
                        "Improve user interface and experience",
                        "Add more helpful error messages",
                        "Provide better guidance and instructions",
                        "Consider user feedback for specific improvements"
                    ]
                })
        
        # Analyze common issues across all agents
        all_issues = Counter()
        for feedback in self.feedback_data:
            if feedback.get("step_failed"):
                all_issues[feedback["step_failed"]] += 1
        
        for issue, count in all_issues.most_common(5):
            if count > 2:  # Only include issues that occur frequently
                improvements.append({
                    "type": "common_issue",
                    "priority": "medium",
                    "description": f"Step '{issue}' fails frequently ({count} times)",
                    "frequency": count,
                    "recommendations": [
                        f"Review and improve handling of '{issue}' step",
                        "Add better error messages and recovery options",
                        "Consider breaking down complex steps",
                        "Implement better validation and user guidance"
                    ]
                })
        
        return improvements

    def generate_learning_insights(self) -> Dict[str, Any]:
        """Generate insights for continuous learning and improvement."""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "data_period": "last_30_days",
            "total_feedback": len(self.feedback_data),
            "insights": []
        }
        
        # Satisfaction trends
        satisfaction_trends = self.analyze_satisfaction_trends()
        if "overall_average" in satisfaction_trends:
            insights["insights"].append({
                "type": "satisfaction_summary",
                "overall_rating": satisfaction_trends["overall_average"],
                "trend": satisfaction_trends["trend"],
                "total_ratings": satisfaction_trends["total_ratings"]
            })
        
        # Agent performance
        agent_performance = self.analyze_agent_performance()
        best_agent = max(agent_performance.items(), key=lambda x: x[1]["performance_score"]) if agent_performance else None
        worst_agent = min(agent_performance.items(), key=lambda x: x[1]["performance_score"]) if agent_performance else None
        
        if best_agent:
            insights["insights"].append({
                "type": "best_performing_agent",
                "agent": best_agent[0],
                "performance_score": best_agent[1]["performance_score"],
                "metrics": best_agent[1]
            })
        
        if worst_agent and worst_agent[1]["performance_score"] < 0.7:
            insights["insights"].append({
                "type": "needs_improvement_agent",
                "agent": worst_agent[0],
                "performance_score": worst_agent[1]["performance_score"],
                "metrics": worst_agent[1]
            })
        
        # Improvement areas
        improvements = self.identify_improvement_areas()
        high_priority = [imp for imp in improvements if imp["priority"] == "high"]
        medium_priority = [imp for imp in improvements if imp["priority"] == "medium"]
        
        insights["insights"].extend([
            {
                "type": "improvement_summary",
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority),
                "total_improvements": len(improvements)
            }
        ])
        
        # Learning recommendations
        learning_recommendations = self._generate_learning_recommendations(agent_performance, improvements)
        insights["learning_recommendations"] = learning_recommendations
        
        return insights

    def _generate_learning_recommendations(self, agent_performance: Dict, improvements: List[Dict]) -> List[Dict[str, Any]]:
        """Generate specific learning recommendations based on analysis."""
        recommendations = []
        
        # Model retraining recommendations
        for agent, perf in agent_performance.items():
            if perf["performance_score"] < 0.6:
                recommendations.append({
                    "type": "model_retraining",
                    "agent": agent,
                    "priority": "high",
                    "description": f"Retrain {agent} model due to low performance",
                    "rationale": f"Performance score: {perf['performance_score']}, Success rate: {perf['success_rate']}",
                    "suggested_actions": [
                        "Collect more training data from successful interactions",
                        "Fine-tune model on failure cases",
                        "Implement active learning for continuous improvement",
                        "Add more diverse training examples"
                    ]
                })
        
        # Knowledge base updates
        common_issues = [imp for imp in improvements if imp["type"] == "common_issue"]
        if common_issues:
            recommendations.append({
                "type": "knowledge_base_update",
                "priority": "medium",
                "description": "Update knowledge base with common failure patterns",
                "rationale": f"Identified {len(common_issues)} common issues that need better documentation",
                "suggested_actions": [
                    "Add FAQ entries for common failure scenarios",
                    "Improve error message clarity and helpfulness",
                    "Create troubleshooting guides for identified issues",
                    "Update agent prompts with better error handling"
                ]
            })
        
        # User experience improvements
        low_satisfaction = [imp for imp in improvements if imp["type"] == "low_satisfaction"]
        if low_satisfaction:
            recommendations.append({
                "type": "ux_improvement",
                "priority": "medium",
                "description": "Improve user experience based on feedback",
                "rationale": f"Found {len(low_satisfaction)} agents with low user satisfaction",
                "suggested_actions": [
                    "Conduct user interviews to understand pain points",
                    "Redesign user interfaces for better usability",
                    "Add progress indicators and better feedback",
                    "Implement user preference learning"
                ]
            })
        
        return recommendations

    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard visualization."""
        satisfaction_trends = self.analyze_satisfaction_trends()
        agent_performance = self.analyze_agent_performance()
        improvements = self.identify_improvement_areas()
        
        return {
            "satisfaction": {
                "overall_average": satisfaction_trends.get("overall_average", 0),
                "trend": satisfaction_trends.get("trend", "unknown"),
                "daily_data": satisfaction_trends.get("daily_averages", {}),
                "rating_distribution": satisfaction_trends.get("rating_distribution", {})
            },
            "agent_performance": agent_performance,
            "improvements": {
                "total": len(improvements),
                "high_priority": len([imp for imp in improvements if imp["priority"] == "high"]),
                "medium_priority": len([imp for imp in improvements if imp["priority"] == "medium"]),
                "by_type": dict(Counter([imp["type"] for imp in improvements]))
            },
            "summary": {
                "total_feedback": len(self.feedback_data),
                "active_agents": len(agent_performance),
                "avg_performance": np.mean([perf["performance_score"] for perf in agent_performance.values()]) if agent_performance else 0
            }
        }
