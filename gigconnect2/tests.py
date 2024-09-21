from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User, Job, JobCategory, Skill, JobApplication
from .serializers import JobSerializer, JobApplicationSerializer

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123', role=User.Role.CLIENT)
        self.freelancer = User.objects.create_user(username='freelancer', password='testpass123', role=User.Role.FREELANCER)
        self.job_category = JobCategory.objects.create(name='Test Category')
        self.skill = Skill.objects.create(name='Test Skill')
        self.job = Job.objects.create(
            title='Test Job',
            description='Test Description',
            client=self.user,
            category=self.job_category,
            pay=100
        )
        self.job.required_skills.add(self.skill)

    def test_signup_client(self):
        url = reverse('signup_client')
        data = {
            'username': 'newclient',
            'password': 'newpass123',
            'email': 'newclient@test.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('access' in response.data)

    def test_login(self):
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)

    def test_job_category_list_create(self):
        url = reverse('job_category_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_job_list(self):
        url = reverse('job_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_apply_for_job(self):
        self.client.force_authenticate(user=self.freelancer)
        url = reverse('apply_for_job', kwargs={'job_id': self.job.id})
        data = {
            'cover_letter': 'Test cover letter',
            'proposed_pay': 90,
            'estimated_completion_time': '5 days'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_jobs_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('client_jobs_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_freelancer_job_applications(self):
        self.client.force_authenticate(user=self.freelancer)
        JobApplication.objects.create(
            job=self.job,
            user=self.freelancer,
            cover_letter='Test application',
            proposed_pay=95,
            estimated_completion_time='4 days'
        )
        url = reverse('freelancer_job_applications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_view(self):
        url = reverse('search')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('jobs' in response.data)
        self.assertTrue('skills' in response.data)
        self.assertTrue('freelancers' in response.data)
        self.assertTrue('job_categories' in response.data)
