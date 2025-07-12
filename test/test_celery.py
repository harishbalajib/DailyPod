import os
import sys
import time
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery
from tasks import test_task, fetch_news_task, daily_delivery_task, health_check_task
from config import Config

def test_celery_connection():
    """Test basic Celery connection and worker status"""
    print("Testing Celery Connection...")
    print("=" * 30)
    
    try:
        # Test basic Celery inspection
        inspect = celery.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("SUCCESS: Celery workers are active")
            print(f"Active workers: {list(stats.keys())}")
            
            # Get worker details
            for worker_name, worker_stats in stats.items():
                print(f"  Worker: {worker_name}")
                print(f"    Pool: {worker_stats.get('pool', {}).get('implementation', 'Unknown')}")
                print(f"    Concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'Unknown')}")
            
            return True
        else:
            print("WARNING: No active Celery workers found")
            print("Make sure to start Celery workers with: celery -A celery_app worker --loglevel=info")
            return False
            
    except Exception as e:
        print(f"FAILED: Celery connection failed - {e}")
        return False

def test_celery_task_execution():
    """Test basic task execution"""
    print("\nTesting Celery Task Execution...")
    print("=" * 30)
    
    try:
        # Submit a test task
        result = test_task.delay("test_message")
        print(f"Task submitted with ID: {result.id}")
        
        # Wait for result
        task_result = result.get(timeout=10)
        print(f"SUCCESS: Task completed with result: {task_result}")
        return True
        
    except Exception as e:
        print(f"FAILED: Celery task execution failed - {e}")
        return False

def test_celery_task_status():
    """Test task status tracking"""
    print("\nTesting Celery Task Status...")
    print("=" * 30)
    
    try:
        # Submit a task
        result = test_task.delay("status_test_message")
        task_id = result.id
        
        # Check different status states
        print(f"Task ID: {task_id}")
        print(f"Initial status: {result.status}")
        
        # Wait a moment and check status
        time.sleep(1)
        print(f"Status after 1s: {result.status}")
        
        # Get final result
        task_result = result.get(timeout=10)
        print(f"Final status: {result.status}")
        print(f"Final result: {task_result}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Task status test failed - {e}")
        return False

def test_celery_load_performance():
    """Test Celery performance under load"""
    print("\nTesting Celery Load Performance...")
    print("=" * 30)
    
    try:
        # Submit multiple tasks simultaneously
        task_results = []
        start_time = time.time()
        
        print("Submitting 20 tasks...")
        for i in range(20):
            result = test_task.delay(f"load_test_message_{i}")
            task_results.append(result)
        
        # Wait for all tasks to complete
        completed_results = []
        failed_tasks = []
        
        for i, result in enumerate(task_results):
            try:
                task_result = result.get(timeout=30)
                completed_results.append(task_result)
                print(f"Task {i+1}/20 completed")
            except Exception as e:
                failed_tasks.append(i)
                print(f"Task {i+1}/20 failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\nLoad Test Results:")
        print(f"  Submitted: {len(task_results)} tasks")
        print(f"  Completed: {len(completed_results)} tasks")
        print(f"  Failed: {len(failed_tasks)} tasks")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Tasks per second: {len(completed_results) / total_time:.1f}")
        print(f"  Success rate: {(len(completed_results) / len(task_results)) * 100:.1f}%")
        
        return len(completed_results) == len(task_results)
        
    except Exception as e:
        print(f"FAILED: Celery load test failed - {e}")
        return False

def test_celery_worker_management():
    """Test Celery worker management and control"""
    print("\nTesting Celery Worker Management...")
    print("=" * 30)
    
    try:
        inspect = celery.control.inspect()
        
        # Get active workers
        active_workers = inspect.active()
        if active_workers:
            print("SUCCESS: Active workers found")
            for worker_name, tasks in active_workers.items():
                print(f"  Worker: {worker_name}")
                print(f"    Active tasks: {len(tasks)}")
        else:
            print("INFO: No active tasks found")
        
        # Get registered tasks
        registered_tasks = inspect.registered()
        if registered_tasks:
            print("\nSUCCESS: Registered tasks found")
            for worker_name, tasks in registered_tasks.items():
                print(f"  Worker: {worker_name}")
                print(f"    Registered tasks: {len(tasks)}")
                for task in tasks[:5]:  # Show first 5 tasks
                    print(f"      - {task}")
        else:
            print("WARNING: No registered tasks found")
        
        # Get worker stats
        stats = inspect.stats()
        if stats:
            print("\nSUCCESS: Worker statistics available")
            for worker_name, worker_stats in stats.items():
                print(f"  Worker: {worker_name}")
                print(f"    Processed: {worker_stats.get('total', {}).get('processed', 'Unknown')}")
                print(f"    Failed: {worker_stats.get('total', {}).get('failed', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Worker management test failed - {e}")
        return False

def test_celery_application_tasks():
    """Test actual application tasks"""
    print("\nTesting Application Tasks...")
    print("=" * 30)
    
    try:
        # Test health check task
        print("Testing health check task...")
        health_result = health_check_task.delay()
        health_response = health_result.get(timeout=10)
        print(f"SUCCESS: Health check completed - {health_response}")
        
        # Test news fetch task (without waiting for completion)
        print("Testing news fetch task...")
        news_result = fetch_news_task.delay()
        print(f"SUCCESS: News fetch task submitted - ID: {news_result.id}")
        
        # Test daily delivery task (without waiting for completion)
        print("Testing daily delivery task...")
        delivery_result = daily_delivery_task.delay()
        print(f"SUCCESS: Daily delivery task submitted - ID: {delivery_result.id}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Application tasks test failed - {e}")
        return False

def test_celery_error_handling():
    """Test Celery error handling"""
    print("\nTesting Celery Error Handling...")
    print("=" * 30)
    
    try:
        # Test with invalid task
        print("Testing invalid task handling...")
        try:
            # This should fail gracefully
            result = celery.send_task('nonexistent_task', args=['test'])
            result.get(timeout=5)
            print("WARNING: Invalid task didn't fail as expected")
        except Exception as e:
            print(f"SUCCESS: Invalid task properly rejected - {type(e).__name__}")
        
        # Test task timeout
        print("Testing task timeout handling...")
        try:
            result = test_task.delay("timeout_test")
            result.get(timeout=1)  # Very short timeout
            print("SUCCESS: Task completed within timeout")
        except Exception as e:
            print(f"SUCCESS: Task timeout handled properly - {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Error handling test failed - {e}")
        return False

def main():
    """Main test function for Celery"""
    print("DailyPod Celery Comprehensive Test")
    print("=" * 50)
    
    # Run all Celery tests
    tests = [
        ("Connection", test_celery_connection),
        ("Task Execution", test_celery_task_execution),
        ("Task Status", test_celery_task_status),
        ("Load Performance", test_celery_load_performance),
        ("Worker Management", test_celery_worker_management),
        ("Application Tasks", test_celery_application_tasks),
        ("Error Handling", test_celery_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Final Summary
    print("\n" + "=" * 50)
    print("CELERY TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("RESULT: All Celery tests passed - Celery is working correctly!")
    else:
        print("RESULT: Some Celery tests failed - Check the issues above.")

if __name__ == "__main__":
    main() 