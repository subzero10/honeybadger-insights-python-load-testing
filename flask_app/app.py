import os
import json
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from dotenv import load_dotenv
from honeybadger.contrib import FlaskHoneybadger
from honeybadger.contrib import CeleryHoneybadger
import logging

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
    f"{os.getenv('DB_PASSWORD', '')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '3306')}/"
    f"{os.getenv('DB_NAME', 'honeybadger_flask_test')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'flask-insecure-test-key-for-development-only')

app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

app.config['HONEYBADGER_ENVIRONMENT'] = os.getenv('HONEYBADGER_ENVIRONMENT', 'production')
app.config['HONEYBADGER_API_KEY'] = os.getenv('HONEYBADGER_API_KEY')
app.config['HONEYBADGER_INSIGHTS_ENABLED'] = os.getenv('HONEYBADGER_INSIGHTS_ENABLED', False)

# Configure Flask-Honeybadger integration
flask_hb = FlaskHoneybadger(app, report_exceptions=True)

db = SQLAlchemy(app)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    CeleryHoneybadger(celery, report_exceptions=True)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

class TestData(db.Model):
    __tablename__ = 'test_data'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@celery.task
def sample_task(name):
    sleep_time = random.randint(1, 5)
    time.sleep(sleep_time)

    test_data = TestData(
        name=f"Task Result: {name}",
        value=random.randint(1, 100)
    )
    db.session.add(test_data)
    db.session.commit()

    return {
        'task_name': name,
        'sleep_time': sleep_time,
        'created_data_id': test_data.id,
        'message': f'Task {name} completed successfully'
    }

@app.route('/')
def index():
    return render_template('index.html',
                         title='Flask Honeybadger Insights Test App',
                         description='Testing automatic instrumentation with Flask')

@app.route('/api/data/')
def api_data():
    try:
        data = [item.to_dict() for item in TestData.query.all()]
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/task/', methods=['POST'])
def trigger_task():
    try:
        data = request.get_json() or {}
        task_name = data.get('task_name', 'default_task')

        task = sample_task.delay(task_name)

        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': f'Task {task_name} has been queued'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/error/')
def api_error():
    """
    A buggy endpoint to perform division between query parameters a and b. It will fail if b is equal to 0 or
    either a or b are not float.

    :param request: request object
    :return:
    """
    a = float(request.args.get('a', '0'))
    b = float(request.args.get('b', '0'))
    return jsonify({
        'result': a / b
    })

@app.route('/api/warmup/')
def api_warmup():
    """
    Warmup endpoint to pre-initialize Honeybadger Insights components.
    This can be called during health checks or load balancer warmup.
    """
    warmup_results = {
        'status': 'success',
        'checks': []
    }

    # Check if Insights is enabled
    insights_enabled = os.getenv('HONEYBADGER_INSIGHTS_ENABLED', 'false').lower() == 'true'
    warmup_results['checks'].append({
        'name': 'insights_enabled',
        'status': 'enabled' if insights_enabled else 'disabled'
    })

    if insights_enabled:
        try:
            import honeybadger
            # Trigger Honeybadger initialization if not already done
            honeybadger.honeybadger.configure(
                api_key=os.getenv('HONEYBADGER_API_KEY'),
                environment=os.getenv('HONEYBADGER_ENVIRONMENT', 'production'),
                insights_enabled=True
            )
            warmup_results['checks'].append({
                'name': 'honeybadger_config',
                'status': 'configured'
            })

            # Test a database query to warm up SQLAlchemy connections
            test_count = TestData.query.count()
            warmup_results['checks'].append({
                'name': 'database_warmup',
                'status': 'success',
                'record_count': test_count
            })

        except Exception as e:
            warmup_results['checks'].append({
                'name': 'warmup_error',
                'status': 'error',
                'error': str(e)
            })

    return jsonify(warmup_results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Use environment variables for host and port
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5001'))

    app.run(debug=True, host=host, port=port)
