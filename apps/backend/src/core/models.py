"""
Core models module.
Base models for the project.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    `created` and `modified` fields.
    """

    created = models.DateTimeField(
        _("created"),
        auto_now_add=True,
        editable=False,
        help_text=_("Creation datetime"),
    )
    modified = models.DateTimeField(
        _("modified"),
        auto_now=True,
        help_text=_("Last modification datetime"),
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base model that provides an UUID primary key.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("UUID identifier"),
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """
    A complete abstract base model for the project.
    Includes UUIDModel, TimeStampedModel, and SoftDeleteModel.
    """

    class Meta:
        abstract = True
        ordering = ["-created"]
