from django.urls import path
from .views import inference_view

app_name = 'inference_app'  # Namespace for your app's URLs

urlpatterns = [
    path('inference/<int:patient_id>/', inference_view, name='inference_view'),
]
