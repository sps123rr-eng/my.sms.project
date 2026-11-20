from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, Subject, AcademicSession, Enrollment
from apps.attendance.models import AttendanceRecord
from apps.classroom.models import Assignment, Submission, Examination, Result
from apps.student_services.models import LeaveApplication, Notice, FeeRecord, Complaint


class AcadifyComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password123!',
            role=User.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Department & Course
        self.dept = Department.objects.create(name='Computer Science', code='CSE')
        self.course = Course.objects.create(name='B.Tech CS', code='BTECH-CS', department=self.dept)
        self.session = AcademicSession.objects.create(
            name='2025-2026',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            is_current=True
        )
        self.subject = Subject.objects.create(
            name='Data Structures',
            code='CS101',
            course=self.course,
            semester=1
        )

        # Teacher
        self.teacher_user = User.objects.create_user(
            username='teacher_test',
            email='teacher@test.com',
            password='Password123!',
            role=User.ROLE_TEACHER
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP101',
            department=self.dept
        )

        # Student 1
        self.student_user1 = User.objects.create_user(
            username='student1_test',
            email='student1@test.com',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.student_profile1 = StudentProfile.objects.create(
            user=self.student_user1,
            student_id='STU101',
            department=self.dept,
            course=self.course,
            semester=1,
            batch_session=self.session
        )

        # Student 2
        self.student_user2 = User.objects.create_user(
            username='student2_test',
            email='student2@test.com',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        self.student_profile2 = StudentProfile.objects.create(
            user=self.student_user2,
            student_id='STU102',
            department=self.dept,
            course=self.course,
            semester=1,
            batch_session=self.session
        )

    # =========================================================================
    # 1. AUTHENTICATION TESTS
    # =========================================================================
    def test_valid_login(self):
        response = self.client.post(reverse('login'), {
            'username_or_email': 'admin_test',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard_redirect'), target_status_code=302)

    def test_invalid_login(self):
        response = self.client.post(reverse('login'), {
            'username_or_email': 'admin_test',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password")

    def test_logout(self):
        self.client.login(username='admin_test', password='Password123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

    def test_role_based_redirects(self):
        # Admin redirect
        self.client.login(username='admin_test', password='Password123!')
        res_admin = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(res_admin, reverse('admin_dashboard'))
        self.client.logout()

        # Teacher redirect
        self.client.login(username='teacher_test', password='Password123!')
        res_teacher = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(res_teacher, reverse('teacher_dashboard'))
        self.client.logout()

        # Student redirect
        self.client.login(username='student1_test', password='Password123!')
        res_student = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(res_student, reverse('student_dashboard'))
        self.client.logout()

    def test_unauthorized_access_protection(self):
        # Student trying to access admin panel
        self.client.login(username='student1_test', password='Password123!')
        response = self.client.get(reverse('admin_dashboard'))
        # Must be redirected away from admin dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard_redirect'), target_status_code=302)

    # =========================================================================
    # 2. STUDENT MANAGEMENT TESTS
    # =========================================================================
    def test_duplicate_student_id_prevention(self):
        user_new = User.objects.create_user(
            username='student_dup',
            email='dup@test.com',
            password='Password123!',
            role=User.ROLE_STUDENT
        )
        with self.assertRaises(IntegrityError):
            StudentProfile.objects.create(
                user=user_new,
                student_id='STU101'  # Existing ID
            )

    def test_student_deactivation(self):
        self.client.login(username='admin_test', password='Password123!')
        response = self.client.get(reverse('admin_student_toggle_status', kwargs={'pk': self.student_profile1.id}))
        self.assertEqual(response.status_code, 302)
        self.student_user1.refresh_from_db()
        self.assertFalse(self.student_user1.is_active)

    # =========================================================================
    # 3. ATTENDANCE TESTS
    # =========================================================================
    def test_mark_attendance_and_duplicate_prevention(self):
        today = date.today()
        # Create record
        rec1 = AttendanceRecord.objects.create(
            student=self.student_profile1,
            subject=self.subject,
            date=today,
            status=AttendanceRecord.STATUS_PRESENT,
            marked_by=self.teacher_user
        )
        self.assertEqual(rec1.status, AttendanceRecord.STATUS_PRESENT)

        # Attempting duplicate record must raise IntegrityError
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(
                student=self.student_profile1,
                subject=self.subject,
                date=today,
                status=AttendanceRecord.STATUS_ABSENT
            )

    def test_attendance_percentage_calculation(self):
        # Mark 3 present, 1 absent for student 1
        for i in range(3):
            AttendanceRecord.objects.create(
                student=self.student_profile1,
                subject=self.subject,
                date=date.today() - timedelta(days=i + 1),
                status=AttendanceRecord.STATUS_PRESENT
            )
        AttendanceRecord.objects.create(
            student=self.student_profile1,
            subject=self.subject,
            date=date.today() - timedelta(days=10),
            status=AttendanceRecord.STATUS_ABSENT
        )

        total = self.student_profile1.attendance_records.count()
        present = self.student_profile1.attendance_records.filter(status='PRESENT').count()
        pct = round((present / total * 100), 1)
        self.assertEqual(total, 4)
        self.assertEqual(present, 3)
        self.assertEqual(pct, 75.0)

    def test_student_record_isolation(self):
        # Student 1 logs in and accesses attendance
        self.client.login(username='student1_test', password='Password123!')
        response = self.client.get(reverse('student_attendance'))
        self.assertEqual(response.status_code, 200)
        # Should not show student 2's ID
        self.assertNotContains(response, 'STU102')

    # =========================================================================
    # 4. ASSIGNMENTS TESTS
    # =========================================================================
    def test_create_and_submit_assignment(self):
        assignment = Assignment.objects.create(
            title='Project 1',
            description='Test task description',
            subject=self.subject,
            created_by=self.teacher_user,
            due_date=date.today() + timedelta(days=7),
            max_marks=100
        )
        self.assertEqual(assignment.max_marks, 100)

        # Student 1 submits
        submission = Submission.objects.create(
            assignment=assignment,
            student=self.student_profile1,
            notes='Solved successfully'
        )
        self.assertEqual(submission.status, Submission.STATUS_SUBMITTED)

        # Prevent duplicate submissions from same student for same assignment
        with self.assertRaises(IntegrityError):
            Submission.objects.create(
                assignment=assignment,
                student=self.student_profile1
            )

    # =========================================================================
    # 5. LEAVE APPLICATIONS TESTS
    # =========================================================================
    def test_leave_submission_and_approval(self):
        leave = LeaveApplication.objects.create(
            student=self.student_profile1,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            reason='Medical leave'
        )
        self.assertEqual(leave.status, LeaveApplication.STATUS_PENDING)

        # Admin reviews and approves
        self.client.login(username='admin_test', password='Password123!')
        post_response = self.client.post(reverse('admin_leave_review', kwargs={'pk': leave.id}), {
            'action': 'APPROVE',
            'admin_remarks': 'Approved by dean'
        })
        self.assertEqual(post_response.status_code, 302)
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveApplication.STATUS_APPROVED)
        self.assertEqual(leave.admin_remarks, 'Approved by dean')

    # =========================================================================
    # 6. EMPTY DATABASE / ZERO RECORD VIEWS
    # =========================================================================
    def test_empty_database_views(self):
        # Admin visiting empty / fresh dashboard
        self.client.login(username='admin_test', password='Password123!')
        res_dash = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_reports = self.client.get(reverse('admin_reports'))
        self.assertEqual(res_reports.status_code, 200)

        res_fees = self.client.get(reverse('admin_fees'))
        self.assertEqual(res_fees.status_code, 200)
