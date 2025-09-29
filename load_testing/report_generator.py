#!/usr/bin/env python3

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from datetime import datetime


class PerformanceReportGenerator:
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def load_comparison_results(self, comparison_file: str) -> Dict:
        """Load comparison results from JSON file"""
        with open(comparison_file, 'r') as f:
            return json.load(f)
    
    def parse_locust_csv(self, csv_file: str) -> pd.DataFrame:
        """Parse Locust stats CSV file"""
        try:
            df = pd.read_csv(csv_file)
            return df
        except Exception as e:
            print(f"Error parsing CSV {csv_file}: {e}")
            return pd.DataFrame()
    
    def generate_summary_table(self, comparison_data: Dict, app_name: str, test_config: str) -> pd.DataFrame:
        """Generate summary comparison table"""
        summary_data = []
        
        for insights_state in ['without_insights', 'with_insights']:
            if insights_state not in comparison_data:
                continue
                
            data = comparison_data[insights_state]
            
            if not data.get('success', False):
                summary_data.append({
                    'Configuration': insights_state.replace('_', ' ').title(),
                    'Status': 'Failed',
                    'Error': data.get('error', 'Unknown error')
                })
                continue
            
            # Extract resource monitoring data
            resource_data = data.get('resource_monitoring', {})
            system_summary = resource_data.get('system_summary', {})
            process_summary = resource_data.get('process_summary', {})
            
            # Find the process data for the current app
            process_key = None
            for key in process_summary.keys():
                if key.startswith('port_'):
                    process_key = key
                    break
            
            process_data = process_summary.get(process_key, {}) if process_key else {}
            
            # Extract Locust data if available
            load_test_data = data.get('load_test', {})
            
            summary_data.append({
                'Configuration': insights_state.replace('_', ' ').title(),
                'Status': 'Success',
                'Avg CPU (System)': f"{system_summary.get('avg_cpu_percent', 0):.1f}%",
                'Max CPU (System)': f"{system_summary.get('max_cpu_percent', 0):.1f}%",
                'Avg Memory (System)': f"{system_summary.get('avg_memory_percent', 0):.1f}%",
                'Max Memory (System)': f"{system_summary.get('max_memory_percent', 0):.1f}%",
                'Avg CPU (Process)': f"{process_data.get('avg_cpu_percent', 0):.1f}%",
                'Max CPU (Process)': f"{process_data.get('max_cpu_percent', 0):.1f}%",
                'Avg Memory (Process)': f"{process_data.get('avg_memory_mb', 0):.1f} MB",
                'Max Memory (Process)': f"{process_data.get('max_memory_mb', 0):.1f} MB",
                'Avg Threads': f"{process_data.get('avg_threads', 0):.0f}",
                'Max Threads': f"{process_data.get('max_threads', 0):.0f}",
                'Test Duration': f"{resource_data.get('duration_seconds', 0):.0f}s",
                'Samples': resource_data.get('total_samples', 0)
            })
        
        return pd.DataFrame(summary_data)
    
    def calculate_performance_impact(self, comparison_data: Dict) -> Dict:
        """Calculate performance impact of insights instrumentation"""
        without_insights = comparison_data.get('without_insights', {})
        with_insights = comparison_data.get('with_insights', {})
        
        if not (without_insights.get('success') and with_insights.get('success')):
            return {'error': 'One or both tests failed'}
        
        # Extract resource data
        baseline_resources = without_insights.get('resource_monitoring', {})
        insights_resources = with_insights.get('resource_monitoring', {})
        
        baseline_system = baseline_resources.get('system_summary', {})
        insights_system = insights_resources.get('system_summary', {})
        
        # Find process data
        baseline_process = {}
        insights_process = {}
        
        for summary in [baseline_resources.get('process_summary', {}), insights_resources.get('process_summary', {})]:
            for key in summary.keys():
                if key.startswith('port_'):
                    if summary == baseline_resources.get('process_summary', {}):
                        baseline_process = summary[key]
                    else:
                        insights_process = summary[key]
                    break
        
        def calculate_impact(baseline_val, insights_val):
            if baseline_val == 0:
                return 0 if insights_val == 0 else float('inf')
            return ((insights_val - baseline_val) / baseline_val) * 100
        
        impact = {
            'system_cpu_impact': calculate_impact(
                baseline_system.get('avg_cpu_percent', 0),
                insights_system.get('avg_cpu_percent', 0)
            ),
            'system_memory_impact': calculate_impact(
                baseline_system.get('avg_memory_percent', 0),
                insights_system.get('avg_memory_percent', 0)
            ),
            'process_cpu_impact': calculate_impact(
                baseline_process.get('avg_cpu_percent', 0),
                insights_process.get('avg_cpu_percent', 0)
            ),
            'process_memory_impact': calculate_impact(
                baseline_process.get('avg_memory_mb', 0),
                insights_process.get('avg_memory_mb', 0)
            ),
            'thread_count_impact': calculate_impact(
                baseline_process.get('avg_threads', 0),
                insights_process.get('avg_threads', 0)
            )
        }
        
        return impact
    
    def create_comparison_charts(self, comparison_data: Dict, app_name: str, output_prefix: str):
        """Create comparison charts"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{app_name.title()} Performance Comparison', fontsize=16)
        
        # Prepare data for charts
        configs = []
        system_cpu = []
        system_memory = []
        process_cpu = []
        process_memory = []
        
        for config_name in ['without_insights', 'with_insights']:
            if config_name not in comparison_data or not comparison_data[config_name].get('success'):
                continue
                
            configs.append(config_name.replace('_', ' ').title())
            
            resource_data = comparison_data[config_name].get('resource_monitoring', {})
            system_summary = resource_data.get('system_summary', {})
            process_summary = resource_data.get('process_summary', {})
            
            # Find process data
            process_data = {}
            for key in process_summary.keys():
                if key.startswith('port_'):
                    process_data = process_summary[key]
                    break
            
            system_cpu.append(system_summary.get('avg_cpu_percent', 0))
            system_memory.append(system_summary.get('avg_memory_percent', 0))
            process_cpu.append(process_data.get('avg_cpu_percent', 0))
            process_memory.append(process_data.get('avg_memory_mb', 0))
        
        # System CPU Usage
        axes[0, 0].bar(configs, system_cpu, color=['skyblue', 'orange'])
        axes[0, 0].set_title('Average System CPU Usage (%)')
        axes[0, 0].set_ylabel('CPU Usage (%)')
        
        # System Memory Usage
        axes[0, 1].bar(configs, system_memory, color=['lightgreen', 'red'])
        axes[0, 1].set_title('Average System Memory Usage (%)')
        axes[0, 1].set_ylabel('Memory Usage (%)')
        
        # Process CPU Usage
        axes[1, 0].bar(configs, process_cpu, color=['gold', 'purple'])
        axes[1, 0].set_title('Average Process CPU Usage (%)')
        axes[1, 0].set_ylabel('CPU Usage (%)')
        
        # Process Memory Usage
        axes[1, 1].bar(configs, process_memory, color=['pink', 'brown'])
        axes[1, 1].set_title('Average Process Memory Usage (MB)')
        axes[1, 1].set_ylabel('Memory Usage (MB)')
        
        plt.tight_layout()
        chart_file = self.results_dir / f'{output_prefix}_comparison_charts.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_file)
    
    def generate_report(self, comparison_file: str) -> str:
        """Generate comprehensive performance report"""
        comparison_data = self.load_comparison_results(comparison_file)
        
        # Extract metadata from filename
        filename = Path(comparison_file).stem
        parts = filename.split('_')
        app_name = parts[0] if len(parts) > 0 else "unknown"
        test_config = parts[1] if len(parts) > 1 else "unknown"
        
        # Generate report content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines = [
            f"# Honeybadger Insights Performance Report",
            f"Generated: {timestamp}\\n",
            f"## Test Configuration",
            f"- **Application**: {app_name.title()}",
            f"- **Test Config**: {test_config}",
            f"- **Source File**: {Path(comparison_file).name}\\n"
        ]
        
        # Summary table
        summary_df = self.generate_summary_table(comparison_data, app_name, test_config)
        report_lines.extend([
            "## Performance Summary",
            summary_df.to_string(index=False),
            "\\n"
        ])
        
        # Impact analysis
        impact = self.calculate_performance_impact(comparison_data)
        if 'error' not in impact:
            report_lines.extend([
                "## Performance Impact Analysis",
                f"- **System CPU Impact**: {impact['system_cpu_impact']:+.1f}%",
                f"- **System Memory Impact**: {impact['system_memory_impact']:+.1f}%",
                f"- **Process CPU Impact**: {impact['process_cpu_impact']:+.1f}%",
                f"- **Process Memory Impact**: {impact['process_memory_impact']:+.1f}%",
                f"- **Thread Count Impact**: {impact['thread_count_impact']:+.1f}%\\n"
            ])
        
        # Create charts
        output_prefix = f"{app_name}_{test_config}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chart_file = self.create_comparison_charts(comparison_data, app_name, output_prefix)
        
        report_lines.extend([
            "## Performance Charts",
            f"Charts saved to: {Path(chart_file).name}\\n"
        ])
        
        # Recommendations
        if 'error' not in impact:
            cpu_impact = impact.get('process_cpu_impact', 0)
            memory_impact = impact.get('process_memory_impact', 0)
            
            report_lines.append("## Recommendations")
            
            if cpu_impact < 5 and memory_impact < 5:
                report_lines.append("✅ **LOW IMPACT**: Insights instrumentation has minimal performance overhead.")
            elif cpu_impact < 15 and memory_impact < 15:
                report_lines.append("⚠️  **MODERATE IMPACT**: Insights instrumentation has noticeable but acceptable overhead.")
            else:
                report_lines.append("❌ **HIGH IMPACT**: Insights instrumentation significantly impacts performance.")
            
            report_lines.append("")
        
        # Save report
        report_file = self.results_dir / f"{output_prefix}_report.md"
        with open(report_file, 'w') as f:
            f.write('\\n'.join(report_lines))
        
        print(f"📊 Report generated: {report_file}")
        print(f"📈 Charts saved: {chart_file}")
        
        return str(report_file)


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <comparison_results_file>")
        sys.exit(1)
    
    comparison_file = sys.argv[1]
    results_dir = Path(comparison_file).parent
    
    generator = PerformanceReportGenerator(str(results_dir))
    report_file = generator.generate_report(comparison_file)
    
    print(f"\\n✅ Report generation complete!")
    print(f"📄 Report: {report_file}")


if __name__ == "__main__":
    main()