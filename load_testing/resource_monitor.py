import time
import psutil
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import requests


class ResourceMonitor:
    def __init__(self, target_ports: List[int] = [8000, 5001]):
        self.target_ports = target_ports
        self.monitoring = False
        self.monitor_thread = None
        self.metrics = []
        self.start_time = None
        
    def get_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """Find process listening on specific port"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process = psutil.Process(proc.info['pid'])
                connections = process.net_connections()
                if connections:
                    for conn in connections:
                        if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                            return process
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        return None
    
    def get_system_metrics(self) -> Dict:
        """Get current system-wide metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / 1024 / 1024,
                'memory_available_mb': memory.available / 1024 / 1024
            },
            'processes': {}
        }
        
        # Monitor target application processes
        for port in self.target_ports:
            proc = self.get_process_by_port(port)
            if proc:
                try:
                    proc_info = {
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.memory_info().rss / 1024 / 1024,
                        'num_threads': proc.num_threads(),
                        'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                        'status': proc.status()
                    }
                    metrics['processes'][f'port_{port}'] = proc_info
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        return metrics
    
    def start_monitoring(self, interval: float = 2.0):
        """Start monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = []
        
        def monitor_loop():
            while self.monitoring:
                try:
                    metrics = self.get_system_metrics()
                    self.metrics.append(metrics)
                    time.sleep(interval)
                except Exception as e:
                    print(f"Monitoring error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return collected metrics"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        return self.get_summary()
    
    def get_summary(self) -> Dict:
        """Generate summary statistics from collected metrics"""
        if not self.metrics:
            return {}
        
        summary = {
            'duration_seconds': time.time() - self.start_time if self.start_time else 0,
            'total_samples': len(self.metrics),
            'system_summary': {},
            'process_summary': {}
        }
        
        # Calculate system averages
        cpu_values = [m['system']['cpu_percent'] for m in self.metrics]
        memory_values = [m['system']['memory_percent'] for m in self.metrics]
        
        summary['system_summary'] = {
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_percent': sum(memory_values) / len(memory_values),
            'max_memory_percent': max(memory_values)
        }
        
        # Calculate per-process averages
        for port in self.target_ports:
            port_key = f'port_{port}'
            process_metrics = []
            
            for metric in self.metrics:
                if port_key in metric['processes']:
                    process_metrics.append(metric['processes'][port_key])
            
            if process_metrics:
                cpu_values = [p['cpu_percent'] for p in process_metrics]
                memory_values = [p['memory_mb'] for p in process_metrics]
                thread_values = [p['num_threads'] for p in process_metrics]
                
                summary['process_summary'][port_key] = {
                    'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
                    'max_cpu_percent': max(cpu_values),
                    'avg_memory_mb': sum(memory_values) / len(memory_values),
                    'max_memory_mb': max(memory_values),
                    'avg_threads': sum(thread_values) / len(thread_values),
                    'max_threads': max(thread_values),
                    'samples': len(process_metrics)
                }
        
        return summary
    
    def save_results(self, filename: str):
        """Save detailed results to JSON file"""
        results = {
            'summary': self.get_summary(),
            'detailed_metrics': self.metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    
    def test_app_responsiveness(self, port: int, endpoint: str = "/") -> Dict:
        """Test if app is responsive"""
        try:
            response = requests.get(f"http://localhost:{port}{endpoint}", timeout=5)
            return {
                'responsive': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                'responsive': False,
                'error': str(e)
            }


def main():
    """Example usage of ResourceMonitor"""
    monitor = ResourceMonitor([8000, 5000])
    
    print("Starting resource monitoring...")
    monitor.start_monitoring(interval=1.0)
    
    # Monitor for 30 seconds
    time.sleep(30)
    
    print("Stopping monitoring...")
    summary = monitor.stop_monitoring()
    
    print("Summary:")
    print(json.dumps(summary, indent=2))
    
    # Save detailed results
    monitor.save_results("resource_monitoring_results.json")


if __name__ == "__main__":
    main()