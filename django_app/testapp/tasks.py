import time
import random
from celery import shared_task
from .models import TestData

@shared_task
def sample_task(name):
    sleep_time = random.randint(1, 5)
    time.sleep(sleep_time)
    
    test_data = TestData.objects.create(
        name=f"Task Result: {name}",
        value=random.randint(1, 100)
    )
    
    return {
        'task_name': name,
        'sleep_time': sleep_time,
        'created_data_id': test_data.id,
        'message': f'Task {name} completed successfully'
    }