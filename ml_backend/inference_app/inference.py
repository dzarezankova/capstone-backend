from .models import NiftiImage
### imports
import matplotlib.pyplot as plt
import nibabel as nib
import torch
from monai.transforms import (
    Compose,
    NormalizeIntensityd,
    Orientationd,
    Spacingd,
    EnsureTyped,
)
from monai.inferers import sliding_window_inference
from monai.networks.nets import SegResNet

import numpy as np
import boto3
import json
import io
import os
import tempfile
from skimage.measure import marching_cubes
import trimesh
from django.conf import settings

def list_image_paths(patient_id):
    """
    Return a list of local file paths of the 4 NIFTI images per patient.
    Assumes there's a field in NiftiImage model that relates to patient_id.
    """
    # Query the NiftiImage model for images related to the patient_id
    images = NiftiImage.objects.filter(id=patient_id)
    image_paths = []

    for image in images:
        # Django stores the path relative to MEDIA_ROOT in the FileField, 
        # so you prepend the MEDIA_URL to get the absolute path
        # If you need the filesystem path, use image.file.path
        image_path = image.file.path  # Use image.file.path for absolute filesystem path
        image_paths.append(image_path)

    return image_paths

def get_media_images(patient_id):
    search_path = os.path.join(settings.MEDIA_ROOT, 'nifti_images')  # Adjust subdirectory as needed
    image_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(search_path):
        # Filter files that contain the patient_id in their file name
        filtered_files = [file for file in files if str(patient_id) in file]
        # Append the full path to the image_paths list
        image_paths.extend([os.path.join(root, file) for file in filtered_files])

    return image_paths

def transform_data(image_paths):
    imgs_data = []
    img_headers = []

    for image_path in image_paths:
        img = nib.load(image_path)
        img_data = img.get_fdata()
        imgs_data.append(img_data)
        img_headers.append(img.header)

    image_data = np.stack(imgs_data, axis=0)

    # 4D nibabel image as image
    image_dict = {"image": image_data}

    transforms = Compose(
        [
        EnsureTyped(keys=["image"]),
        Orientationd(keys=["image"], axcodes="RAS"),
        Spacingd(
            keys=["image"],
            pixdim=(1.0, 1.0, 1.0),
            mode=("bilinear"),
        ),
        NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True)      
        ]
    )

    transformed_imgs = transforms(image_dict)

    print("Image is transformed")
    final_img = transformed_imgs['image']

    return final_img, img_headers


def model_fn(model_path = None):
    if model_path is None:
        model_path = os.path.join(os.path.dirname(__file__), 'model.pth')

    model = SegResNet(
        blocks_down=[1, 2, 2, 4],
        blocks_up=[1, 1, 1],
        init_filters=16,
        in_channels=4,
        out_channels=3,
        dropout_prob=0.2,
    )
    try:
        if torch.cuda.is_available():
            model.load_state_dict(torch.load(model_path))
        else:
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    except:
        with open(model_path, 'rb') as f:
            if torch.cuda.is_available():
                model.load_state_dict(torch.load(f))
            else:
                model.load_state_dict(torch.load(f, map_location=torch.device('cpu')))

    # Put model in eval mode for inference
    model.eval()

    return model

def inference(model, input, VAL_AMP=False):
    def _compute(input_img):
        print(input_img.shape)
        input_img = torch.unsqueeze(input_img, 0)
        return sliding_window_inference(
            inputs=input_img,
            roi_size=(240, 240, 160),
            sw_batch_size=1,
            predictor=model,
            overlap=0.5,
        )

    if VAL_AMP:
        with torch.cuda.amp.autocast():
            return _compute(input)
    else:
        return _compute(input)

def pytorch_to_stl(prediction):
    if isinstance(prediction, torch.Tensor):
        prediction = prediction.detach().cpu().numpy()
        inf_0 = prediction[0, 0, :, :, :]
        inf_1 = prediction[0, 1, :, :, :]
        inf_2 = prediction[0, 2, :, :, :]

        verts_0, faces_0, _, _ = marching_cubes(inf_0, level=0.5)
        verts_1, faces_1, _, _ = marching_cubes(inf_1, level=0.5)
        verts_2, faces_2, _, _ = marching_cubes(inf_2, level=0.5)

        mesh_0 = trimesh.Trimesh(vertices=verts_0, faces=faces_0)
        mesh_1 = trimesh.Trimesh(vertices=verts_1, faces=faces_1)
        mesh_2 = trimesh.Trimesh(vertices=verts_2, faces=faces_2)

        return mesh_0, mesh_1, mesh_2
    
    raise TypeError("Input must be a torch.Tensor")

