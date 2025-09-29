import random
import json
from locust import HttpUser, task, between, events


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called at the beginning of each test run.
    Performs warmup requests to initialize Honeybadger Insights components.
    """
    if hasattr(environment, 'parsed_options') and hasattr(environment.parsed_options, 'host'):
        host = environment.parsed_options.host
        
        # Warmup both applications if testing both
        warmup_hosts = []
        if ':8000' in host or 'django' in host.lower():
            warmup_hosts.append('http://localhost:8000')
        elif ':5000' in host or 'flask' in host.lower():
            warmup_hosts.append('http://localhost:5000')
        else:
            # If host is not specific, warm up both
            warmup_hosts = ['http://localhost:8000', 'http://localhost:5000']
        
        print("🔥 Performing Honeybadger Insights warmup...")
        
        import requests
        for warmup_host in warmup_hosts:
            try:
                # Call warmup endpoint to pre-initialize components
                response = requests.get(f"{warmup_host}/api/warmup/", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    app_name = "Django" if ":8000" in warmup_host else "Flask"
                    print(f"✅ {app_name} warmup successful: {result}")
                else:
                    print(f"⚠️  Warmup request failed for {warmup_host}: {response.status_code}")
            except Exception as e:
                print(f"❌ Warmup error for {warmup_host}: {e}")
        
        print("🔥 Warmup completed, starting load test...")


class WebAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - includes individual user warmup"""
        # Optional individual warmup for each user
        try:
            self.client.get("/api/warmup/", timeout=5)
        except Exception:
            # Silently continue if warmup fails
            pass
    
    @task(40)
    def view_homepage(self):
        """Simulate users visiting the homepage"""
        self.client.get("/")
    
    @task(30)
    def get_data(self):
        """Simulate users fetching data from API"""
        self.client.get("/api/data/")
    
    @task(20)
    def trigger_task(self):
        """Simulate users triggering background tasks"""
        task_names = ["user_action", "data_processing", "report_generation", "cleanup_task", "analysis_job"]
        payload = {
            "task_name": random.choice(task_names)
        }
        
        with self.client.post(
            "/api/task/",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Task trigger failed: {response.status_code}")
    
    @task(10)
    def trigger_error(self):
        """Simulate users hitting error endpoint (for exception tracking)"""
        # Generate random parameters that might cause errors
        a = random.uniform(0, 100)
        b = random.uniform(-5, 5)  # Sometimes zero, causing division by zero
        
        with self.client.get(
            "/api/error/",
            params={"a": a, "b": b},
            catch_response=True
        ) as response:
            if response.status_code in [200, 500]:  # Both success and errors are expected
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(5)
    def warmup_check(self):
        """Periodically check warmup endpoint to monitor system state"""
        with self.client.get("/api/warmup/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Warmup check failed: {response.status_code}")


class HeavyUser(HttpUser):
    """More intensive user behavior for stress testing"""
    wait_time = between(0.1, 0.5)
    
    @task(50)
    def rapid_data_requests(self):
        """Rapid API data requests"""
        self.client.get("/api/data/")
    
    @task(30)
    def batch_task_triggers(self):
        """Trigger multiple tasks in quick succession"""
        for i in range(random.randint(1, 3)):
            payload = {"task_name": f"batch_task_{i}"}
            self.client.post("/api/task/", json=payload)
    
    @task(20)
    def stress_homepage(self):
        """Stress test homepage rendering"""
        self.client.get("/")


class BurstUser(HttpUser):
    """User that creates burst traffic patterns"""
    wait_time = between(0, 0.1)
    
    @task(1)
    def burst_requests(self):
        """Generate burst traffic to all endpoints"""
        endpoints = ["/", "/api/data/", "/api/task/", "/api/error/"]
        
        # Random burst of requests
        for _ in range(random.randint(3, 8)):
            endpoint = random.choice(endpoints)
            
            if endpoint == "/api/task/":
                self.client.post(endpoint, json={"task_name": "burst_task"})
            elif endpoint == "/api/error/":
                self.client.get(endpoint, params={"a": 10, "b": random.uniform(-2, 2)})
            else:
                self.client.get(endpoint)


class DatabaseHeavyUser(HttpUser):
    """User focused on database-intensive operations"""
    wait_time = between(0.5, 1.5)
    
    @task(70)
    def continuous_data_fetch(self):
        """Continuous database reads"""
        self.client.get("/api/data/")
    
    @task(30)
    def continuous_task_creation(self):
        """Continuous database writes via tasks"""
        payload = {"task_name": f"db_task_{random.randint(1, 1000)}"}
        self.client.post("/api/task/", json=payload)