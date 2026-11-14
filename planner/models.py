from django.conf import settings
from django.db import models


class PersonalTask(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey("academics.Course", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, max_length=2000)

    class Meta:
        ordering = ["completed", "due_date", "pk"]
