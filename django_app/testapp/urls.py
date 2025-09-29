from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/data/', views.api_data, name='api_data'),
    path('api/task/', views.trigger_task, name='trigger_task'),
    path('api/error/', views.buggy_division, name='buggy_division'),
    path('api/warmup/', views.warmup, name='warmup'),
]
