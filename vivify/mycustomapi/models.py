from django.contrib.auth.models import (
    AbstractUser, BaseUserManager, AbstractBaseUser)
from django.db import models
from django.utils import timezone
# from django.contrib.auth import get_user_model
from oscar.core import compat
from oscar.apps.customer import abstract_models


class UserProfile(models.Model):
    """
    Dummy profile model used for testing
    """
    user = models.OneToOneField(compat.AUTH_USER_MODEL, related_name="profile",
                                on_delete=models.CASCADE)

    MALE, FEMALE = 'M', 'F'
    choices = (
        (MALE, 'Male'),
        (FEMALE, 'Female'))
    gender = models.CharField(max_length=1, choices=choices,
                              verbose_name='Gender')
    address = models.CharField(max_length=150, null=True)
    phone = models.CharField(max_length = 12, null=False, blank=False, unique=True)
