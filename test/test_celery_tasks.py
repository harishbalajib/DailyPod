import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import test_task, fetch_news_task, daily_delivery_task
from celery_app import celery

def test_celery_tasks():
    """
    Test Celery tasks for DailyPod automation
    """
    print("DailyPod Celery Tasks Test")
    print("=" * 40)
    
    try:
        # Test 1: Check Celery connection
        print("1. Testing Celery connection...")
        try:
            # Try to inspect active tasks
            inspect = celery.control.inspect()
            stats = inspect.stats()
            if stats:
                print("   ✓ Celery is running and connected")
            else:
                print("   ⚠ Celery is running but no workers found")
        except Exception as e:
            print(f"   ✗ Celery connection failed: {e}")
            return False
        
        # Test 2: Test simple task
        print("\n2. Testing simple task execution...")
        try:
            # Test a simple task
            result = test_task.delay("DailyPod Celery Test: Task system is working!")
            print(f"   Task submitted with ID: {result.id}")
            
            # Wait for task to complete
            print("   Waiting for task completion...")
            task_result = result.get(timeout=30)
            
            if task_result:
                print("   ✓ Task completed successfully")
                print(f"   Result: {task_result}")
            else:
                print("   ✗ Task failed")
                return False
                
        except Exception as e:
            print(f"   ✗ Task execution failed: {e}")
            return False
        
        # Test 3: Test news fetching task
        print("\n3. Testing news fetching task...")
        try:
            result = fetch_news_task.delay()
            print(f"   News fetching task submitted with ID: {result.id}")
            
            # Wait for task to complete
            print("   Waiting for news fetching...")
            task_result = result.get(timeout=60)
            
            if task_result:
                print("   ✓ News fetching completed successfully")
                print(f"   Result: {task_result}")
            else:
                print("   ✗ News fetching failed")
                return False
                
        except Exception as e:
            print(f"   ✗ News fetching task failed: {e}")
            return False
        
        # Test 4: Test health check
        print("\n4. Testing health check task...")
        try:
            from tasks import health_check_task
            result = health_check_task.delay()
            print(f"   Health check task submitted with ID: {result.id}")
            
            # Wait for task to complete
            print("   Waiting for health check...")
            task_result = result.get(timeout=30)
            
            if task_result:
                print("   ✓ Health check completed successfully")
                print(f"   Result: {task_result}")
            else:
                print("   ✗ Health check failed")
                return False
                
        except Exception as e:
            print(f"   ✗ Health check task failed: {e}")
            return False
        
        print("\n" + "=" * 40)
        print("CELERY TASKS TEST SUMMARY")
        print("=" * 40)
        print("✓ Celery connection: WORKING")
        print("✓ Simple task execution: WORKING")
        print("✓ News fetching task: WORKING")
        print("✓ Health check task: WORKING")
        print("\n🎉 Celery automation is fully operational!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Celery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_celery_tasks()
    if success:
        print("\nDailyPod automation is ready for production!")
    else:
        print("\nDailyPod automation needs attention.") 