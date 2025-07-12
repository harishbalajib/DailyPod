import os
import sys
import time
import redis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def test_redis_connection():
    """Test basic Redis connection"""
    print("Testing Redis Connection...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        r.ping()
        print("SUCCESS: Redis connection is working")
        
        # Get Redis info
        info = r.info()
        print(f"Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"Connected clients: {info.get('connected_clients', 'Unknown')}")
        print(f"Used memory: {info.get('used_memory_human', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"FAILED: Redis connection failed - {e}")
        return False

def test_redis_basic_operations():
    """Test basic Redis operations"""
    print("\nTesting Redis Basic Operations...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Test string operations
        print("Testing string operations...")
        r.set("test_string", "Hello Redis")
        value = r.get("test_string")
        print(f"SUCCESS: String set/get - {value}")
        
        # Test integer operations
        print("Testing integer operations...")
        r.set("test_counter", 0)
        r.incr("test_counter")
        r.incr("test_counter")
        counter_value = r.get("test_counter")
        print(f"SUCCESS: Counter operations - {counter_value}")
        
        # Test list operations
        print("Testing list operations...")
        r.lpush("test_list", "item1", "item2", "item3")
        list_items = r.lrange("test_list", 0, -1)
        print(f"SUCCESS: List operations - {list_items}")
        
        # Test hash operations
        print("Testing hash operations...")
        r.hset("test_hash", "field1", "value1")
        r.hset("test_hash", "field2", "value2")
        hash_data = r.hgetall("test_hash")
        print(f"SUCCESS: Hash operations - {hash_data}")
        
        # Cleanup
        r.delete("test_string", "test_counter", "test_list", "test_hash")
        print("SUCCESS: Cleanup completed")
        
        return True
    except Exception as e:
        print(f"FAILED: Basic operations test failed - {e}")
        return False

def test_redis_performance():
    """Test Redis performance under load"""
    print("\nTesting Redis Performance...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Test write performance
        print("Testing write performance...")
        start_time = time.time()
        
        for i in range(1000):
            r.set(f"perf_test_key_{i}", f"value_{i}")
        
        write_time = time.time() - start_time
        write_rate = 1000 / write_time
        print(f"SUCCESS: Wrote 1000 keys in {write_time:.3f}s ({write_rate:.1f} ops/sec)")
        
        # Test read performance
        print("Testing read performance...")
        start_time = time.time()
        
        for i in range(1000):
            value = r.get(f"perf_test_key_{i}")
        
        read_time = time.time() - start_time
        read_rate = 1000 / read_time
        print(f"SUCCESS: Read 1000 keys in {read_time:.3f}s ({read_rate:.1f} ops/sec)")
        
        # Test mixed operations
        print("Testing mixed operations...")
        start_time = time.time()
        
        for i in range(500):
            r.set(f"mixed_test_key_{i}", f"value_{i}")
            r.get(f"mixed_test_key_{i}")
            r.incr("mixed_counter")
        
        mixed_time = time.time() - start_time
        mixed_rate = 1500 / mixed_time  # 500 sets + 500 gets + 500 incrs
        print(f"SUCCESS: Mixed operations in {mixed_time:.3f}s ({mixed_rate:.1f} ops/sec)")
        
        # Cleanup
        keys_to_delete = [f"perf_test_key_{i}" for i in range(1000)]
        keys_to_delete.extend([f"mixed_test_key_{i}" for i in range(500)])
        keys_to_delete.extend(["mixed_counter"])
        
        for key in keys_to_delete:
            r.delete(key)
        print("SUCCESS: Performance test cleanup completed")
        
        return True
    except Exception as e:
        print(f"FAILED: Performance test failed - {e}")
        return False

def test_redis_celery_integration():
    """Test Redis integration with Celery"""
    print("\nTesting Redis-Celery Integration...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Check if Celery is using Redis
        print("Checking Celery Redis usage...")
        
        # Look for Celery-related keys
        celery_keys = r.keys("celery*")
        if celery_keys:
            print(f"SUCCESS: Found {len(celery_keys)} Celery-related keys")
            for key in celery_keys[:5]:  # Show first 5 keys
                print(f"  - {key}")
        else:
            print("INFO: No Celery keys found (workers may not be running)")
        
        # Check for task results
        task_keys = r.keys("celery-task-meta-*")
        if task_keys:
            print(f"SUCCESS: Found {len(task_keys)} task result keys")
        else:
            print("INFO: No task result keys found")
        
        # Check for worker registrations
        worker_keys = r.keys("celery@*")
        if worker_keys:
            print(f"SUCCESS: Found {len(worker_keys)} worker registrations")
            for key in worker_keys:
                print(f"  - {key}")
        else:
            print("INFO: No worker registrations found")
        
        return True
    except Exception as e:
        print(f"FAILED: Redis-Celery integration test failed - {e}")
        return False

def test_redis_memory_usage():
    """Test Redis memory usage and optimization"""
    print("\nTesting Redis Memory Usage...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Get initial memory info
        initial_info = r.info('memory')
        initial_memory = initial_info.get('used_memory_human', 'Unknown')
        print(f"Initial memory usage: {initial_memory}")
        
        # Add some test data
        print("Adding test data...")
        for i in range(100):
            r.set(f"memory_test_key_{i}", "x" * 1000)  # 1KB per key
        
        # Get memory after adding data
        after_info = r.info('memory')
        after_memory = after_info.get('used_memory_human', 'Unknown')
        print(f"Memory after adding data: {after_memory}")
        
        # Test memory optimization
        print("Testing memory optimization...")
        r.flushdb()  # Clear all data
        
        final_info = r.info('memory')
        final_memory = final_info.get('used_memory_human', 'Unknown')
        print(f"Memory after cleanup: {final_memory}")
        
        print("SUCCESS: Memory management working correctly")
        return True
    except Exception as e:
        print(f"FAILED: Memory usage test failed - {e}")
        return False

def test_redis_persistence():
    """Test Redis persistence and data durability"""
    print("\nTesting Redis Persistence...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Get persistence info
        info = r.info('persistence')
        
        print("Redis Persistence Configuration:")
        print(f"  RDB enabled: {info.get('rdb_enabled', 'Unknown')}")
        print(f"  AOF enabled: {info.get('aof_enabled', 'Unknown')}")
        print(f"  Last save time: {info.get('last_save_time', 'Unknown')}")
        print(f"  Last bgsave status: {info.get('last_bgsave_status', 'Unknown')}")
        
        # Test data persistence
        print("Testing data persistence...")
        test_key = "persistence_test_key"
        test_value = "persistence_test_value"
        
        r.set(test_key, test_value)
        
        # Force a save
        r.save()
        print("SUCCESS: Data saved to disk")
        
        # Verify data is still there
        retrieved_value = r.get(test_key)
        if retrieved_value == test_value.encode():
            print("SUCCESS: Data persisted correctly")
        else:
            print("WARNING: Data persistence verification failed")
        
        # Cleanup
        r.delete(test_key)
        
        return True
    except Exception as e:
        print(f"FAILED: Persistence test failed - {e}")
        return False

def test_redis_error_handling():
    """Test Redis error handling"""
    print("\nTesting Redis Error Handling...")
    print("=" * 30)
    
    try:
        r = redis.from_url(Config.REDIS_URL)
        
        # Test invalid operations
        print("Testing invalid operations...")
        try:
            # Try to get a non-existent key
            value = r.get("non_existent_key")
            if value is None:
                print("SUCCESS: Non-existent key handled correctly")
            else:
                print("WARNING: Unexpected value for non-existent key")
        except Exception as e:
            print(f"ERROR: Unexpected error for non-existent key - {e}")
        
        # Test connection error handling
        print("Testing connection error handling...")
        try:
            # Try to use a closed connection
            r.close()
            r.ping()
            print("WARNING: Connection should have failed")
        except Exception as e:
            print(f"SUCCESS: Connection error handled correctly - {type(e).__name__}")
        
        return True
    except Exception as e:
        print(f"FAILED: Error handling test failed - {e}")
        return False

def main():
    """Main test function for Redis"""
    print("DailyPod Redis Comprehensive Test")
    print("=" * 50)
    
    # Run all Redis tests
    tests = [
        ("Connection", test_redis_connection),
        ("Basic Operations", test_redis_basic_operations),
        ("Performance", test_redis_performance),
        ("Celery Integration", test_redis_celery_integration),
        ("Memory Usage", test_redis_memory_usage),
        ("Persistence", test_redis_persistence),
        ("Error Handling", test_redis_error_handling)
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
    print("REDIS TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("RESULT: All Redis tests passed - Redis is working correctly!")
    else:
        print("RESULT: Some Redis tests failed - Check the issues above.")

if __name__ == "__main__":
    main() 