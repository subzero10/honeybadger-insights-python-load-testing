from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TestData
from .tasks import sample_task
import json
import os
import honeybadger

def index(request):
    context = {
        'title': 'Django Honeybadger Insights Test App',
        'description': 'Testing automatic instrumentation with Django'
    }
    return render(request, 'testapp/index.html', context)

def api_data(request):
    try:
        data = list(TestData.objects.all().values('id', 'name', 'value', 'created_at'))

        for item in data:
            item['created_at'] = item['created_at'].isoformat() if item['created_at'] else None

        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def trigger_task(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body) if request.body else {}
            task_name = body.get('task_name', 'default_task')

            task = sample_task.delay(task_name)

            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'message': f'Task {task_name} has been queued'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Only POST method allowed'
        }, status=405)

def buggy_division(request):
    """
    A buggy endpoint to perform division between query parameters a and b. It will fail if b is equal to 0 or
    either a or b are not float.

    :param request: request object
    :return:
    """
    a = float(request.GET.get('a', '0'))
    b = float(request.GET.get('b', '0'))
    return JsonResponse({'result': a / b})

def warmup(request):
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
            
            # Test a database query to warm up ORM connections
            test_count = TestData.objects.count()
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
    
    return JsonResponse(warmup_results)
