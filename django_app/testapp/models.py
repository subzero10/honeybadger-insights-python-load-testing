from django.db import models

class TestData(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'test_data'
    
    def __str__(self):
        return f"{self.name}: {self.value}"