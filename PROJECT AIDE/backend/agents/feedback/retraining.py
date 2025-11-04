"""
Model Retraining Engine
=======================
Handles continuous learning through model retraining and fine-tuning.
Updates models based on feedback data and performance metrics.
"""

import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class TrainingData:
    """Structured training data for model retraining."""
    input_text: str
    expected_output: str
    context: Dict[str, Any]
    success: bool
    user_rating: Optional[int] = None
    feedback_type: str = "general"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ModelRetrainer:
    """
    Handles continuous learning through model retraining and fine-tuning.
    Updates models based on feedback data and performance metrics.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.models_dir = self.project_path / "backend" / "feedback_data" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize retraining configuration
        self.retraining_config = {
            "min_feedback_threshold": 10,
            "performance_threshold": 0.6,
            "retraining_frequency_days": 7,
            "max_training_samples": 1000,
            "validation_split": 0.2
        }
        
        # Load existing training data
        self.training_data_file = self.models_dir / "training_data.json"
        self.training_data = self._load_training_data()
        
        # Load model metadata
        self.model_metadata_file = self.models_dir / "model_metadata.json"
        self.model_metadata = self._load_model_metadata()

    def _load_training_data(self) -> List[Dict[str, Any]]:
        """Load existing training data."""
        if self.training_data_file.exists():
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load training data: {e}")
        return []

    def _load_model_metadata(self) -> Dict[str, Any]:
        """Load model metadata."""
        if self.model_metadata_file.exists():
            try:
                with open(self.model_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load model metadata: {e}")
        return {}

    def _save_training_data(self):
        """Save training data to storage."""
        try:
            with open(self.training_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save training data: {e}")

    def _save_model_metadata(self):
        """Save model metadata."""
        try:
            with open(self.model_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")

    def extract_training_data_from_feedback(self, feedback_data: List[Dict[str, Any]]) -> List[TrainingData]:
        """Extract training data from feedback for model retraining."""
        training_samples = []
        
        for feedback in feedback_data:
            # Skip if no useful training data
            if not feedback.get("description") or not feedback.get("context"):
                continue
            
            # Extract input and expected output
            input_text = self._extract_input_text(feedback)
            expected_output = self._extract_expected_output(feedback)
            
            if not input_text or not expected_output:
                continue
            
            # Determine success based on feedback type and rating
            success = self._determine_success(feedback)
            user_rating = feedback.get("rating")
            
            training_sample = TrainingData(
                input_text=input_text,
                expected_output=expected_output,
                context=feedback.get("context", {}),
                success=success,
                user_rating=user_rating,
                feedback_type=feedback.get("feedback_type", "general"),
                timestamp=datetime.fromisoformat(feedback["timestamp"])
            )
            
            training_samples.append(training_sample)
        
        return training_samples

    def _extract_input_text(self, feedback: Dict[str, Any]) -> Optional[str]:
        """Extract input text from feedback for training."""
        # Combine relevant context for input
        input_parts = []
        
        # Add user query or description
        if feedback.get("description"):
            input_parts.append(f"User: {feedback['description']}")
        
        # Add context about the step or agent
        if feedback.get("step_failed"):
            input_parts.append(f"Step: {feedback['step_failed']}")
        
        if feedback.get("agent_involved"):
            input_parts.append(f"Agent: {feedback['agent_involved']}")
        
        # Add user experience context
        if feedback.get("user_experience"):
            input_parts.append(f"Context: {feedback['user_experience']}")
        
        return " | ".join(input_parts) if input_parts else None

    def _extract_expected_output(self, feedback: Dict[str, Any]) -> Optional[str]:
        """Extract expected output from feedback for training."""
        # Use suggested fix if available
        if feedback.get("suggested_fix"):
            return feedback["suggested_fix"]
        
        # Generate expected output based on feedback type
        feedback_type = feedback.get("feedback_type", "general")
        
        if feedback_type == "failure_analysis":
            return f"Successfully handle the {feedback.get('step_failed', 'requested')} step"
        elif feedback_type == "improvement_suggestion":
            return "Implement the suggested improvement"
        elif feedback_type == "satisfaction":
            return "Provide a satisfactory user experience"
        else:
            return "Provide helpful assistance"

    def _determine_success(self, feedback: Dict[str, Any]) -> bool:
        """Determine if the interaction was successful based on feedback."""
        feedback_type = feedback.get("feedback_type", "general")
        rating = feedback.get("rating")
        
        # High rating indicates success
        if rating and rating >= 4:
            return True
        
        # Low rating indicates failure
        if rating and rating <= 2:
            return False
        
        # Use feedback type as indicator
        if feedback_type == "success_story":
            return True
        elif feedback_type == "failure_analysis":
            return False
        
        # Default to neutral
        return True

    def prepare_retraining_data(self, agent_name: str, days: int = 30) -> Dict[str, Any]:
        """Prepare retraining data for a specific agent."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter feedback for the specific agent
        agent_feedback = [
            f for f in self.training_data
            if f.get("agent_involved") == agent_name and
            datetime.fromisoformat(f["timestamp"]) >= cutoff_date
        ]
        
        if len(agent_feedback) < self.retraining_config["min_feedback_threshold"]:
            return {
                "status": "insufficient_data",
                "message": f"Not enough feedback data for {agent_name} (need {self.retraining_config['min_feedback_threshold']}, have {len(agent_feedback)})",
                "feedback_count": len(agent_feedback)
            }
        
        # Extract training samples
        training_samples = self.extract_training_data_from_feedback(agent_feedback)
        
        if not training_samples:
            return {
                "status": "no_training_data",
                "message": f"No usable training data extracted for {agent_name}",
                "feedback_count": len(agent_feedback)
            }
        
        # Split into training and validation sets
        np.random.seed(42)  # For reproducibility
        indices = np.random.permutation(len(training_samples))
        split_idx = int(len(training_samples) * (1 - self.retraining_config["validation_split"]))
        
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]
        
        train_samples = [training_samples[i] for i in train_indices]
        val_samples = [training_samples[i] for i in val_indices]
        
        # Limit training samples if too many
        if len(train_samples) > self.retraining_config["max_training_samples"]:
            train_samples = train_samples[:self.retraining_config["max_training_samples"]]
        
        return {
            "status": "ready",
            "agent": agent_name,
            "total_feedback": len(agent_feedback),
            "training_samples": len(train_samples),
            "validation_samples": len(val_samples),
            "training_data": [asdict(sample) for sample in train_samples],
            "validation_data": [asdict(sample) for sample in val_samples],
            "data_quality": self._assess_data_quality(training_samples)
        }

    def _assess_data_quality(self, training_samples: List[TrainingData]) -> Dict[str, Any]:
        """Assess the quality of training data."""
        if not training_samples:
            return {"quality_score": 0, "issues": ["No training data available"]}
        
        issues = []
        quality_score = 1.0
        
        # Check success/failure balance
        success_count = sum(1 for sample in training_samples if sample.success)
        failure_count = len(training_samples) - success_count
        
        if success_count == 0 or failure_count == 0:
            issues.append("Unbalanced success/failure data")
            quality_score -= 0.3
        elif abs(success_count - failure_count) / len(training_samples) > 0.8:
            issues.append("Highly imbalanced success/failure data")
            quality_score -= 0.2
        
        # Check rating distribution
        rated_samples = [s for s in training_samples if s.user_rating is not None]
        if rated_samples:
            avg_rating = np.mean([s.user_rating for s in rated_samples])
            if avg_rating < 2.0:
                issues.append("Low average user ratings")
                quality_score -= 0.2
            elif avg_rating > 4.5:
                issues.append("Suspiciously high average ratings")
                quality_score -= 0.1
        
        # Check data diversity
        unique_inputs = len(set(sample.input_text for sample in training_samples))
        if unique_inputs / len(training_samples) < 0.5:
            issues.append("Low input diversity")
            quality_score -= 0.1
        
        # Check recency
        recent_samples = [
            s for s in training_samples
            if (datetime.now() - s.timestamp).days <= 7
        ]
        if len(recent_samples) / len(training_samples) < 0.3:
            issues.append("Limited recent data")
            quality_score -= 0.1
        
        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "success_rate": success_count / len(training_samples),
            "avg_rating": np.mean([s.user_rating for s in rated_samples]) if rated_samples else None,
            "diversity_ratio": unique_inputs / len(training_samples),
            "recent_data_ratio": len(recent_samples) / len(training_samples)
        }

    def retrain_agent_model(self, agent_name: str, retraining_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrain a specific agent's model with new data."""
        if retraining_data["status"] != "ready":
            return {
                "status": "failed",
                "message": f"Cannot retrain {agent_name}: {retraining_data['message']}"
            }
        
        try:
            # Generate model version
            model_version = self._generate_model_version(agent_name)
            
            # Simulate model retraining (replace with actual implementation)
            retraining_result = self._simulate_model_retraining(
                agent_name, 
                retraining_data["training_data"],
                retraining_data["validation_data"]
            )
            
            # Update model metadata
            self.model_metadata[agent_name] = {
                "version": model_version,
                "last_retrained": datetime.now().isoformat(),
                "training_samples": retraining_data["training_samples"],
                "validation_samples": retraining_data["validation_samples"],
                "data_quality": retraining_data["data_quality"],
                "performance_metrics": retraining_result["metrics"],
                "model_path": f"models/{agent_name}_{model_version}.pkl"
            }
            
            self._save_model_metadata()
            
            logger.info(f"Successfully retrained model for {agent_name} (version {model_version})")
            
            return {
                "status": "success",
                "agent": agent_name,
                "model_version": model_version,
                "training_samples": retraining_data["training_samples"],
                "performance_metrics": retraining_result["metrics"],
                "data_quality": retraining_data["data_quality"]
            }
            
        except Exception as e:
            logger.error(f"Failed to retrain model for {agent_name}: {e}")
            return {
                "status": "failed",
                "message": f"Retraining failed: {str(e)}"
            }

    def _generate_model_version(self, agent_name: str) -> str:
        """Generate a new version identifier for the model."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{agent_name}_{timestamp}"

    def _simulate_model_retraining(self, agent_name: str, training_data: List[Dict], validation_data: List[Dict]) -> Dict[str, Any]:
        """Simulate model retraining (replace with actual implementation)."""
        # This is a placeholder - replace with actual model retraining logic
        # For example, fine-tuning a language model or updating a classifier
        
        # Calculate basic metrics
        training_size = len(training_data)
        validation_size = len(validation_data)
        
        # Simulate performance improvement
        base_accuracy = 0.7
        improvement = min(0.2, training_size / 100)  # Up to 20% improvement based on data size
        new_accuracy = base_accuracy + improvement
        
        return {
            "metrics": {
                "training_accuracy": new_accuracy,
                "validation_accuracy": new_accuracy - 0.05,  # Slightly lower validation accuracy
                "training_loss": 0.3 - (improvement * 0.5),
                "validation_loss": 0.35 - (improvement * 0.5),
                "improvement": improvement
            },
            "training_time_seconds": training_size * 0.1,  # Simulate training time
            "model_size_mb": training_size * 0.01  # Simulate model size
        }

    def schedule_retraining(self, agent_name: str) -> Dict[str, Any]:
        """Schedule retraining for an agent based on performance and data availability."""
        # Check if retraining is needed
        last_retrained = self.model_metadata.get(agent_name, {}).get("last_retrained")
        if last_retrained:
            last_retrained_date = datetime.fromisoformat(last_retrained)
            days_since_retraining = (datetime.now() - last_retrained_date).days
            if days_since_retraining < self.retraining_config["retraining_frequency_days"]:
                return {
                    "status": "not_needed",
                    "message": f"Retraining not needed for {agent_name} (last retrained {days_since_retraining} days ago)"
                }
        
        # Prepare retraining data
        retraining_data = self.prepare_retraining_data(agent_name)
        
        if retraining_data["status"] != "ready":
            return retraining_data
        
        # Check data quality
        quality_score = retraining_data["data_quality"]["quality_score"]
        if quality_score < 0.5:
            return {
                "status": "poor_data_quality",
                "message": f"Data quality too low for {agent_name} (score: {quality_score:.2f})",
                "data_quality": retraining_data["data_quality"]
            }
        
        # Proceed with retraining
        return self.retrain_agent_model(agent_name, retraining_data)

    def get_retraining_status(self) -> Dict[str, Any]:
        """Get status of all agents' retraining needs."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "overall_status": "healthy"
        }
        
        # Check each agent
        for agent_name in ["repo_analysis", "environment_setup", "documentation", "qna_agent", "walkthrough", "ci_cd_agent"]:
            agent_status = self._check_agent_retraining_status(agent_name)
            status["agents"][agent_name] = agent_status
        
        # Determine overall status
        needs_retraining = [agent for agent, data in status["agents"].items() if data["needs_retraining"]]
        if needs_retraining:
            status["overall_status"] = "needs_attention"
            status["agents_needing_retraining"] = needs_retraining
        
        return status

    def _check_agent_retraining_status(self, agent_name: str) -> Dict[str, Any]:
        """Check if an agent needs retraining."""
        # Check last retraining date
        last_retrained = self.model_metadata.get(agent_name, {}).get("last_retrained")
        days_since_retraining = None
        if last_retrained:
            days_since_retraining = (datetime.now() - datetime.fromisoformat(last_retrained)).days
        
        # Check data availability
        retraining_data = self.prepare_retraining_data(agent_name, days=30)
        
        needs_retraining = False
        reason = None
        
        if retraining_data["status"] == "ready":
            if days_since_retraining is None or days_since_retraining >= self.retraining_config["retraining_frequency_days"]:
                needs_retraining = True
                reason = "Scheduled retraining due"
        elif retraining_data["status"] == "insufficient_data":
            reason = "Insufficient feedback data"
        elif retraining_data["status"] == "no_training_data":
            reason = "No usable training data"
        
        return {
            "needs_retraining": needs_retraining,
            "reason": reason,
            "last_retrained": last_retrained,
            "days_since_retraining": days_since_retraining,
            "available_data": retraining_data.get("total_feedback", 0),
            "data_quality": retraining_data.get("data_quality", {}).get("quality_score", 0)
        }

    def update_knowledge_base(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update knowledge base based on feedback patterns."""
        # Extract common patterns and insights
        patterns = self._extract_knowledge_patterns(feedback_data)
        
        # Generate knowledge base updates
        updates = []
        
        # Add common failure patterns
        for pattern in patterns.get("common_failures", []):
            updates.append({
                "type": "failure_pattern",
                "pattern": pattern["pattern"],
                "frequency": pattern["frequency"],
                "suggested_solution": pattern["suggested_solution"],
                "context": pattern["context"]
            })
        
        # Add successful interaction patterns
        for pattern in patterns.get("success_patterns", []):
            updates.append({
                "type": "success_pattern",
                "pattern": pattern["pattern"],
                "frequency": pattern["frequency"],
                "best_practices": pattern["best_practices"],
                "context": pattern["context"]
            })
        
        # Add user preference patterns
        for pattern in patterns.get("user_preferences", []):
            updates.append({
                "type": "user_preference",
                "preference": pattern["preference"],
                "frequency": pattern["frequency"],
                "context": pattern["context"]
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_updates": len(updates),
            "updates": updates,
            "patterns_analyzed": len(feedback_data)
        }

    def _extract_knowledge_patterns(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract knowledge patterns from feedback data."""
        patterns = {
            "common_failures": [],
            "success_patterns": [],
            "user_preferences": []
        }
        
        # Analyze failure patterns
        failure_feedback = [f for f in feedback_data if f.get("feedback_type") == "failure_analysis"]
        if failure_feedback:
            # Group by common failure points
            failure_points = {}
            for feedback in failure_feedback:
                step = feedback.get("step_failed", "unknown")
                if step not in failure_points:
                    failure_points[step] = []
                failure_points[step].append(feedback)
            
            for step, failures in failure_points.items():
                if len(failures) >= 2:  # Only include patterns that occur multiple times
                    patterns["common_failures"].append({
                        "pattern": f"Failure at step: {step}",
                        "frequency": len(failures),
                        "suggested_solution": self._generate_solution_suggestion(failures),
                        "context": {"step": step, "agent": failures[0].get("agent_involved")}
                    })
        
        # Analyze success patterns
        success_feedback = [f for f in feedback_data if f.get("rating", 0) >= 4]
        if success_feedback:
            # Group by agent
            agent_successes = {}
            for feedback in success_feedback:
                agent = feedback.get("agent_involved", "unknown")
                if agent not in agent_successes:
                    agent_successes[agent] = []
                agent_successes[agent].append(feedback)
            
            for agent, successes in agent_successes.items():
                if len(successes) >= 3:  # Only include patterns with multiple successes
                    patterns["success_patterns"].append({
                        "pattern": f"Successful interactions with {agent}",
                        "frequency": len(successes),
                        "best_practices": self._extract_best_practices(successes),
                        "context": {"agent": agent}
                    })
        
        return patterns

    def _generate_solution_suggestion(self, failures: List[Dict[str, Any]]) -> str:
        """Generate solution suggestions based on failure patterns."""
        # Analyze common themes in failure descriptions
        descriptions = [f.get("description", "") for f in failures]
        suggested_fixes = [f.get("suggested_fix", "") for f in failures if f.get("suggested_fix")]
        
        if suggested_fixes:
            return f"Consider implementing user suggestions: {'; '.join(suggested_fixes[:3])}"
        else:
            return "Review error handling and user guidance for this step"

    def _extract_best_practices(self, successes: List[Dict[str, Any]]) -> List[str]:
        """Extract best practices from successful interactions."""
        practices = []
        
        # Look for common positive themes
        positive_themes = []
        for success in successes:
            description = success.get("description", "").lower()
            if "helpful" in description:
                positive_themes.append("Provide helpful guidance")
            if "clear" in description:
                positive_themes.append("Use clear instructions")
            if "fast" in description or "quick" in description:
                positive_themes.append("Ensure fast response times")
        
        # Return most common themes
        from collections import Counter
        theme_counts = Counter(positive_themes)
        return [theme for theme, count in theme_counts.most_common(3)]
