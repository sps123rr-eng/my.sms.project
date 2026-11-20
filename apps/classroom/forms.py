from django import forms
from .models import Timetable, Assignment, Submission, StudyMaterial, Examination, Result
from apps.academics.models import Subject


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['subject', 'teacher', 'day_of_week', 'start_time', 'end_time', 'room_number', 'section']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'teacher': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control rounded-3', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control rounded-3', 'type': 'time'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Room 101 / Lab B'}),
            'section': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. A'}),
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'subject', 'due_date', 'max_marks', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Network Routing Algorithms'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Detailed instructions for students...'}),
            'subject': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 10, 'max': 500}),
            'attachment': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['attachment', 'notes']
        widgets = {
            'attachment': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Optional submission notes, git links, or remarks...'}),
        }


class SubmissionGradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['marks_obtained', 'feedback', 'status']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '0.5'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Feedback for the student'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'subject', 'file', 'file_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Database Normalization Notes'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 2}),
            'subject': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'file': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
            'file_type': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }


class ExaminationForm(forms.ModelForm):
    class Meta:
        model = Examination
        fields = ['name', 'exam_type', 'session', 'semester', 'start_date', 'end_date', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Mid Semester Exam 2025'}),
            'exam_type': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'session': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'start_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['examination', 'student', 'subject', 'internal_marks', 'end_sem_marks', 'max_marks', 'remarks']
        widgets = {
            'examination': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'student': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'subject': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'internal_marks': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '0.5'}),
            'end_sem_marks': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '0.5'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '1'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Excellent / Passed'}),
        }
