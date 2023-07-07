from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import datetime
import random
from django.db.models import F

class DefaultField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by', blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by', blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_deleted_by', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


