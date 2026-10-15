from django.db import models
from django.utils.translation import get_language


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_ar = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    @property
    def display_name(self):
        return (
            self.name_ar
            if (get_language() or "").startswith("ar") and self.name_ar
            else self.name
        )

    def __str__(self):
        return self.display_name


class Skill(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="skills"
    )
    name = models.CharField(max_length=100, unique=True)
    name_ar = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    @property
    def display_name(self):
        return (
            self.name_ar
            if (get_language() or "").startswith("ar") and self.name_ar
            else self.name
        )

    def __str__(self):
        return self.display_name
