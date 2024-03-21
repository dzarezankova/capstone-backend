from django.contrib import admin

# Register your models here.
# Register NiftiImage model
from .models import NiftiImage

@admin.register(NiftiImage)
class NiftiImageAdmin(admin.ModelAdmin):
    list_display = ('desired_name', 'mri_mod', 'file')
    search_fields = ('desired_name', 'mri_mod')