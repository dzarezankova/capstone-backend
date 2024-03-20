from django.db import models

class NiftiImage(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='nifti_images/')
