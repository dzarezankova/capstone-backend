from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import NiftiImage
from .inference import get_media_images, transform_data, model_fn, inference, pytorch_to_stl
import os

@require_http_methods(["POST"])
def upload_nifti(request):
    file = request.FILES.get('nifti_image')
    desired_name = request.POST.get('filename')  # Get the desired filename from the request
    mri_mod = request.POST.get('mri_mod')  # Get the MRI modality from the request

    if not file:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    if not desired_name:
        return JsonResponse({'error': 'No filename specified.'}, status=400)
    
    if not mri_mod:
        return JsonResponse({'error': 'No MRI modality specified.'}, status=400)


    # Change the file name to the desired name
    # Ensure the directory exists (e.g., 'nifti_images/') and save using the new name
    new_filename = f"{desired_name}_{mri_mod}.nii.gz"
    
    # Handle the directory path where files are stored
    file_path = os.path.join('nifti_images', new_filename)
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # Make sure the directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # Create a NiftiImage instance with the custom path
    nifti_image = NiftiImage(file=file_path)
    nifti_image.save()

    return JsonResponse({'message': 'File uploaded successfully with the specified name.', 'id': nifti_image.id})

@require_http_methods(["GET", "POST"])  # Adjust based on your app's needs
def inference_view(request, patient_id):
    # Step 1: List image paths
    image_paths = get_media_images(patient_id)
    if not image_paths:
        return JsonResponse({'error': 'No images found for the given patient ID'}, status=404)

    # Step 2: Transform data
    transformed_img, img_headers = transform_data(image_paths)

    # Step 3: Load the model (consider loading this once and reusing it if it's resource-intensive)
    model = model_fn()

    # Step 4: Perform inference
    prediction = inference(model, transformed_img)

    # Step 5: Convert to STL (this step may need customization based on how you handle STL files)
    meshes = pytorch_to_stl(prediction)

    # Process the STL files as needed, e.g., saving them to disk, returning file paths, etc.
    # Save STL files to location of original Nifti images
    for i, mesh in enumerate(meshes):
        save_directory = os.path.join(settings.MEDIA_ROOT, 'inference_output', str(patient_id)+f'_meshes')
        # Ensure the directory exists
        os.makedirs(save_directory, exist_ok=True)  # exist_ok=True avoids error if directory already exists
        file_path = os.path.join(save_directory, f'{patient_id}_{i}.stl')
        mesh.export(file_path)

    # For demonstration, return a simple success response
    return JsonResponse({f'success': True, 'save_directory' : save_directory})