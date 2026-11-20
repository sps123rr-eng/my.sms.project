import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from .models import AttendanceRecord
from apps.academics.models import Subject, TeachingAssignment, Enrollment
from apps.accounts.models import StudentProfile, TeacherProfile
from apps.accounts.permissions import admin_required, teacher_required, student_required
from apps.dashboard.models import log_activity


# ==============================================================================
# TEACHER: ATTENDANCE MARKING (SCREEN 7)
# ==============================================================================
@login_required
@teacher_required
def teacher_attendance(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    today = date.today()
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    selected_subject_id = request.GET.get('subject', '')

    # Fetch subjects assigned to this teacher (or all if admin)
    if teacher:
        assigned_subjects = Subject.objects.filter(teaching_assignments__teacher=teacher).distinct()
    else:
        assigned_subjects = Subject.objects.all()

    selected_subject = None
    if selected_subject_id:
        selected_subject = assigned_subjects.filter(id=selected_subject_id).first()
    elif assigned_subjects.exists():
        selected_subject = assigned_subjects.first()
        selected_subject_id = str(selected_subject.id)

    students_with_attendance = []
    if selected_subject:
        # Find students enrolled in the course & semester of this subject
        students = StudentProfile.objects.filter(
            course=selected_subject.course,
            semester=selected_subject.semester,
            user__is_active=True
        ).select_related('user').order_by('student_id')

        # Existing attendance records for this date and subject
        existing_records = {
            rec.student_id: rec.status
            for rec in AttendanceRecord.objects.filter(
                subject=selected_subject,
                date=selected_date_str
            )
        }

        for s in students:
            status = existing_records.get(s.id, 'PRESENT')
            students_with_attendance.append({
                'student': s,
                'status': status,
                'is_saved': s.id in existing_records
            })

    if request.method == 'POST':
        if not selected_subject:
            messages.error(request, "Please select a valid subject.")
            return redirect('teacher_attendance')

        with transaction.atomic():
            saved_count = 0
            for item in students_with_attendance:
                stu = item['student']
                field_name = f"status_{stu.id}"
                new_status = request.POST.get(field_name, AttendanceRecord.STATUS_PRESENT)
                remarks = request.POST.get(f"remarks_{stu.id}", '').strip()

                AttendanceRecord.objects.update_or_create(
                    student=stu,
                    subject=selected_subject,
                    date=selected_date_str,
                    defaults={
                        'status': new_status,
                        'marked_by': request.user,
                        'remarks': remarks or None,
                    }
                )
                saved_count += 1

        log_activity(request.user, f"Marked attendance for {saved_count} students in {selected_subject.code} on {selected_date_str}", module="Attendance")
        messages.success(request, f"Attendance saved successfully for {saved_count} students!")
        return redirect(f"{request.path}?date={selected_date_str}&subject={selected_subject.id}")

    return render(request, 'attendance/teacher_attendance.html', {
        'assigned_subjects': assigned_subjects,
        'selected_subject': selected_subject,
        'selected_date': selected_date_str,
        'students_with_attendance': students_with_attendance,
        'today': today.strftime('%Y-%m-%d'),
    })


# ==============================================================================
# STUDENT: ATTENDANCE HISTORY & STATS
# ==============================================================================
@login_required
@student_required
def student_attendance(request):
    profile = get_object_or_404(StudentProfile, user=request.user)

    records = AttendanceRecord.objects.filter(student=profile).select_related('subject', 'marked_by').order_by('-date')
    
    # Dynamic calculations
    total_records = records.count()
    present_count = records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
    absent_count = records.filter(status=AttendanceRecord.STATUS_ABSENT).count()
    late_count = records.filter(status=AttendanceRecord.STATUS_LATE).count()
    leave_count = records.filter(status=AttendanceRecord.STATUS_LEAVE).count()

    attendance_percentage = round((present_count / total_records * 100), 1) if total_records > 0 else 0

    # Subject-wise attendance calculation
    subject_stats = []
    if profile.course:
        enrolled_subjects = Subject.objects.filter(course=profile.course, semester=profile.semester)
        for sub in enrolled_subjects:
            sub_records = records.filter(subject=sub)
            sub_total = sub_records.count()
            sub_present = sub_records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
            pct = round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0
            subject_stats.append({
                'subject': sub,
                'total': sub_total,
                'present': sub_present,
                'absent': sub_records.filter(status=AttendanceRecord.STATUS_ABSENT).count(),
                'percentage': pct,
            })

    # Pagination
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'attendance/student_attendance.html', {
        'profile': profile,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'leave_count': leave_count,
        'attendance_percentage': attendance_percentage,
        'subject_stats': subject_stats,
        'page_obj': page_obj,
    })


# ==============================================================================
# ADMIN: ATTENDANCE OVERVIEW & CSV EXPORT
# ==============================================================================
@login_required
@admin_required
def admin_attendance(request):
    date_filter = request.GET.get('date', '')
    subject_id = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    records = AttendanceRecord.objects.select_related('student__user', 'subject', 'marked_by').order_by('-date')

    if date_filter:
        records = records.filter(date=date_filter)
    if subject_id:
        records = records.filter(subject_id=subject_id)
    if status_filter:
        records = records.filter(status=status_filter)
    if query:
        records = records.filter(
            Q(student__student_id__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query)
        )

    # Export CSV feature
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{date.today()}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Student ID', 'Student Name', 'Subject', 'Status', 'Marked By', 'Remarks'])
        for r in records:
            writer.writerow([
                r.date,
                r.student.student_id,
                r.student.user.display_name,
                r.subject.name,
                r.get_status_display(),
                r.marked_by.display_name if r.marked_by else 'Admin',
                r.remarks or ''
            ])
        return response

    subjects = Subject.objects.all()
    paginator = Paginator(records, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Aggregates
    today_records = AttendanceRecord.objects.filter(date=date.today())
    today_total = today_records.count()
    today_present = today_records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
    today_pct = round((today_present / today_total * 100), 1) if today_total > 0 else 0

    return render(request, 'attendance/admin_attendance.html', {
        'page_obj': page_obj,
        'subjects': subjects,
        'selected_date': date_filter,
        'selected_subject': subject_id,
        'selected_status': status_filter,
        'query': query,
        'today_total': today_total,
        'today_present': today_present,
        'today_pct': today_pct,
    })
