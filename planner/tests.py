from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from academics.models import Course, CourseEnrollment
from .models import PersonalTask

class PersonalTaskTests(TestCase):
    def setUp(self):
        self.a = get_user_model().objects.create_user('alice', password='TestPass!461')
        self.b = get_user_model().objects.create_user('bob', password='TestPass!461')
        self.client.force_login(self.a)
        self.course = Course.objects.create(code='CMPE131', name='SE', section='1', semester='fall', year=2026)
        CourseEnrollment.objects.create(user=self.a, course=self.course)

    def test_create_edit_complete_delete(self):
        self.assertEqual(self.client.post(reverse('planner:task_new'), {'title':'Read chapter 2', 'course':self.course.pk, 'due_date':'2026-12-01', 'notes':'Private'}).status_code,302)
        task=PersonalTask.objects.get()
        url=reverse('planner:task_edit', args=[task.pk])
        self.client.post(url, {'title':'Read chapter 3', 'completed':'on'})
        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertEqual(task.title,'Read chapter 3')
        delete=reverse('planner:task_delete', args=[task.pk])
        self.client.get(delete)
        self.assertTrue(PersonalTask.objects.exists())
        self.client.post(delete)
        self.assertFalse(PersonalTask.objects.exists())

    def test_invalid_fields_and_course(self):
        for data in ({'title':''},{'title':'x'*201},{'title':'Test','due_date':'2026-02-30'}, {'title':'Test','notes':'x'*2001}, {'title':'Test','course':'999999'}):
            self.assertEqual(self.client.post(reverse('planner:task_new'),data).status_code,200)
            self.assertFalse(PersonalTask.objects.exists())
        self.client.force_login(self.b)
        self.client.post(reverse('planner:task_new'),{'title':'Test','course':self.course.pk})
        self.assertFalse(PersonalTask.objects.exists())

    def test_ownership_and_html_escaping(self):
        task=PersonalTask.objects.create(owner=self.a,title='<script>alert(1)</script>',notes='Secret')
        self.assertContains(self.client.get(reverse('planner:task_list')), '&lt;script&gt;')
        self.client.force_login(self.b)
        self.assertNotContains(self.client.get(reverse('planner:task_list')), 'Secret')
        for route in ('planner:task_edit','planner:task_delete'):
            url=reverse(route,args=[task.pk])
            self.assertEqual(self.client.get(url).status_code,404)
            self.assertEqual(self.client.post(url,{'title':'Stolen'}).status_code,404)
        self.assertEqual(PersonalTask.objects.get().title,task.title)

    def test_login_and_csrf_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('planner:task_list')).status_code,302)
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        self.assertEqual(client.post(reverse('planner:task_new'),{'title':'Test'}).status_code,403)
