from django.db import models
import uuid
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class CustomUser(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    phone_number = models.BigIntegerField(
        _("Phone Number"),
        validators=[
            MinValueValidator(1000000000), 
            MaxValueValidator(999999999999999)  
        ],
        unique=True,
        blank=False,
        null=False,
        help_text=_("Enter 10-15 digit phone number")
    )
    department = models.CharField(
        _("Department"),
        max_length=50,
        blank=False,
        null=False
    )
    address = models.TextField(
        _("Address"),
        max_length=100,
        blank=False,
        null=False
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='custom_user'
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True
    )

    class Meta:
        verbose_name = _("Custom User")
        verbose_name_plural = _("Custom Users")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.department}"

    @classmethod
    def get_user_count(cls):
        return cls.objects.count()