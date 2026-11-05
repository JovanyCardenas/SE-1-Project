from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Course', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code',models.CharField(max_length=32)),('name',models.CharField(max_length=150)),
            ('instructor',models.CharField(blank=True,max_length=100)),('instructor_email',models.EmailField(blank=True,max_length=254)),
            ('office_hours',models.CharField(blank=True,max_length=255)),('created_at',models.DateTimeField(auto_now_add=True)),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='planner_courses',to=settings.AUTH_USER_MODEL))],
            options={'ordering':['code','name']}),
        migrations.CreateModel(name='Task', fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('title',models.CharField(max_length=180)),
            ('task_type',models.CharField(choices=[('assignment','Assignment'),('exam','Exam'),('other','Other')],default='assignment',max_length=15)),
            ('due_date',models.DateField()),('completed',models.BooleanField(default=False)),
            ('notes',models.TextField(blank=True)),('created_at',models.DateTimeField(auto_now_add=True)),
            ('course',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='tasks',to='planner.course'))],
            options={'ordering':['due_date','title']}),
    ]
