from django import forms
from .models import Department, Course, Subject, AcademicSession, Enrollment, TeachingAssignment


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_of_department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Computer Science & Engineering'}),
            'code': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. CSE'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Department overview'}),
            'head_of_department': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'department', 'duration_years', 'total_semesters', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Bachelor of Technology in CS'}),
            'code': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. BTECH-CS'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 6}),
            'total_semesters': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 2}),
        }


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. 2025-2026 Academic Year'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'course', 'semester', 'credits', 'subject_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Data Structures & Algorithms'}),
            'code': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. CS201'}),
            'course': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'credits': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 10}),
            'subject_type': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'session', 'semester', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'course': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'session': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'status': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ['teacher', 'subject', 'session', 'section']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'subject': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'session': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'section': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. A'}),
        }
