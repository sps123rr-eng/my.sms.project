import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum
from .models import ActivityLog, log_activity
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, Subject, AcademicSession, TeachingAssignment
from apps.attendance.models import AttendanceRecord
from apps.classroom.models import Timetable, Assignment, Submission, Result
from apps.student_services.models import LeaveApplication, Notice, FeeRecord, Complaint
from apps.accounts.permissions import admin_required, teacher_required, student_required


# ==============================================================================
# SCREEN 3: ADMIN DASHBOARD
# ==============================================================================
@login_required
@admin_required
def admin_dashboard(request):
    today = date.today()

    # Dynamic metrics directly from real database
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_courses = Course.objects.count()
    total_departments = Department.objects.count()

    today_attendance_qs = AttendanceRecord.objects.filter(date=today)
    today_total = today_attendance_qs.count()
    today_present = today_attendance_qs.filter(status=AttendanceRecord.STATUS_PRESENT).count()
    today_absent = today_attendance_qs.filter(status=AttendanceRecord.STATUS_ABSENT).count()
    today_att_rate = round((today_present / today_total * 100), 1) if today_total > 0 else 0

    pending_leaves = LeaveApplication.objects.filter(status=LeaveApplication.STATUS_PENDING).count()
    pending_complaints = Complaint.objects.filter(status=Complaint.STATUS_PENDING).count()

    # Department-wise student distribution for Donut Chart
    dept_stats = Department.objects.annotate(student_count=Count('students')).values('name', 'student_count')
    dept_labels = [d['name'] for d in dept_stats if d['student_count'] > 0]
    dept_counts = [d['student_count'] for d in dept_stats if d['student_count'] > 0]

    # Attendance trends for last 6 months (Monthly Line Chart)
    # Genuinely aggregates monthly attendance records
    month_labels = []
    month_data = []
    for i in range(5, -1, -1):
        m_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        next_m = (m_start + timedelta(days=32)).replace(day=1)
        m_name = m_start.strftime('%b')
        month_labels.append(m_name)

        month_records = AttendanceRecord.objects.filter(date__gte=m_start, date__lt=next_m)
        m_total = month_records.count()
        m_present = month_records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
        pct = round((m_present / m_total * 100), 1) if m_total > 0 else 0
        month_data.append(pct)

    # Recent Actual Activities
    recent_activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:6]

    # Upcoming Notices / Events
    recent_notices = Notice.objects.select_related('author').order_by('-published_date', '-created_at')[:5]

    return render(request, 'dashboards/admin_dashboard.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'today_att_rate': today_att_rate,
        'today_present': today_present,
        'today_absent': today_absent,
        'today_total': today_total,
        'pending_leaves': pending_leaves,
        'pending_complaints': pending_complaints,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_counts_json': json.dumps(dept_counts),
        'month_labels_json': json.dumps(month_labels),
        'month_data_json': json.dumps(month_data),
        'recent_activities': recent_activities,
        'recent_notices': recent_notices,
        'today': today,
    })


# ==============================================================================
# SCREEN 4: TEACHER DASHBOARD
# ==============================================================================
@login_required
@teacher_required
def teacher_dashboard(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    today = date.today()
    day_name = today.strftime('%A').upper()  # e.g. MONDAY

    if teacher:
        assigned_subjects = Subject.objects.filter(teaching_assignments__teacher=teacher).distinct()
        my_classes_count = assigned_subjects.count()

        # Total enrolled students in teacher's assigned subjects
        total_assigned_students = StudentProfile.objects.filter(
            course__in=assigned_subjects.values_list('course', flat=True),
            semester__in=assigned_subjects.values_list('semester', flat=True),
            user__is_active=True
        ).distinct().count()

        # Pending submissions needing grading
        pending_submissions = Submission.objects.filter(
            assignment__created_by=request.user,
            status=Submission.STATUS_SUBMITTED
        ).count()

        # Today's classes from Timetable
        today_classes = Timetable.objects.filter(
            teacher=teacher,
            day_of_week=day_name
        ).select_related('subject__course').order_by('start_time')
    else:
        my_classes_count = 0
        total_assigned_students = 0
        pending_submissions = 0
        today_classes = []

    pending_leaves = LeaveApplication.objects.filter(status=LeaveApplication.STATUS_PENDING).count()
    recent_notices = Notice.objects.all().order_by('-published_date')[:5]

    return render(request, 'dashboards/teacher_dashboard.html', {
        'teacher': teacher,
        'my_classes_count': my_classes_count,
        'total_assigned_students': total_assigned_students,
        'pending_submissions': pending_submissions,
        'pending_leaves': pending_leaves,
        'today_classes': today_classes,
        'recent_notices': recent_notices,
        'today': today,
        'day_name': today.strftime('%A'),
    })


# ==============================================================================
# SCREEN 5: STUDENT DASHBOARD
# ==============================================================================
@login_required
@student_required
def student_dashboard(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    today = date.today()
    day_name = today.strftime('%A').upper()

    # Attendance Rate calculation
    student_records = AttendanceRecord.objects.filter(student=student)
    total_att = student_records.count()
    present_att = student_records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
    absent_att = student_records.filter(status=AttendanceRecord.STATUS_ABSENT).count()
    att_percentage = round((present_att / total_att * 100), 1) if total_att > 0 else 0

    # Pending Assignments
    submitted_assignment_ids = Submission.objects.filter(student=student).values_list('assignment_id', flat=True)
    if student.course:
        pending_assignments = Assignment.objects.filter(
            subject__course=student.course,
            subject__semester=student.semester,
            due_date__gte=today
        ).exclude(id__in=submitted_assignment_ids).count()

        # Today's schedule
        today_classes = Timetable.objects.filter(
            subject__course=student.course,
            subject__semester=student.semester,
            day_of_week=day_name
        ).select_related('subject', 'teacher__user').order_by('start_time')
    else:
        pending_assignments = 0
        today_classes = []

    # Latest Results / CGPA
    results = Result.objects.filter(student=student)
    total_obtained = sum(r.total_marks for r in results)
    total_max = sum(r.max_marks for r in results)
    cgpa = round((total_obtained / total_max * 10), 2) if total_max > 0 else 0

    # Fee Status
    pending_fees = FeeRecord.objects.filter(student=student, status__in=[FeeRecord.STATUS_PENDING, FeeRecord.STATUS_OVERDUE]).count()
    fee_status = "Pending" if pending_fees > 0 else "Paid"

    # Notices
    recent_notices = Notice.objects.filter(
        Q(audience=Notice.AUDIENCE_ALL) |
        Q(audience=Notice.AUDIENCE_STUDENTS) |
        Q(audience=Notice.AUDIENCE_DEPARTMENT, department=student.department)
    ).order_by('-published_date')[:5]

    return render(request, 'dashboards/student_dashboard.html', {
        'student': student,
        'att_percentage': att_percentage,
        'present_att': present_att,
        'absent_att': absent_att,
        'pending_assignments': pending_assignments,
        'cgpa': cgpa,
        'fee_status': fee_status,
        'today_classes': today_classes,
        'recent_notices': recent_notices,
        'today': today,
        'day_name': today.strftime('%A'),
    })


# ==============================================================================
# ADMIN REPORTS & ANALYTICS
# ==============================================================================
@login_required
@admin_required
def admin_reports(request):
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_courses = Course.objects.count()

    dept_summary = Department.objects.annotate(
        students_count=Count('students', distinct=True),
        courses_count=Count('courses', distinct=True)
    )

    attendance_by_status = AttendanceRecord.objects.values('status').annotate(total=Count('id'))

    total_fees_collected = FeeRecord.objects.filter(status=FeeRecord.STATUS_PAID).aggregate(Sum('amount'))['amount__sum'] or 0
    total_fees_pending = FeeRecord.objects.filter(status__in=[FeeRecord.STATUS_PENDING, FeeRecord.STATUS_OVERDUE]).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'reports/admin_reports.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'dept_summary': dept_summary,
        'attendance_by_status': attendance_by_status,
        'total_fees_collected': total_fees_collected,
        'total_fees_pending': total_fees_pending,
    })


# ==============================================================================
# ADMIN SETTINGS & SESSIONS
# ==============================================================================
@login_required
@admin_required
def admin_settings(request):
    sessions = AcademicSession.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_session':
            name = request.POST.get('name')
            start = request.POST.get('start_date')
            end = request.POST.get('end_date')
            is_cur = request.POST.get('is_current') == 'on'
            if name and start and end:
                AcademicSession.objects.create(name=name, start_date=start, end_date=end, is_current=is_cur)
                log_activity(request.user, f"Added academic session {name}", module="Settings")
                messages.success(request, f"Academic session '{name}' created.")
        elif action == 'set_current':
            s_id = request.POST.get('session_id')
            session = get_object_or_404(AcademicSession, id=s_id)
            session.is_current = True
            session.save()
            log_activity(request.user, f"Set current session to {session.name}", module="Settings")
            messages.success(request, f"Session '{session.name}' set as active.")
        return redirect('admin_settings')

    return render(request, 'reports/admin_settings.html', {'sessions': sessions})
