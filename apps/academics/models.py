from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    head_of_department = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    duration_years = models.PositiveSmallIntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(6)])
    total_semesters = models.PositiveSmallIntegerField(default=8, validators=[MinValueValidator(1), MaxValueValidator(12)])
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class AcademicSession(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. "2024 - 2025" or "2024-2028 Batch"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one session is marked current
            AcademicSession.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        current_badge = " (Current)" if self.is_current else ""
        return f"{self.name}{current_badge}"


class Subject(models.Model):
    TYPE_THEORY = 'THEORY'
    TYPE_PRACTICAL = 'PRACTICAL'
    TYPE_CHOICES = [
        (TYPE_THEORY, 'Theory'),
        (TYPE_PRACTICAL, 'Practical / Lab'),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    semester = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    credits = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(10)])
    subject_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_THEORY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'semester', 'code']

    def __str__(self):
        return f"{self.code} - {self.name} (Sem {self.semester})"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('DROPPED', 'Dropped'),
    ]

    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    enrollment_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-enrollment_date']
        constraints = [
            models.UniqueConstraint(fields=['student', 'session', 'semester'], name='unique_student_session_semester')
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} (Sem {self.semester})"


class TeachingAssignment(models.Model):
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, related_name='teaching_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teaching_assignments')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='teaching_assignments')
    section = models.CharField(max_length=10, default='A')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['teacher', 'subject']
        constraints = [
            models.UniqueConstraint(fields=['teacher', 'subject', 'session', 'section'], name='unique_teacher_subject_session_section')
        ]

    def __str__(self):
        return f"{self.teacher.user.display_name} -> {self.subject.code} (Sec {self.section})"
