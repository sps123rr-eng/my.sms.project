from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, Subject, AcademicSession


class AcadifyAllUrlRoutesTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Department, Course, Subject, Session
        self.dept = Department.objects.create(name='Computer Science', code='CSE')
        self.course = Course.objects.create(name='B.Tech CS', code='BTECH-CS', department=self.dept)
        self.session = AcademicSession.objects.create(name='2025-2026', start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), is_current=True)
        self.subject = Subject.objects.create(name='Data Structures', code='CS101', course=self.course, semester=1)

        # Admin User
        self.admin = User.objects.create_user(username='admin_u', email='admin_u@test.com', password='pass', role=User.ROLE_ADMIN, is_superuser=True)

        # Teacher User
        self.teacher_u = User.objects.create_user(username='teacher_u', email='teacher_u@test.com', password='pass', role=User.ROLE_TEACHER)
        self.teacher_p = TeacherProfile.objects.create(user=self.teacher_u, employee_id='EMP999', department=self.dept)

        # Student User
        self.student_u = User.objects.create_user(username='student_u', email='student_u@test.com', password='pass', role=User.ROLE_STUDENT)
        self.student_p = StudentProfile.objects.create(user=self.student_u, student_id='STU999', department=self.dept, course=self.course, semester=1, batch_session=self.session)

    # Public URLs
    def test_public_urls(self):
        public_urls = ['login', 'register', 'password_reset']
        for url_name in public_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Public URL {url_name} failed")

    # Admin URLs (Section 12 Master Prompt)
    def test_admin_urls(self):
        self.client.login(username='admin_u', password='pass')
        admin_urls = [
            'admin_dashboard',
            'admin_students',
            'admin_teachers',
            'admin_departments',
            'admin_courses',
            'admin_subjects',
            'admin_enrollments',
            'admin_attendance',
            'admin_timetable',
            'admin_assignments',
            'admin_results',
            'admin_leaves',
            'admin_notices',
            'admin_fees',
            'admin_complaints',
            'admin_reports',
            'admin_settings',
        ]
        for url_name in admin_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Admin URL {url_name} failed with {response.status_code}")
        self.client.logout()

    # Teacher URLs (Section 12 Master Prompt)
    def test_teacher_urls(self):
        self.client.login(username='teacher_u', password='pass')
        teacher_urls = [
            'teacher_dashboard',
            'teacher_profile',
            'teacher_classes',
            'teacher_students',
            'teacher_attendance',
            'teacher_assignments',
            'teacher_submissions',
            'teacher_study_materials',
            'teacher_results',
            'teacher_leaves',
            'teacher_notices',
        ]
        for url_name in teacher_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Teacher URL {url_name} failed with {response.status_code}")
        self.client.logout()

    # Student URLs (Section 12 Master Prompt)
    def test_student_urls(self):
        self.client.login(username='student_u', password='pass')
        student_urls = [
            'student_dashboard',
            'student_profile',
            'student_attendance',
            'student_timetable',
            'student_assignments',
            'student_results',
            'student_leave',
            'student_notices',
            'student_study_materials',
            'student_fees',
            'student_complaints',
        ]
        for url_name in student_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Student URL {url_name} failed with {response.status_code}")
        self.client.logout()
