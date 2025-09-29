# Load Testing Framework for Honeybadger Insights

This framework provides comprehensive load testing capabilities to compare the performance of Django and Flask applications with and without Honeybadger Insights instrumentation enabled.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd load_testing
   pip install -r requirements.txt
   ```

2. **Ensure your infrastructure is running:**
   ```bash
   # From project root
   docker-compose up -d  # MySQL and Redis
   ```

3. **Run a comparison test:**
   ```bash
   python test_runner.py /path/to/project/root
   ```

## Test Configurations

The framework includes several predefined test scenarios:

- **light_load**: 10 users, 2 spawn rate, 2 minutes
- **medium_load**: 50 users, 5 spawn rate, 5 minutes  
- **heavy_load**: 100 users, 10 spawn rate, 5 minutes
- **burst_load**: 200 users, 50 spawn rate, 3 minutes

## User Behavior Patterns

The Locust test suite includes multiple user classes:

- **WebAppUser** (default): Realistic mixed workload
  - 40% homepage visits
  - 30% API data requests
  - 20% task triggers
  - 10% error endpoint hits

- **HeavyUser**: Intensive operations with minimal wait time
- **BurstUser**: Creates burst traffic patterns
- **DatabaseHeavyUser**: Focuses on database operations

## Usage Examples

### Run specific test configuration:
```bash
python test_runner.py .. medium_load django
python test_runner.py .. heavy_load flask
python test_runner.py .. burst_load both
```

### Generate performance reports:
```bash
python report_generator.py results/django_medium_load_comparison_20231201_143022.json
```

### Monitor resources only:
```bash
python resource_monitor.py
```

## File Structure

```
load_testing/
├── locustfile.py           # Load test scenarios and user behaviors
├── test_runner.py          # Main test orchestration script
├── resource_monitor.py     # System resource monitoring
├── report_generator.py     # Performance analysis and reporting
├── requirements.txt        # Python dependencies
├── env_configs/           # Environment configurations
│   ├── .env.django.with_insights
│   ├── .env.django.without_insights
│   ├── .env.flask.with_insights
│   └── .env.flask.without_insights
└── results/               # Test results and reports (auto-created)
    ├── *.csv              # Locust raw data
    ├── *.html             # Locust HTML reports
    ├── *_monitoring.json  # Resource monitoring data
    ├── *_comparison.json  # Comparison results
    ├── *_report.md        # Performance analysis reports
    └── *.png              # Performance comparison charts
```

## What Gets Measured

### Application Performance:
- Request throughput (requests/second)
- Response times (percentiles)
- Error rates
- Request success rates

### System Resources:
- CPU usage (system and process-specific)
- Memory consumption (system and process-specific)
- Thread count
- File descriptors
- Process status and responsiveness

### Comparison Metrics:
- Performance overhead of Insights instrumentation
- Resource usage differences
- Stability under load
- Error rate changes

## Environment Configuration

The framework automatically switches between configuration files to enable/disable Insights:

- **With Insights**: `HONEYBADGER_INSIGHTS_ENABLED=true`
- **Without Insights**: `HONEYBADGER_INSIGHTS_ENABLED=false`

Each test run creates isolated environments to ensure accurate comparisons.

## Output and Reports

### Raw Data:
- **Locust CSV files**: Detailed request-level statistics
- **Resource monitoring JSON**: Time-series system metrics
- **HTML reports**: Interactive Locust performance dashboards

### Analysis Reports:
- **Markdown reports**: Human-readable performance analysis
- **Comparison charts**: Visual performance differences
- **Impact analysis**: Quantified overhead calculations

### Key Metrics in Reports:
- CPU impact percentage
- Memory overhead
- Thread count changes
- Response time differences
- Throughput variations

## Best Practices

1. **Clean Environment**: Ensure no other applications are running on ports 8000/5000
2. **Stable Infrastructure**: Make sure MySQL and Redis are running smoothly
3. **Multiple Runs**: Run tests multiple times to account for variability
4. **Resource Monitoring**: Monitor the testing machine's resources too
5. **Baseline Comparison**: Always compare against the same baseline configuration

## Troubleshooting

### Common Issues:

**Port conflicts:**
```bash
# Kill processes using target ports
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:5000 | xargs kill -9
```

**Database connection errors:**
```bash
# Ensure MySQL is running
docker-compose ps
mysql -u root -p -e "SHOW DATABASES;"
```

**Celery worker issues:**
```bash
# Check Redis connectivity  
redis-cli ping
```

**Permission errors:**
```bash
# Ensure scripts are executable
chmod +x test_runner.py report_generator.py
```

## Advanced Usage

### Custom Test Scenarios:
Modify `locustfile.py` to add custom user behaviors or endpoints.

### Extended Monitoring:
Modify `resource_monitor.py` to track additional metrics like disk I/O or network usage.

### Automated Testing:
Use the framework in CI/CD pipelines to monitor performance regressions.

### Load Testing Best Practices:
- Start with light loads and gradually increase
- Monitor both application and database performance
- Test different user behavior patterns
- Validate results across multiple test runs
