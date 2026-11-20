from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Modular views
from apps.accounts import views as account_views
from apps.academics import views as academic_views
from apps.attendance import views as attendance_views
from apps.classroom import views as classroom_views
from apps.student_services import views as service_views
from apps.dashboard import views as dashboard_views

urlpatterns = [
    # Django emergency admin
    path('django-admin/', admin.site.urls),

    # Public & Authentication
    path('', account_views.login_view, name='home'),
    path('login/', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('logout/', account_views.logout_view, name='logout'),
    path('password-reset/', account_views.password_reset_view, name='password_reset'),
    path('password-change/', account_views.password_change_view, name='password_change'),
    path('redirect/', account_views.dashboard_redirect, name='dashboard_redirect'),

    # =========================================================================
    # ADMIN PANEL ROUTES
    # =========================================================================
    path('admin-panel/dashboard/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    
    # Students
    path('admin-panel/students/', account_views.admin_students, name='admin_students'),
    path('admin-panel/students/add/', account_views.admin_student_add, name='admin_student_add'),
    path('admin-panel/students/<int:pk>/edit/', account_views.admin_student_edit, name='admin_student_edit'),
    path('admin-panel/students/<int:pk>/toggle-status/', account_views.admin_student_toggle_status, name='admin_student_toggle_status'),
    path('admin-panel/students/<int:pk>/detail/', account_views.admin_student_detail, name='admin_student_detail'),

    # Teachers
    path('admin-panel/teachers/', account_views.admin_teachers, name='admin_teachers'),
    path('admin-panel/teachers/add/', account_views.admin_teacher_add, name='admin_teacher_add'),
    path('admin-panel/teachers/<int:pk>/edit/', account_views.admin_teacher_edit, name='admin_teacher_edit'),
    path('admin-panel/teachers/<int:pk>/toggle-status/', account_views.admin_teacher_toggle_status, name='admin_teacher_toggle_status'),

    # Academics
    path('admin-panel/departments/', academic_views.admin_departments, name='admin_departments'),
    path('admin-panel/departments/<int:pk>/edit/', academic_views.admin_department_edit, name='admin_department_edit'),
    path('admin-panel/departments/<int:pk>/delete/', academic_views.admin_department_delete, name='admin_department_delete'),

    path('admin-panel/courses/', academic_views.admin_courses, name='admin_courses'),
    path('admin-panel/courses/<int:pk>/edit/', academic_views.admin_course_edit, name='admin_course_edit'),
    path('admin-panel/courses/<int:pk>/delete/', academic_views.admin_course_delete, name='admin_course_delete'),

    path('admin-panel/subjects/', academic_views.admin_subjects, name='admin_subjects'),
    path('admin-panel/subjects/<int:pk>/edit/', academic_views.admin_subject_edit, name='admin_subject_edit'),
    path('admin-panel/subjects/<int:pk>/delete/', academic_views.admin_subject_delete, name='admin_subject_delete'),

    path('admin-panel/enrollments/', academic_views.admin_enrollments, name='admin_enrollments'),
    path('admin-panel/enrollments/<int:pk>/delete/', academic_views.admin_enrollment_delete, name='admin_enrollment_delete'),

    # Attendance
    path('admin-panel/attendance/', attendance_views.admin_attendance, name='admin_attendance'),

    # Timetable
    path('admin-panel/timetable/', classroom_views.timetable_view, name='admin_timetable'),
    path('admin-panel/timetable/add/', classroom_views.admin_timetable_add, name='admin_timetable_add'),
    path('admin-panel/timetable/<int:pk>/delete/', classroom_views.admin_timetable_delete, name='admin_timetable_delete'),

    # Classroom & Results
    path('admin-panel/assignments/', classroom_views.assignments_list, name='admin_assignments'),
    path('admin-panel/study-materials/', classroom_views.study_materials_list, name='admin_study_materials'),
    path('admin-panel/results/', classroom_views.results_view, name='admin_results'),
    path('admin-panel/results/save/', classroom_views.result_save, name='admin_result_save'),
    path('admin-panel/results/exam/add/', classroom_views.admin_exam_add, name='admin_exam_add'),

    # Services
    path('admin-panel/leaves/', service_views.leaves_list, name='admin_leaves'),
    path('admin-panel/leaves/<int:pk>/review/', service_views.leave_review, name='admin_leave_review'),
    path('admin-panel/notices/', service_views.notices_list, name='admin_notices'),
    path('admin-panel/notices/<int:pk>/delete/', service_views.notice_delete, name='admin_notice_delete'),
    path('admin-panel/fees/', service_views.fees_list, name='admin_fees'),
    path('admin-panel/fees/<int:pk>/mark-paid/', service_views.admin_fee_mark_paid, name='admin_fee_mark_paid'),
    path('admin-panel/complaints/', service_views.complaints_list, name='admin_complaints'),
    path('admin-panel/complaints/<int:pk>/respond/', service_views.admin_complaint_respond, name='admin_complaint_respond'),

    # Reports & Settings
    path('admin-panel/reports/', dashboard_views.admin_reports, name='admin_reports'),
    path('admin-panel/settings/', dashboard_views.admin_settings, name='admin_settings'),

    # =========================================================================
    # TEACHER PORTAL ROUTES
    # =========================================================================
    path('teacher/dashboard/', dashboard_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/profile/', account_views.teacher_profile_view, name='teacher_profile'),
    path('teacher/classes/', classroom_views.timetable_view, name='teacher_classes'),
    path('teacher/students/', account_views.teacher_students, name='teacher_students'),
    path('teacher/attendance/', attendance_views.teacher_attendance, name='teacher_attendance'),
    path('teacher/assignments/', classroom_views.assignments_list, name='teacher_assignments'),
    path('teacher/assignments/create/', classroom_views.teacher_assignment_create, name='teacher_assignment_create'),
    path('teacher/assignments/<int:pk>/edit/', classroom_views.teacher_assignment_edit, name='teacher_assignment_edit'),
    path('teacher/assignments/<int:pk>/delete/', classroom_views.teacher_assignment_delete, name='teacher_assignment_delete'),
    path('teacher/assignments/<int:pk>/submissions/', classroom_views.assignment_submissions, name='assignment_submissions'),
    path('teacher/submissions/', classroom_views.teacher_submissions_all, name='teacher_submissions'),
    path('teacher/submissions/<int:pk>/grade/', classroom_views.submission_grade, name='submission_grade'),
    path('teacher/study-materials/', classroom_views.study_materials_list, name='teacher_study_materials'),
    path('teacher/study-materials/<int:pk>/delete/', classroom_views.study_material_delete, name='teacher_study_material_delete'),
    path('teacher/results/', classroom_views.results_view, name='teacher_results'),
    path('teacher/results/save/', classroom_views.result_save, name='teacher_result_save'),
    path('teacher/leaves/', service_views.leaves_list, name='teacher_leaves'),
    path('teacher/leaves/<int:pk>/review/', service_views.leave_review, name='teacher_leave_review'),
    path('teacher/notices/', service_views.notices_list, name='teacher_notices'),

    # =========================================================================
    # STUDENT PORTAL ROUTES
    # =========================================================================
    path('student/dashboard/', dashboard_views.student_dashboard, name='student_dashboard'),
    path('student/profile/', account_views.student_profile_view, name='student_profile'),
    path('student/attendance/', attendance_views.student_attendance, name='student_attendance'),
    path('student/timetable/', classroom_views.timetable_view, name='student_timetable'),
    path('student/assignments/', classroom_views.assignments_list, name='student_assignments'),
    path('student/assignments/<int:pk>/submit/', classroom_views.student_assignment_submit, name='student_assignment_submit'),
    path('student/results/', classroom_views.results_view, name='student_results'),
    path('student/leave/', service_views.leaves_list, name='student_leave'),
    path('student/notices/', service_views.notices_list, name='student_notices'),
    path('student/study-materials/', classroom_views.study_materials_list, name='student_study_materials'),
    path('student/fees/', service_views.fees_list, name='student_fees'),
    path('student/complaints/', service_views.complaints_list, name='student_complaints'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
