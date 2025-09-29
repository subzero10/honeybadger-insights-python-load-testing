from django.contrib import admin
from .models import TestData

@admin.register(TestData)
class TestDataAdmin(admin.ModelAdmin):
    list_display = ['name', 'value', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']