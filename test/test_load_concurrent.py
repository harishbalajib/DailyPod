import os
import sys
import time
import requests
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def simulate_user_request(user_id, request_type="random"):
    """Simulate a single user making a request to the application"""
    try:
        # Define different types of requests users might make
        request_types = [
            ("GET", "/", "Homepage"),
            ("GET", "/subscribe", "Subscribe page"),
            ("POST", "/subscribe", "Subscribe action"),
            ("GET", "/unsubscribe", "Unsubscribe page"),
            ("POST", "/unsubscribe", "Unsubscribe action"),
            ("GET", "/admin", "Admin page"),
            ("GET", "/admin/dashboard", "Admin dashboard")
        ]
        
        if request_type == "random":
            request_type, endpoint, description = random.choice(request_types)
        else:
            request_type, endpoint, description = request_types[user_id % len(request_types)]
        
        start_time = time.time()
        
        # Prepare request data
        headers = {
            'User-Agent': f'DailyPod-Test-User-{user_id}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        if request_type == "GET":
            response = requests.get(
                f"http://{Config.HOST}:{Config.PORT}{endpoint}", 
                headers=headers,
                timeout=10
            )
        else:
            # For POST requests, simulate form data
            data = {
                "phone_number": f"+1{5550000000 + user_id}",
                "language": random.choice(["en", "es", "fr", "de", "pt"])
            }
            response = requests.post(
                f"http://{Config.HOST}:{Config.PORT}{endpoint}", 
                data=data,
                headers=headers,
                timeout=10
            )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            "user_id": user_id,
            "endpoint": endpoint,
            "description": description,
            "method": request_type,
            "status_code": response.status_code,
            "response_time": response_time,
            "response_size": len(response.content),
            "success": response.status_code < 400,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.Timeout:
        return {
            "user_id": user_id,
            "endpoint": endpoint if 'endpoint' in locals() else "unknown",
            "description": "Timeout",
            "method": request_type if 'request_type' in locals() else "unknown",
            "status_code": 0,
            "response_time": 10.0,  # Timeout time
            "response_size": 0,
            "success": False,
            "error": "Request timeout",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.ConnectionError:
        return {
            "user_id": user_id,
            "endpoint": endpoint if 'endpoint' in locals() else "unknown",
            "description": "Connection Error",
            "method": request_type if 'request_type' in locals() else "unknown",
            "status_code": 0,
            "response_time": 0,
            "response_size": 0,
            "success": False,
            "error": "Connection error",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "endpoint": endpoint if 'endpoint' in locals() else "unknown",
            "description": "Error",
            "method": request_type if 'request_type' in locals() else "unknown",
            "status_code": 0,
            "response_time": 0,
            "response_size": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def test_concurrent_users(num_users=50, max_workers=None):
    """Test application with concurrent users"""
    print(f"Testing {num_users} Concurrent Users...")
    print("=" * 50)
    
    if max_workers is None:
        max_workers = min(num_users, 50)  # Cap at 50 workers
    
    start_time = time.time()
    results = []
    
    print(f"Using {max_workers} worker threads")
    print("Starting concurrent user simulation...")
    
    # Use ThreadPoolExecutor to simulate concurrent users
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all user requests
        future_to_user = {
            executor.submit(simulate_user_request, i): i 
            for i in range(num_users)
        }
        
        # Collect results as they complete
        completed_count = 0
        for future in as_completed(future_to_user):
            result = future.result()
            results.append(result)
            completed_count += 1
            
            # Progress indicator
            if completed_count % 10 == 0:
                print(f"Completed {completed_count}/{num_users} requests...")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return results, total_time

def analyze_results(results, total_time):
    """Analyze the load test results"""
    print("\n" + "=" * 50)
    print("LOAD TEST ANALYSIS")
    print("=" * 50)
    
    # Basic statistics
    total_requests = len(results)
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    # Response time analysis
    response_times = [r["response_time"] for r in results if r["response_time"] > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    
    # Status code analysis
    status_codes = {}
    for result in results:
        status = result["status_code"]
        status_codes[status] = status_codes.get(status, 0) + 1
    
    # Endpoint analysis
    endpoint_stats = {}
    for result in results:
        endpoint = result["endpoint"]
        if endpoint not in endpoint_stats:
            endpoint_stats[endpoint] = {"total": 0, "success": 0, "failed": 0}
        endpoint_stats[endpoint]["total"] += 1
        if result["success"]:
            endpoint_stats[endpoint]["success"] += 1
        else:
            endpoint_stats[endpoint]["failed"] += 1
    
    # Print results
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {len(successful_requests)}")
    print(f"Failed Requests: {len(failed_requests)}")
    print(f"Success Rate: {(len(successful_requests) / total_requests) * 100:.1f}%")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Requests per Second: {total_requests / total_time:.1f}")
    
    print(f"\nResponse Time Statistics:")
    print(f"  Average: {avg_response_time:.3f} seconds")
    print(f"  Minimum: {min_response_time:.3f} seconds")
    print(f"  Maximum: {max_response_time:.3f} seconds")
    
    print(f"\nStatus Code Distribution:")
    for status, count in sorted(status_codes.items()):
        percentage = (count / total_requests) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    print(f"\nEndpoint Performance:")
    for endpoint, stats in endpoint_stats.items():
        success_rate = (stats["success"] / stats["total"]) * 100
        print(f"  {endpoint}: {stats['success']}/{stats['total']} ({success_rate:.1f}% success)")
    
    # Performance assessment
    print(f"\nPerformance Assessment:")
    if len(successful_requests) / total_requests >= 0.95:
        print("  SUCCESS: Excellent performance (95%+ success rate)")
    elif len(successful_requests) / total_requests >= 0.90:
        print("  GOOD: Good performance (90%+ success rate)")
    elif len(successful_requests) / total_requests >= 0.80:
        print("  ACCEPTABLE: Acceptable performance (80%+ success rate)")
    else:
        print("  POOR: Poor performance (<80% success rate)")
    
    if avg_response_time < 1.0:
        print("  SUCCESS: Fast response times (<1s average)")
    elif avg_response_time < 3.0:
        print("  GOOD: Reasonable response times (<3s average)")
    elif avg_response_time < 5.0:
        print("  ACCEPTABLE: Slow response times (<5s average)")
    else:
        print("  POOR: Very slow response times (5s+ average)")
    
    return {
        "total_requests": total_requests,
        "successful_requests": len(successful_requests),
        "failed_requests": len(failed_requests),
        "success_rate": (len(successful_requests) / total_requests) * 100,
        "total_time": total_time,
        "avg_response_time": avg_response_time,
        "max_response_time": max_response_time,
        "min_response_time": min_response_time,
        "requests_per_second": total_requests / total_time,
        "status_codes": status_codes,
        "endpoint_stats": endpoint_stats
    }

def test_different_load_scenarios():
    """Test different load scenarios"""
    print("Testing Different Load Scenarios...")
    print("=" * 50)
    
    scenarios = [
        ("Light Load", 10),
        ("Medium Load", 25),
        ("Heavy Load", 50),
        ("Stress Test", 100)
    ]
    
    scenario_results = {}
    
    for scenario_name, num_users in scenarios:
        print(f"\n{scenario_name} Test ({num_users} users)...")
        print("-" * 30)
        
        try:
            results, total_time = test_concurrent_users(num_users)
            analysis = analyze_results(results, total_time)
            scenario_results[scenario_name] = analysis
            
            # Brief summary
            success_rate = analysis["success_rate"]
            avg_time = analysis["avg_response_time"]
            rps = analysis["requests_per_second"]
            
            print(f"Summary: {success_rate:.1f}% success, {avg_time:.3f}s avg, {rps:.1f} req/s")
            
        except Exception as e:
            print(f"ERROR in {scenario_name}: {e}")
            scenario_results[scenario_name] = None
    
    return scenario_results

def save_test_results(results, filename="load_test_results.json"):
    """Save test results to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nTest results saved to {filename}")
    except Exception as e:
        print(f"Failed to save results: {e}")

def main():
    """Main load testing function"""
    print("DailyPod Load Testing - 50 Concurrent Users")
    print("=" * 60)
    
    # Check if app is running
    try:
        response = requests.get(f"http://{Config.HOST}:{Config.PORT}/", timeout=2)
        if response.status_code != 200:
            print("WARNING: Flask app responded but with unexpected status code")
    except requests.exceptions.ConnectionError:
        print("ERROR: Flask app is not running!")
        print("Please start the app with: python run.py")
        print("Then run this test in another terminal.")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    print("SUCCESS: Flask app is running, proceeding with load tests...")
    
    # Run the main 50-user test
    print("\n" + "=" * 60)
    print("MAIN LOAD TEST: 50 Concurrent Users")
    print("=" * 60)
    
    results, total_time = test_concurrent_users(50)
    analysis = analyze_results(results, total_time)
    
    # Determine overall result
    success_rate = analysis["success_rate"]
    avg_response_time = analysis["avg_response_time"]
    
    print("\n" + "=" * 60)
    print("FINAL LOAD TEST RESULT")
    print("=" * 60)
    
    if success_rate >= 95 and avg_response_time < 2.0:
        print("RESULT: EXCELLENT - Application handles 50 concurrent users perfectly!")
    elif success_rate >= 90 and avg_response_time < 3.0:
        print("RESULT: GOOD - Application handles 50 concurrent users well!")
    elif success_rate >= 80 and avg_response_time < 5.0:
        print("RESULT: ACCEPTABLE - Application handles 50 concurrent users adequately.")
    else:
        print("RESULT: POOR - Application struggles with 50 concurrent users.")
    
    # Save results
    save_test_results({
        "test_timestamp": datetime.now().isoformat(),
        "scenario": "50_concurrent_users",
        "analysis": analysis,
        "raw_results": results[:10]  # Save first 10 results as sample
    })

if __name__ == "__main__":
    main() 