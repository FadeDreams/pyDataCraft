# fileuploader/models.py
from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    database_choices = [('elasticsearch', 'Elasticsearch'), ('mongodb', 'MongoDB')]
    database = models.CharField(choices=database_choices, max_length=15, default='elasticsearch')
    uploaded_at = models.DateTimeField(auto_now_add=True)

