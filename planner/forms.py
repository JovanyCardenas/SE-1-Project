from django import forms
from academics.models import Course
from .models import PersonalTask


class PersonalTaskForm(forms.ModelForm):
    class Meta:
        model = PersonalTask
        fields = ["title", "course", "due_date", "completed", "notes"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.filter(enrollments__user=user)
