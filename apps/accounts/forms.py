import random
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, AcademicSession


class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            # Check if input is email or username
            user_obj = None
            if '@' in username_or_email:
                try:
                    user_match = User.objects.get(email__iexact=username_or_email)
                    user_obj = authenticate(username=user_match.username, password=password)
                except User.DoesNotExist:
                    user_obj = None
            else:
                user_obj = authenticate(username=username_or_email, password=password)

            if not user_obj:
                raise ValidationError("Invalid username/email or password. Please verify and try again.")
            if not user_obj.is_active:
                raise ValidationError("Your account is currently disabled. Please contact the administrator.")

            cleaned_data['user'] = user_obj

        return cleaned_data


class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Enter your email address'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Choose a username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Create a password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control py-2 px-3 rounded-3',
            'placeholder': 'Confirm your password'
        })
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        initial=User.ROLE_STUDENT
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'username', 'password', 'confirm_password', 'role']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError({'confirm_password': "Passwords do not match."})

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            # Automatically create respective profile
            if user.is_student_user:
                # Generate unique student ID (e.g. STU2026xxxx)
                random_suffix = random.randint(1000, 9999)
                student_id = f"STU{user.id:03d}{random_suffix}"
                StudentProfile.objects.create(user=user, student_id=student_id)
            elif user.is_teacher_user:
                random_suffix = random.randint(100, 999)
                emp_id = f"FAC{user.id:03d}{random_suffix}"
                TeacherProfile.objects.create(user=user, employee_id=emp_id)

        return user


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = StudentProfile
        fields = [
            'gender', 'date_of_birth', 'blood_group', 'address',
            'guardian_name', 'guardian_phone', 'emergency_contact'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. O+'}),
            'address': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.phone = self.cleaned_data.get('phone')
        if self.cleaned_data.get('avatar'):
            user.avatar = self.cleaned_data.get('avatar')
        user.save()
        return profile


class TeacherProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = TeacherProfile
        fields = ['designation', 'qualification', 'office_room', 'address']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'office_room': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'address': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.phone = self.cleaned_data.get('phone')
        if self.cleaned_data.get('avatar'):
            user.avatar = self.cleaned_data.get('avatar')
        user.save()
        return profile


class AdminStudentCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control rounded-3'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Default initial password'})
    )
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = StudentProfile
        fields = [
            'student_id', 'department', 'course', 'semester', 'batch_session',
            'gender', 'date_of_birth', 'address', 'guardian_name', 'guardian_phone'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. CS2025001'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'course': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'batch_session': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'gender': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 2}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
        }

    def clean_student_id(self):
        sid = self.cleaned_data.get('student_id')
        if StudentProfile.objects.filter(student_id__iexact=sid).exists():
            raise ValidationError("This Student ID already exists in the system.")
        return sid

    def clean_username(self):
        un = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=un).exists():
            raise ValidationError("This username is already taken.")
        return un

    def clean_email(self):
        em = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=em).exists():
            raise ValidationError("This email is already registered.")
        return em


class AdminTeacherCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control rounded-3'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Default password'})
    )
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = TeacherProfile
        fields = ['employee_id', 'department', 'designation', 'qualification', 'joining_date', 'office_room', 'address']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. EMP202501'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'designation': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'office_room': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'address': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 2}),
        }

    def clean_employee_id(self):
        eid = self.cleaned_data.get('employee_id')
        if TeacherProfile.objects.filter(employee_id__iexact=eid).exists():
            raise ValidationError("This Employee ID already exists.")
        return eid

    def clean_username(self):
        un = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=un).exists():
            raise ValidationError("This username is already taken.")
        return un

    def clean_email(self):
        em = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=em).exists():
            raise ValidationError("This email is already registered.")
        return em
