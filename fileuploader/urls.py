# fileuploader/urls.py
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('test/', views.test_mongodb, name='test_mongodb'),
    path('teste/', views.test_elastic, name='test_elastic'),
    path('upload/', views.upload_file, name='upload_file'),
    path('upload/success/', views.upload_success, name='upload_success'),
    path('file/<int:pk>/', views.file_detail, name='file_detail'),
    path('file/<int:pk>/update/', views.file_update, name='file_update'),
    path('file/<int:pk>/delete/', views.file_delete, name='file_delete'),
    path('', views.file_list, name='file_list'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

