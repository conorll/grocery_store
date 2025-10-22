from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser

from .store import *

class CustomUser(AbstractUser):
    store = models.ForeignKey(Store, null=True, on_delete=models.SET_NULL)

    # objects = MyUserManager()

    class Meta:
        db_table = 'auth_user'

    def get_store(self):
        return self.store

