from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, AcademicSession, Subject, Enrollment, TeachingAssignment
from apps.attendance.models import AttendanceRecord
from apps.classroom.models import Timetable, Assignment, Submission, StudyMaterial, Examination, Result
from apps.student_services.models import LeaveApplication, Notice, FeeRecord, Complaint
from apps.dashboard.models import ActivityLog


class Command(BaseCommand):
    help = "Seeds optional development mock data. Must ONLY be run manually for demo/testing."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Wipes existing records before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            User.objects.all().delete()
            Department.objects.all().delete()
            AcademicSession.objects.all().delete()

        self.stdout.write(self.style.MIGRATE_HEADING("Beginning Acadify development data seeding..."))

        # 1. Admin User
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                'email': "admin@acadify.edu",
                'first_name': "Super",
                'last_name': "Admin",
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("✓ Admin created: admin / admin123"))

        # 2. Academic Session
        today = date.today()
        session, _ = AcademicSession.objects.get_or_create(
            name="2025 - 2026 Academic Year",
            defaults={
                'start_date': date(2025, 7, 1),
                'end_date': date(2026, 6, 30),
                'is_current': True
            }
        )

        # 3. Departments
        dept_cs, _ = Department.objects.get_or_create(
            code="CSE",
            defaults={'name': "Computer Science & Engineering", 'description': "Computing and software systems"}
        )
        dept_me, _ = Department.objects.get_or_create(
            code="MECH",
            defaults={'name': "Mechanical Engineering", 'description': "Thermal, design, and robotics engineering"}
        )
        dept_ee, _ = Department.objects.get_or_create(
            code="ECE",
            defaults={'name': "Electronics & Communication", 'description': "Signal processing and embedded circuits"}
        )

        # 4. Courses
        course_cs, _ = Course.objects.get_or_create(
            code="BTECH-CS",
            defaults={
                'name': "B.Tech Computer Science",
                'department': dept_cs,
                'duration_years': 4,
                'total_semesters': 8,
                'description': "Four-year undergraduate program in computer engineering"
            }
        )
        course_me, _ = Course.objects.get_or_create(
            code="BTECH-ME",
            defaults={
                'name': "B.Tech Mechanical Engineering",
                'department': dept_me,
                'duration_years': 4,
                'total_semesters': 8,
            }
        )

        # 5. Subjects
        sub_ds, _ = Subject.objects.get_or_create(
            code="CS201",
            defaults={'name': "Data Structures", 'course': course_cs, 'semester': 4, 'credits': 4, 'subject_type': 'THEORY'}
        )
        sub_web, _ = Subject.objects.get_or_create(
            code="CS202",
            defaults={'name': "Web Development", 'course': course_cs, 'semester': 4, 'credits': 3, 'subject_type': 'PRACTICAL'}
        )
        sub_db, _ = Subject.objects.get_or_create(
            code="CS203",
            defaults={'name': "Database Management", 'course': course_cs, 'semester': 4, 'credits': 4, 'subject_type': 'THEORY'}
        )
        sub_cn, _ = Subject.objects.get_or_create(
            code="CS204",
            defaults={'name': "Computer Networks", 'course': course_cs, 'semester': 4, 'credits': 4, 'subject_type': 'THEORY'}
        )
        sub_se, _ = Subject.objects.get_or_create(
            code="CS205",
            defaults={'name': "Software Engineering", 'course': course_cs, 'semester': 4, 'credits': 3, 'subject_type': 'THEORY'}
        )

        # 6. Teachers
        teachers_data = [
            ("teacher_sharma", "sharma@acadify.edu", "Mr.", "Sharma", "FAC001", "Professor", dept_cs, "Room 101"),
            ("teacher_gupta", "gupta@acadify.edu", "Mrs.", "Gupta", "FAC002", "Associate Professor", dept_cs, "Room 102"),
            ("teacher_khan", "khan@acadify.edu", "Mr.", "Khan", "FAC003", "Assistant Professor", dept_cs, "Room 103"),
        ]
        created_teachers = []
        for username, email, first, last, emp_id, desig, dept, room in teachers_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': User.ROLE_TEACHER
                }
            )
            user.set_password("teacher123")
            user.save()
            tp, _ = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': emp_id,
                    'department': dept,
                    'designation': desig,
                    'office_room': room,
                    'joining_date': date(2021, 1, 15)
                }
            )
            created_teachers.append(tp)

        # Head of department
        dept_cs.head_of_department = created_teachers[0]
        dept_cs.save()

        # Teaching Assignments
        TeachingAssignment.objects.get_or_create(teacher=created_teachers[0], subject=sub_ds, session=session, section="A")
        TeachingAssignment.objects.get_or_create(teacher=created_teachers[0], subject=sub_web, session=session, section="A")
        TeachingAssignment.objects.get_or_create(teacher=created_teachers[1], subject=sub_db, session=session, section="A")
        TeachingAssignment.objects.get_or_create(teacher=created_teachers[2], subject=sub_cn, session=session, section="A")
        TeachingAssignment.objects.get_or_create(teacher=created_teachers[2], subject=sub_se, session=session, section="A")

        self.stdout.write(self.style.SUCCESS("✓ Teachers created: teacher_sharma, teacher_gupta, teacher_khan (pwd: teacher123)"))

        # 7. Students (Matching Reference names)
        students_data = [
            ("student_rahul", "rahul@acadify.edu", "Rahul", "Sharma", "CS2024001", "MALE", "123, Green Park, New Delhi", "+91 9876543210"),
            ("student_priya", "priya@acadify.edu", "Priya", "Singh", "CS2024002", "FEMALE", "45, Park Street, Kolkata", "+91 9876543211"),
            ("student_aman", "aman@acadify.edu", "Aman", "Verma", "CS2024003", "MALE", "12, Civil Lines, Jaipur", "+91 9876543212"),
            ("student_neha", "neha@acadify.edu", "Neha", "Gupta", "CS2024004", "FEMALE", "78, Model Town, Delhi", "+91 9876543213"),
            ("student_rohan", "rohan@acadify.edu", "Rohan", "Yadav", "CS2024005", "MALE", "56, Sector 14, Gurgaon", "+91 9876543214"),
        ]
        created_students = []
        for username, email, first, last, sid, gender, addr, phone in students_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'phone': phone,
                    'role': User.ROLE_STUDENT
                }
            )
            user.set_password("student123")
            user.save()
            sp, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': sid,
                    'department': dept_cs,
                    'course': course_cs,
                    'semester': 4,
                    'batch_session': session,
                    'gender': gender,
                    'address': addr,
                    'guardian_name': f"Mr. {last}",
                    'guardian_phone': "+91 9988776655",
                    'date_of_birth': date(2004, 1, 12),
                    'blood_group': "O+"
                }
            )
            Enrollment.objects.get_or_create(student=sp, course=course_cs, session=session, semester=4)
            created_students.append(sp)

        self.stdout.write(self.style.SUCCESS("✓ Students created: student_rahul, student_priya, ... (pwd: student123)"))

        # 8. Timetable
        days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
        timetable_slots = [
            (sub_ds, created_teachers[0], "09:00", "10:00", "Room 101"),
            (sub_web, created_teachers[0], "10:30", "11:30", "Lab 2"),
            (sub_db, created_teachers[1], "12:00", "13:00", "Room 102"),
            (sub_cn, created_teachers[2], "14:00", "15:00", "Room 103"),
            (sub_se, created_teachers[2], "15:30", "16:30", "Room 104"),
        ]
        for day in days:
            for sub, teacher, start, end, room in timetable_slots:
                Timetable.objects.get_or_create(
                    day_of_week=day,
                    start_time=start,
                    room_number=room,
                    defaults={'subject': sub, 'teacher': teacher, 'end_time': end, 'section': "A"}
                )

        # 9. Attendance Records (Real records for today and past days)
        for i in range(14):
            day_dt = today - timedelta(days=i)
            if day_dt.weekday() < 5:  # Mon to Fri
                for s in created_students:
                    # Rahul has good attendance, Aman occasional absent
                    status = AttendanceRecord.STATUS_PRESENT
                    if s.student_id == "CS2024003" and i % 3 == 0:
                        status = AttendanceRecord.STATUS_ABSENT
                    elif s.student_id == "CS2024005" and i % 5 == 0:
                        status = AttendanceRecord.STATUS_LATE

                    AttendanceRecord.objects.update_or_create(
                        student=s,
                        subject=sub_ds,
                        date=day_dt,
                        defaults={'status': status, 'marked_by': created_teachers[0].user}
                    )

        # 10. Assignments & Submissions
        asgn1, _ = Assignment.objects.get_or_create(
            title="Web Development Project",
            subject=sub_web,
            defaults={
                'created_by': created_teachers[0].user,
                'description': "Design a responsive student portal dashboard with HTML, CSS, and Vanilla JS.",
                'due_date': today + timedelta(days=15),
                'max_marks': 100
            }
        )
        asgn2, _ = Assignment.objects.get_or_create(
            title="Database Normalization",
            subject=sub_db,
            defaults={
                'created_by': created_teachers[1].user,
                'description': "Normalize the supplied academic schema from 1NF through BCNF.",
                'due_date': today + timedelta(days=7),
                'max_marks': 50
            }
        )
        # Rahul submission
        Submission.objects.get_or_create(
            assignment=asgn1,
            student=created_students[0],
            defaults={
                'notes': "Implemented clean responsive SaaS dashboard with Bootstrap 5.",
                'marks_obtained': 92,
                'status': Submission.STATUS_GRADED,
                'feedback': "Outstanding UI hierarchy and database integration."
            }
        )

        # 11. Examinations & Results
        exam, _ = Examination.objects.get_or_create(
            name="Semester 4 Mid-Term Examinations 2025",
            defaults={
                'exam_type': Examination.TYPE_MID_SEM,
                'session': session,
                'semester': 4,
                'start_date': date(2025, 4, 1),
                'end_date': date(2025, 4, 15),
                'is_published': True
            }
        )
        # Results for Rahul (Matching reference Screen 10)
        results_data = [
            (sub_ds, 28, 62, "A+"),
            (sub_web, 27, 60, "A"),
            (sub_db, 26, 58, "B+"),
            (sub_cn, 25, 59, "B+"),
            (sub_se, 29, 64, "A+"),
        ]
        for sub, internal, endsem, grade in results_data:
            Result.objects.get_or_create(
                examination=exam,
                student=created_students[0],
                subject=sub,
                defaults={
                    'internal_marks': internal,
                    'end_sem_marks': endsem,
                    'max_marks': 100,
                    'grade': grade
                }
            )

        # 12. Leave Applications
        LeaveApplication.objects.get_or_create(
            student=created_students[0],
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=5),
            defaults={
                'reason': "Attending national collegiate coding hackathon in Bengaluru.",
                'status': LeaveApplication.STATUS_APPROVED,
                'reviewed_by': admin_user,
                'admin_remarks': "Approved. Represent the university well!"
            }
        )
        LeaveApplication.objects.get_or_create(
            student=created_students[1],
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            defaults={
                'reason': "Viral fever recovery and medical checkup.",
                'status': LeaveApplication.STATUS_PENDING
            }
        )

        # 13. Notices (Matching Screen 12)
        Notice.objects.get_or_create(
            title="College will remain closed on 15th August for Independence Day",
            defaults={
                'content': "All academic classes and administrative offices will observe the national holiday.",
                'category': Notice.CATEGORY_GENERAL,
                'audience': Notice.AUDIENCE_ALL,
                'author': admin_user,
                'is_pinned': True
            }
        )
        Notice.objects.get_or_create(
            title="Mid-semester Examination Schedule Released",
            defaults={
                'content': "The examination schedule for all undergraduate engineering courses has been published on the portal.",
                'category': Notice.CATEGORY_EXAM,
                'audience': Notice.AUDIENCE_STUDENTS,
                'author': admin_user
            }
        )
        Notice.objects.get_or_create(
            title="Annual Inter-College Sports & Hackathon Registration",
            defaults={
                'content': "Registration is now open for university athletics, cricket, football, and cybersecurity events.",
                'category': Notice.CATEGORY_EVENT,
                'audience': Notice.AUDIENCE_ALL,
                'author': admin_user
            }
        )

        # 14. Fee Records (Matching Screen 14)
        FeeRecord.objects.get_or_create(
            student=created_students[0],
            semester=1,
            defaults={'title': "Semester 1 Tuition & Lab Fee", 'amount': 15000, 'paid_amount': 15000, 'due_date': date(2024, 7, 10), 'paid_date': date(2024, 7, 5), 'status': FeeRecord.STATUS_PAID, 'receipt_number': "RCP-2024-001"}
        )
        FeeRecord.objects.get_or_create(
            student=created_students[0],
            semester=2,
            defaults={'title': "Semester 2 Tuition Fee", 'amount': 15000, 'paid_amount': 15000, 'due_date': date(2025, 1, 10), 'paid_date': date(2025, 1, 4), 'status': FeeRecord.STATUS_PAID, 'receipt_number': "RCP-2025-002"}
        )
        FeeRecord.objects.get_or_create(
            student=created_students[0],
            semester=3,
            defaults={'title': "Semester 3 Tuition Fee", 'amount': 15000, 'paid_amount': 15000, 'due_date': date(2025, 7, 10), 'paid_date': date(2025, 7, 2), 'status': FeeRecord.STATUS_PAID, 'receipt_number': "RCP-2025-003"}
        )
        FeeRecord.objects.get_or_create(
            student=created_students[0],
            semester=4,
            defaults={'title': "Semester 4 Tuition & Campus Amenities Fee", 'amount': 15000, 'paid_amount': 0, 'due_date': today + timedelta(days=20), 'status': FeeRecord.STATUS_PENDING, 'receipt_number': "RCP-2026-004"}
        )

        # 15. Complaints (Matching Screen 15)
        Complaint.objects.get_or_create(
            student=created_students[0],
            subject="Library book not available in reserve section",
            defaults={'category': Complaint.CATEGORY_LIBRARY, 'description': "Data Structures by Tanenbaum 3rd edition is needed for term reference.", 'status': Complaint.STATUS_RESOLVED, 'admin_response': "Additional copies procured and reserved on Rack 4."}
        )
        Complaint.objects.get_or_create(
            student=created_students[0],
            subject="WiFi signal dropping in Main Block Room 102",
            defaults={'category': Complaint.CATEGORY_WIFI, 'description': "Frequent connectivity drops during evening lab sessions.", 'status': Complaint.STATUS_IN_REVIEW, 'admin_response': "IT networking team has been dispatched to replace the access point router."}
        )

        # 16. Activity Logs
        ActivityLog.objects.create(user=admin_user, action="Published Mid-semester examination schedule", module="Examinations")
        ActivityLog.objects.create(user=created_teachers[0].user, action="Marked attendance for Computer Science Semester 4", module="Attendance")
        ActivityLog.objects.create(user=created_students[0].user, action="Submitted Web Development Project solution", module="Assignments")

        self.stdout.write(self.style.SUCCESS("✓ Data seeding complete! All mock data records successfully generated in the database."))
