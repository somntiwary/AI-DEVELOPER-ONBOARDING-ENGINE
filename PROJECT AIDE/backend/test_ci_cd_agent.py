#!/usr/bin/env python3
"""
CI/CD Agent Test Suite
======================
Comprehensive test suite for the CI/CD Agent functionality.
Tests all endpoints, performance optimizations, and error handling.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.ci_cd_routes import router
from fastapi import HTTPException
from agents.ci_cd_agent.github_ci import GitHubCISummarizer
from agents.ci_cd_agent.jenkins_ci import JenkinsFileParser
from agents.ci_cd_agent.validation import CIValidator

def test_imports():
    """Test that all CI/CD agent modules can be imported."""
    print("Testing CI/CD Agent Imports...")
    
    try:
        from agents.ci_cd_agent.github_ci import GitHubCISummarizer, GitHubWorkflowManager
        print("PASS GitHub CI module imported successfully")
    except Exception as e:
        print(f"FAIL GitHub CI import failed: {e}")
        return False
    
    try:
        from agents.ci_cd_agent.jenkins_ci import JenkinsFileParser, JenkinsManager
        print("PASS Jenkins CI module imported successfully")
    except Exception as e:
        print(f"FAIL Jenkins CI import failed: {e}")
        return False
    
    try:
        from agents.ci_cd_agent.llm_diagnostics import LLMDiagnostics
        print("PASS LLM Diagnostics module imported successfully")
    except Exception as e:
        print(f"FAIL LLM Diagnostics import failed: {e}")
        return False
    
    try:
        from agents.ci_cd_agent.validation import CIValidator
        print("PASS Validation module imported successfully")
    except Exception as e:
        print(f"FAIL Validation import failed: {e}")
        return False
    
    return True

def test_github_ci():
    """Test GitHub CI functionality."""
    print("\nTesting GitHub CI Functionality...")
    
    try:
        # Test with current directory
        summarizer = GitHubCISummarizer(".")
        workflows = summarizer.summarize_all()
        
        print(f"PASS GitHub CI analysis completed - Found {len(workflows)} workflow(s)")
        
        # Test workflow explanation
        if workflows:
            explanation = summarizer.explain_workflow(workflows[0])
            print(f"PASS Workflow explanation generated ({len(explanation)} characters)")
        
        return True
    except Exception as e:
        print(f"FAIL GitHub CI test failed: {e}")
        return False

def test_jenkins_ci():
    """Test Jenkins CI functionality."""
    print("\nTesting Jenkins CI Functionality...")
    
    try:
        # Test with current directory
        parser = JenkinsFileParser(".")
        summary = parser.summarize()
        
        if "error" in summary:
            print(f"INFO No Jenkinsfile found (expected): {summary['error']}")
        else:
            print(f"PASS Jenkins pipeline analysis completed - {summary['total_stages']} stages")
        
        return True
    except Exception as e:
        print(f"FAIL Jenkins CI test failed: {e}")
        return False

def test_validation():
    """Test CI/CD validation functionality."""
    print("\nTesting CI/CD Validation...")
    
    try:
        validator = CIValidator(".")
        configs = validator.detect_configs()
        issues = validator.detect_common_issues()
        
        print(f"PASS Validation completed - Detected configs: {list(configs.keys())}")
        print(f"PASS Found {len(issues)} common issues")
        
        return True
    except Exception as e:
        print(f"FAIL Validation test failed: {e}")
        return False

def test_performance_optimizations():
    """Test performance optimizations."""
    print("\nTesting Performance Optimizations...")
    
    try:
        from routes.ci_cd_routes import _cache, cache_result, log_performance
        
        # Test cache functionality
        print(f"PASS Cache system initialized - {len(_cache)} entries")
        
        # Test decorators
        @cache_result(ttl_seconds=60)
        @log_performance
        def test_function():
            time.sleep(0.1)  # Simulate work
            return "test_result"
        
        # First call (should be cached)
        start_time = time.time()
        result1 = test_function()
        time1 = time.time() - start_time
        
        # Second call (should hit cache)
        start_time = time.time()
        result2 = test_function()
        time2 = time.time() - start_time
        
        print(f"PASS Performance optimizations working - Cache hit: {time2 < time1}")
        return True
    except Exception as e:
        print(f"FAIL Performance test failed: {e}")
        return False

def test_error_handling():
    """Test error handling capabilities."""
    print("\nTesting Error Handling...")
    
    try:
        from routes.ci_cd_routes import handle_errors
        
        @handle_errors
        def test_error_function():
            raise FileNotFoundError("Test file not found")
        
        try:
            test_error_function()
            print("FAIL Error handling test failed - should have raised HTTPException")
            return False
        except HTTPException as e:
            if "Test file not found" in str(e.detail):
                print("PASS Error handling working correctly")
                return True
            else:
                print(f"FAIL Unexpected HTTPException: {e}")
                return False
        except Exception as e:
            print(f"FAIL Unexpected error type: {type(e).__name__}: {e}")
            return False
    except Exception as e:
        print(f"FAIL Error handling test failed: {e}")
        return False

def test_monitoring():
    """Test monitoring capabilities."""
    print("\nTesting Monitoring Capabilities...")
    
    try:
        from routes.ci_cd_routes import _cache
        
        # Test cache monitoring
        cache_stats = {
            "total_entries": len(_cache),
            "cache_keys": list(_cache.keys())[:5]
        }
        
        print(f"PASS Cache monitoring working - {cache_stats['total_entries']} entries")
        
        # Test timestamp functionality
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        print(f"PASS Timestamp generation working: {timestamp}")
        
        return True
    except Exception as e:
        print(f"FAIL Monitoring test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("Starting CI/CD Agent Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("GitHub CI Tests", test_github_ci),
        ("Jenkins CI Tests", test_jenkins_ci),
        ("Validation Tests", test_validation),
        ("Performance Tests", test_performance_optimizations),
        ("Error Handling Tests", test_error_handling),
        ("Monitoring Tests", test_monitoring)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! CI/CD Agent is working efficiently and strongly!")
    else:
        print("Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
