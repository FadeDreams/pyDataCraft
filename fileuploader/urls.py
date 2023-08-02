from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('test/', views.TestMongoDBView.as_view(), name='test_mongodb'),
    path('teste/', views.TestElasticView.as_view(), name='test_elastic'),
    path('upload/', views.UploadFileView.as_view(), name='upload_file'),
    path('upload/success/', views.UploadSuccessView.as_view(), name='upload_success'),
    path('file/<int:pk>/', views.FileDetailView.as_view(), name='file_detail'),
    path('file/<int:pk>/update/', views.FileUpdateView.as_view(), name='file_update'),
    path('file/<int:pk>/delete/', views.FileDeleteView.as_view(), name='file_delete'),
    path('', views.FileListView.as_view(), name='file_list'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

