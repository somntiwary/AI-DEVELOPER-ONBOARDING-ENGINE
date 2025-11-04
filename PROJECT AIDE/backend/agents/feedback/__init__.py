"""
Feedback & Continuous Learning Agent
===================================
Enables AIDE to continuously learn, improve, and adapt from real-world interactions,
errors, and user feedback — making it more efficient and human-like over time.

Core Components:
- FeedbackCollector: Collects and manages user feedback
- FeedbackAnalytics: Analyzes feedback patterns and trends
- ModelRetrainer: Handles continuous learning through model retraining
"""

from .feedback_collector import FeedbackCollector, UserFeedback, FeedbackType, FeedbackSeverity
from .analytics import FeedbackAnalytics
from .retraining import ModelRetrainer, TrainingData

__all__ = [
    'FeedbackCollector',
    'UserFeedback', 
    'FeedbackType',
    'FeedbackSeverity',
    'FeedbackAnalytics',
    'ModelRetrainer',
    'TrainingData'
]
