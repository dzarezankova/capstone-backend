from django.db import models
from django.core.files.base import ContentFile
import os

class NiftiImage(models.Model):
    file = models.FileField(upload_to='nifti_images/')
    desired_name = models.CharField(max_length=255, blank=True, null=True)  # Optional field for preferred name
    mri_mod = models.CharField(max_length=100, blank=True, null=True)  # Optional field for MRI modality
    # Add any other fields you need

    def save(self, *args, **kwargs):
        if self.file and self.desired_name and self.mri_mod:
            # Construct new file name
            file_name = f"{self.desired_name}_{self.mri_mod}.nii.gz"

            # Read the original file content
            file_content = self.file.read()

            # Create a new File instance with the desired name and content
            new_file = ContentFile(file_content, name=file_name)

            # Assign the new File instance to the file field
            self.file = new_file

        super().save(*args, **kwargs)