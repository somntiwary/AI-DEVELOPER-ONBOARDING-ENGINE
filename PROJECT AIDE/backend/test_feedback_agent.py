"""
Test Suite for Feedback & Continuous Learning Agent
==================================================
Comprehensive tests for feedback collection, analytics, and model retraining.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import feedback agent modules
try:
    from backend.agents.feedback import (
        FeedbackCollector, FeedbackAnalytics, ModelRetrainer,
        FeedbackType, FeedbackSeverity, UserFeedback
    )
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.feedback import (
        FeedbackCollector, FeedbackAnalytics, ModelRetrainer,
        FeedbackType, FeedbackSeverity, UserFeedback
    )

class TestFeedbackCollector(unittest.TestCase):
    """Test cases for FeedbackCollector."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.collector = FeedbackCollector(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_collect_feedback_basic(self):
        """Test basic feedback collection."""
        feedback_id = self.collector.collect_feedback(
            user_id="test_user",
            session_id="test_session",
            feedback_type=FeedbackType.SATISFACTION,
            description="Great onboarding experience!",
            rating=5,
            title="Positive Feedback"
        )
        
        self.assertIsNotNone(feedback_id)
        self.assertEqual(len(self.collector.feedback_data), 1)
        
        feedback = self.collector.feedback_data[0]
        self.assertEqual(feedback["user_id"], "test_user")
        self.assertEqual(feedback["rating"], 5)
        self.assertEqual(feedback["feedback_type"], "satisfaction")
    
    def test_collect_satisfaction_survey(self):
        """Test satisfaction survey collection."""
        feedback_id = self.collector.collect_satisfaction_survey(
            user_id="test_user",
            session_id="test_session",
            overall_rating=4,
            onboarding_time_minutes=15,
            agents_used=["repo_analysis", "environment_setup"],
            most_helpful_agent="repo_analysis",
            would_recommend=True
        )
        
        self.assertIsNotNone(feedback_id)
        self.assertEqual(len(self.collector.feedback_data), 1)
        
        feedback = self.collector.feedback_data[0]
        self.assertEqual(feedback["rating"], 4)
        self.assertEqual(feedback["context"]["onboarding_time_minutes"], 15)
        self.assertEqual(feedback["context"]["agents_used"], ["repo_analysis", "environment_setup"])
    
    def test_collect_failure_analysis(self):
        """Test failure analysis collection."""
        feedback_id = self.collector.collect_failure_analysis(
            user_id="test_user",
            session_id="test_session",
            agent_involved="repo_analysis",
            step_failed="code_parsing",
            error_message="Failed to parse Python file",
            user_actions=["opened_file", "ran_analysis"],
            suggested_fix="Check file encoding"
        )
        
        self.assertIsNotNone(feedback_id)
        self.assertEqual(len(self.collector.feedback_data), 1)
        
        feedback = self.collector.feedback_data[0]
        self.assertEqual(feedback["feedback_type"], "failure_analysis")
        self.assertEqual(feedback["agent_involved"], "repo_analysis")
        self.assertEqual(feedback["step_failed"], "code_parsing")
    
    def test_feedback_validation(self):
        """Test feedback validation."""
        # Test invalid rating
        with self.assertRaises(ValueError):
            self.collector.collect_feedback(
                user_id="test_user",
                session_id="test_session",
                feedback_type=FeedbackType.SATISFACTION,
                description="Test",
                rating=6  # Invalid rating
            )
    
    def test_get_feedback_summary(self):
        """Test feedback summary generation."""
        # Add some test feedback
        self.collector.collect_feedback(
            user_id="user1",
            session_id="session1",
            feedback_type=FeedbackType.SATISFACTION,
            description="Good experience",
            rating=4
        )
        
        self.collector.collect_feedback(
            user_id="user2",
            session_id="session2",
            feedback_type=FeedbackType.SATISFACTION,
            description="Excellent experience",
            rating=5
        )
        
        summary = self.collector.get_feedback_summary(days=30)
        
        self.assertEqual(summary["total_feedback"], 2)
        self.assertEqual(summary["average_rating"], 4.5)
        self.assertIn("satisfaction", summary["feedback_by_type"])

class TestFeedbackAnalytics(unittest.TestCase):
    """Test cases for FeedbackAnalytics."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.analytics = FeedbackAnalytics(self.temp_dir)
        
        # Add test feedback data
        self._add_test_feedback()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _add_test_feedback(self):
        """Add test feedback data."""
        test_feedback = [
            {
                "feedback_id": "1",
                "user_id": "user1",
                "session_id": "session1",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "feedback_type": "satisfaction",
                "rating": 4,
                "agent_involved": "repo_analysis",
                "description": "Good experience"
            },
            {
                "feedback_id": "2",
                "user_id": "user2",
                "session_id": "session2",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "feedback_type": "satisfaction",
                "rating": 5,
                "agent_involved": "environment_setup",
                "description": "Excellent experience"
            },
            {
                "feedback_id": "3",
                "user_id": "user3",
                "session_id": "session3",
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "feedback_type": "failure_analysis",
                "rating": 2,
                "agent_involved": "repo_analysis",
                "step_failed": "code_parsing",
                "description": "Failed to parse code"
            }
        ]
        
        # Save test feedback
        feedback_file = Path(self.temp_dir) / "backend" / "feedback_data" / "feedback.json"
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(test_feedback, f, indent=2)
        
        # Reload analytics with test data
        self.analytics.feedback_data = test_feedback
    
    def test_analyze_satisfaction_trends(self):
        """Test satisfaction trends analysis."""
        trends = self.analytics.analyze_satisfaction_trends(days=30)
        
        self.assertIn("overall_average", trends)
        self.assertIn("trend", trends)
        self.assertIn("daily_averages", trends)
        self.assertEqual(trends["total_ratings"], 3)
    
    def test_analyze_agent_performance(self):
        """Test agent performance analysis."""
        performance = self.analytics.analyze_agent_performance()
        
        self.assertIn("repo_analysis", performance)
        self.assertIn("environment_setup", performance)
        
        # Check performance metrics
        repo_perf = performance["repo_analysis"]
        self.assertIn("total_feedback", repo_perf)
        self.assertIn("average_rating", repo_perf)
        self.assertIn("success_rate", repo_perf)
        self.assertIn("performance_score", repo_perf)
    
    def test_identify_improvement_areas(self):
        """Test improvement areas identification."""
        improvements = self.analytics.identify_improvement_areas()
        
        self.assertIsInstance(improvements, list)
        # Should identify repo_analysis as needing improvement due to failure
        improvement_agents = [imp["agent"] for imp in improvements if "agent" in imp]
        self.assertIn("repo_analysis", improvement_agents)
    
    def test_generate_learning_insights(self):
        """Test learning insights generation."""
        insights = self.analytics.generate_learning_insights()
        
        self.assertIn("timestamp", insights)
        self.assertIn("total_feedback", insights)
        self.assertIn("insights", insights)
        self.assertIn("learning_recommendations", insights)
    
    def test_get_performance_dashboard_data(self):
        """Test performance dashboard data generation."""
        dashboard_data = self.analytics.get_performance_dashboard_data()
        
        self.assertIn("satisfaction", dashboard_data)
        self.assertIn("agent_performance", dashboard_data)
        self.assertIn("improvements", dashboard_data)
        self.assertIn("summary", dashboard_data)

class TestModelRetrainer(unittest.TestCase):
    """Test cases for ModelRetrainer."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.retrainer = ModelRetrainer(self.temp_dir)
        
        # Add test training data
        self._add_test_training_data()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _add_test_training_data(self):
        """Add test training data."""
        test_data = [
            {
                "feedback_id": "1",
                "user_id": "user1",
                "session_id": "session1",
                "timestamp": datetime.now().isoformat(),
                "feedback_type": "satisfaction",
                "rating": 4,
                "agent_involved": "repo_analysis",
                "description": "Good code analysis",
                "context": {"response_time": 1.5}
            },
            {
                "feedback_id": "2",
                "user_id": "user2",
                "session_id": "session2",
                "timestamp": datetime.now().isoformat(),
                "feedback_type": "failure_analysis",
                "rating": 2,
                "agent_involved": "repo_analysis",
                "step_failed": "parsing",
                "description": "Failed to parse code",
                "suggested_fix": "Check file encoding"
            }
        ]
        
        # Save test data
        training_file = Path(self.temp_dir) / "backend" / "feedback_data" / "feedback.json"
        training_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(training_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Reload retrainer with test data
        self.retrainer.training_data = test_data
    
    def test_prepare_retraining_data(self):
        """Test retraining data preparation."""
        retraining_data = self.retrainer.prepare_retraining_data("repo_analysis", days=30)
        
        self.assertIn("status", retraining_data)
        if retraining_data["status"] == "ready":
            self.assertIn("training_samples", retraining_data)
            self.assertIn("validation_samples", retraining_data)
            self.assertIn("data_quality", retraining_data)
    
    def test_extract_training_data_from_feedback(self):
        """Test training data extraction from feedback."""
        training_samples = self.retrainer.extract_training_data_from_feedback(self.retrainer.training_data)
        
        self.assertIsInstance(training_samples, list)
        if training_samples:
            sample = training_samples[0]
            self.assertIn("input_text", sample.__dict__)
            self.assertIn("expected_output", sample.__dict__)
            self.assertIn("success", sample.__dict__)
    
    def test_assess_data_quality(self):
        """Test data quality assessment."""
        training_samples = self.retrainer.extract_training_data_from_feedback(self.retrainer.training_data)
        quality = self.retrainer._assess_data_quality(training_samples)
        
        self.assertIn("quality_score", quality)
        self.assertIn("issues", quality)
        self.assertIn("success_rate", quality)
        self.assertGreaterEqual(quality["quality_score"], 0)
        self.assertLessEqual(quality["quality_score"], 1)
    
    def test_schedule_retraining(self):
        """Test retraining scheduling."""
        result = self.retrainer.schedule_retraining("repo_analysis")
        
        self.assertIn("status", result)
        # Status could be "not_needed", "insufficient_data", "poor_data_quality", or success
        self.assertIn(result["status"], ["not_needed", "insufficient_data", "poor_data_quality", "success"])
    
    def test_get_retraining_status(self):
        """Test retraining status retrieval."""
        status = self.retrainer.get_retraining_status()
        
        self.assertIn("timestamp", status)
        self.assertIn("agents", status)
        self.assertIn("overall_status", status)
        
        # Check that all expected agents are present
        expected_agents = ["repo_analysis", "environment_setup", "documentation", "qna_agent", "walkthrough", "ci_cd_agent"]
        for agent in expected_agents:
            self.assertIn(agent, status["agents"])
    
    def test_update_knowledge_base(self):
        """Test knowledge base updates."""
        updates = self.retrainer.update_knowledge_base(self.retrainer.training_data)
        
        self.assertIn("timestamp", updates)
        self.assertIn("total_updates", updates)
        self.assertIn("updates", updates)
        self.assertIsInstance(updates["updates"], list)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete feedback system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_feedback_flow(self):
        """Test complete feedback collection and analysis flow."""
        # Initialize components
        collector = FeedbackCollector(self.temp_dir)
        analytics = FeedbackAnalytics(self.temp_dir)
        retrainer = ModelRetrainer(self.temp_dir)
        
        # Collect feedback
        feedback_id = collector.collect_satisfaction_survey(
            user_id="test_user",
            session_id="test_session",
            overall_rating=4,
            onboarding_time_minutes=20,
            agents_used=["repo_analysis", "environment_setup"],
            most_helpful_agent="repo_analysis"
        )
        
        self.assertIsNotNone(feedback_id)
        
        # Analyze feedback
        trends = analytics.analyze_satisfaction_trends()
        # The analytics might not have data yet, so check for either success or no data message
        self.assertTrue("overall_average" in trends or "message" in trends)
        
        performance = analytics.analyze_agent_performance()
        self.assertIsInstance(performance, dict)
        
        # Check retraining status
        status = retrainer.get_retraining_status()
        self.assertIn("overall_status", status)
        
        print("PASS End-to-end feedback flow test passed")
    
    def test_feedback_persistence(self):
        """Test that feedback data persists across instances."""
        # Create first collector instance
        collector1 = FeedbackCollector(self.temp_dir)
        feedback_id = collector1.collect_feedback(
            user_id="test_user",
            session_id="test_session",
            feedback_type=FeedbackType.SATISFACTION,
            description="Test feedback",
            rating=4
        )
        
        # Create second collector instance (should load existing data)
        collector2 = FeedbackCollector(self.temp_dir)
        
        # Check that data was persisted
        self.assertEqual(len(collector2.feedback_data), 1)
        self.assertEqual(collector2.feedback_data[0]["feedback_id"], feedback_id)
        
        print("PASS Feedback persistence test passed")

def run_tests():
    """Run all feedback agent tests."""
    print("Testing Feedback & Continuous Learning Agent")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestFeedbackCollector))
    test_suite.addTest(unittest.makeSuite(TestFeedbackAnalytics))
    test_suite.addTest(unittest.makeSuite(TestModelRetrainer))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    run_tests()
