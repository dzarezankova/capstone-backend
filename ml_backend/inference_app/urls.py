from django.urls import path, include, re_path
from django.views.generic import RedirectView
from .views import upload_nifti, inference_view

app_name = 'inference_app'  # Namespace for your app's URLs

urlpatterns = [
    path('inference/<str:patient_id>/', inference_view, name='inference_view'),
    path('upload/', upload_nifti, name='upload_nifti'),  # Add the URL pattern for upload_nifti
    re_path(r'^$', RedirectView.as_view(url='/admin/', permanent=False)),
]
