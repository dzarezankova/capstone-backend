from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

class NiftiUploadTestCase(TestCase):
    def setUp(self):
        # The Client instance is a dummy web browser for simulating POST requests
        self.client = Client()

    def test_upload_nifti_file(self):
        # Define the URL for your upload view
        # Make sure to replace 'upload_nifti' with the actual name of your upload URL
        upload_url = reverse('inference_app:upload_nifti')

        # Create a mock NIFTI file in memory
        nifti_content = b'Simple NIFTI file content'  # This is a placeholder
        uploaded_file = SimpleUploadedFile('test_image.nii', nifti_content, content_type='application/octet-stream')

        # The data to POST includes the file and any other fields your view expects
        post_data = {
            'nifti_image': uploaded_file,
            'filename': 'test_image',
            'mri_mod': 'T1'
            # Include other fields if necessary
        }

        # Make the POST request to simulate the file upload
        response = self.client.post(upload_url, post_data)

        # Check the response status code (e.g., 200 OK or 201 Created)
        self.assertEqual(response.status_code, 200)  # Or another expected status code

        # Optionally, verify the file has been saved correctly
        # This assumes you have a model for storing uploaded files
        from .models import NiftiImage
        self.assertTrue(NiftiImage.objects.exists())

class InferTestCase(TestCase):
    def setUp(self):
        # The Client instance is a dummy web browser for simulating GET and POST requests
        self.client = Client()

    def test_inference_view(self):
        # Define the URL for your inference view
        # Make sure to replace 'inference_view' with the actual name of your inference URL
        inference_url = reverse('inference_app:inference_view', args=('bobmarley',))

        # Make the GET request to simulate the inference
        response = self.client.get(inference_url)

        # Check the response status code (e.g., 200 OK)
        self.assertEqual(response.status_code, 200)  # Or another expected status code
        print(response.content)

