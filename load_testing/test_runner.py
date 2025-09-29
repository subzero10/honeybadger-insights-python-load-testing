#!/usr/bin/env python3

import os
import sys
import time
import json
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from resource_monitor import ResourceMonitor

FLASK_RUN_PORT=5002
DJANGO_RUN_PORT=8001

class LoadTestRunner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.load_testing_dir = self.project_root / "load_testing"
        self.django_dir = self.project_root / "django_app"
        self.flask_dir = self.project_root / "flask_app"

        # Test configurations
        self.test_configs = {
            'light_load': {
                'users': 10,
                'spawn_rate': 2,
                'duration': '1m',
                'description': 'Light load test - 10 users over 1 minute'
            },
            'medium_load': {
                'users': 50,
                'spawn_rate': 5,
                'duration': '5m',
                'description': 'Medium load test - 50 users over 5 minutes'
            },
            'heavy_load': {
                'users': 100,
                'spawn_rate': 10,
                'duration': '5m',
                'description': 'Heavy load test - 100 users over 5 minutes'
            },
            'burst_load': {
                'users': 200,
                'spawn_rate': 50,
                'duration': '3m',
                'description': 'Burst load test - 200 users spawned quickly'
            }
        }

        self.active_processes = []

    def setup_environment(self, app: str, with_insights: bool):
        """Setup environment variables for the specified app"""
        env_suffix = "with_insights" if with_insights else "without_insights"
        env_file = self.load_testing_dir / "env_configs" / f".env.{app}.{env_suffix}"

        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")

        # Copy environment file to app directory
        if app == "django":
            target = self.django_dir / ".env"
        else:  # flask
            target = self.flask_dir / ".env"

        with open(env_file, 'r') as src, open(target, 'w') as dst:
            dst.write(src.read())

        print(f"✓ Environment configured for {app} ({'with' if with_insights else 'without'} insights)")

    def start_app(self, app: str, port: int) -> subprocess.Popen:
        """Start the specified application"""
        if app == "django":
            cmd = [sys.executable, "manage.py", "runserver", f"0.0.0.0:{port}"]
            cwd = self.django_dir
        else:  # flask
            if app == "flask":
                cmd = ["flask", "--app", "app", "run", "--port", f"{port}", "--debug"]
                cwd = self.flask_dir
                env = os.environ.copy()
                env['FLASK_RUN_PORT'] = str(port)
                env['FLASK_RUN_HOST'] = '0.0.0.0'
            else:
                raise ValueError(f"Unknown app: {app}")

        print(f"Starting {app} on port {port}...")

        # Start app process
        if app == "flask":
            process = subprocess.Popen(
                cmd, cwd=cwd, env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            process = subprocess.Popen(
                cmd, cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        self.active_processes.append(process)

        # Wait for app to be ready
        time.sleep(5)

        # Test if app is responsive
        monitor = ResourceMonitor()
        responsiveness = monitor.test_app_responsiveness(port)

        if not responsiveness['responsive']:
            self.cleanup()
            raise RuntimeError(f"Failed to start {app}: {responsiveness.get('error', 'Unknown error')}")

        print(f"✓ {app.title()} is running on port {port}")
        return process

    def start_celery_worker(self, app: str) -> subprocess.Popen:
        """Start Celery worker for the specified app"""
        if app == "django":
            cmd = ["celery", "-A", "honeybadger_django", "worker", "--loglevel=info"]
            cwd = self.django_dir
        else:  # flask
            cmd = ["celery", "-A", "app:celery", "worker", "--loglevel=info"]
            cwd = self.flask_dir

        print(f"Starting Celery worker for {app}...")

        process = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.active_processes.append(process)
        time.sleep(3)  # Give Celery time to start

        print(f"✓ Celery worker started for {app}")
        return process

    def run_locust_test(self, target_host: str, app: str, config_name: str, insights_label: str, user_class: str = "DatabaseHeavyUser") -> dict:
        """Run Locust load test with specified configuration"""
        config = self.test_configs[config_name]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_prefix = f"{app}_{insights_label}_{config_name}_{timestamp}"

        # Create results directory
        results_dir = self.load_testing_dir / "results" / csv_prefix
        results_dir.mkdir(exist_ok=True)

        cmd = [
            "locust",
            "-f", str(self.load_testing_dir / "locustfile.py"),
            f"--users={config['users']}",
            f"--spawn-rate={config['spawn_rate']}",
            f"--run-time={config['duration']}",
            f"--host={target_host}",
            "--headless",
            "--csv", str(results_dir / "stats"),
            "--html", str(results_dir / "report.html"),
            user_class
        ]

        print(f"Running {config['description']}...")
        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.load_testing_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'csv_files': list(results_dir.glob(f"{csv_prefix}*.csv")),
                'html_report': results_dir / "report.html"
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test timed out after 10 minutes'
            }

    def run_comparison_test(self, app: str, port: int, config_name: str = "medium_load"):
        """Run complete comparison test (with and without insights)"""
        results = {}

        print(f"{'='*60}")
        print(f"COMPARISON TEST: {app.upper()} - {config_name}")
        print(f"{'='*60}")

        for insights_enabled in [False, True]:
            insights_label = "with_insights" if insights_enabled else "without_insights"
            target_host = f"http://localhost:{port}"

            print(f"n--- Testing {insights_label.replace('_', ' ').title()} ---")

            try:
                # Setup environment
                self.setup_environment(app, insights_enabled)

                # Start application
                app_process = self.start_app(app, port)

                # Start Celery worker
                celery_process = self.start_celery_worker(app)

                # Start resource monitoring
                monitor = ResourceMonitor([port])
                monitor.start_monitoring(interval=1.0)

                # Run load test
                test_result = self.run_locust_test(target_host, app, config_name, insights_label)

                # Stop monitoring
                resource_summary = monitor.stop_monitoring()

                # Save detailed monitoring results
                results_dir = self.load_testing_dir / "results"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                monitor_file = results_dir / f"{app}_{config_name}_{insights_label}_{timestamp}_monitoring.json"
                monitor.save_results(str(monitor_file))

                results[insights_label] = {
                    'load_test': test_result,
                    'resource_monitoring': resource_summary,
                    'monitoring_file': str(monitor_file),
                    'success': test_result.get('success', False)
                }

                print(f"✓ Test completed: {insights_label}")

            except Exception as e:
                print(f"✗ Test failed: {e}")
                results[insights_label] = {
                    'success': False,
                    'error': str(e)
                }

            finally:
                # Cleanup processes
                self.cleanup()
                time.sleep(5)  # Wait between tests

        # Save comparison results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = self.load_testing_dir / "results" / f"{app}_{config_name}_comparison_{timestamp}.json"

        with open(comparison_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✓ Comparison results saved to: {comparison_file}")
        return results

    def cleanup(self):
        """Clean up all running processes"""
        print("Cleaning up processes...")

        for process in self.active_processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"Error cleaning up process: {e}")

        self.active_processes.clear()

        # Also kill any leftover processes on our target ports
        for port in [DJANGO_RUN_PORT, FLASK_RUN_PORT]:
            try:
                subprocess.run(['pkill', '-f', f':{port}'], capture_output=True)
            except:
                pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <project_root_path> [test_config] [app]")
        print("test_config options: light_load, medium_load, heavy_load, burst_load")
        print("app options: django, flask, both")
        sys.exit(1)

    project_root = sys.argv[1]
    test_config = sys.argv[2] if len(sys.argv) > 2 else "medium_load"
    app_choice = sys.argv[3] if len(sys.argv) > 3 else "both"

    runner = LoadTestRunner(project_root)

    # Setup signal handler for cleanup
    def signal_handler(sig, frame):
        print("Interrupted by user")
        runner.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        if app_choice in ["django", "both"]:
            runner.run_comparison_test("django", DJANGO_RUN_PORT, test_config)

        if app_choice in ["flask", "both"]:
            runner.run_comparison_test("flask", FLASK_RUN_PORT, test_config)

        print("🎉 All tests completed!")

    except KeyboardInterrupt:
        print("Tests interrupted by user")
    except Exception as e:
        print(f"Test execution failed: {e}")
    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
