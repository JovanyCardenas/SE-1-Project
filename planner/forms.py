from django import forms
from .models import Course, Task

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'instructor', 'instructor_email', 'office_hours']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['course', 'title', 'task_type', 'due_date', 'completed', 'notes']
        widgets = {'due_date': forms.DateInput(attrs={'type':'date'}), 'notes': forms.Textarea(attrs={'rows':3})}
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(user=user) if user else Course.objects.none()

class UploadForm(forms.Form):
    syllabus = forms.FileField(help_text='Text-based PDF only, up to 5 MB.')
    def clean_syllabus(self):
        f = self.cleaned_data['syllabus']
        if not f.name.lower().endswith('.pdf') or f.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Choose a PDF file smaller than 5 MB.')
        if f.read(5) != b'%PDF-':
            raise forms.ValidationError('This does not appear to be a valid PDF.')
        f.seek(0)
        return f
