from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from .models import Course, Exam, Choice, Question
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})

class RegisterForm(UserCreationForm):
    USER_TYPE_CHOICES =[('', '*Select')] + [(group.name, group.name) for group in Group.objects.all()]
    # use the list as the choices for the user_type field
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='User Type', required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", 'user_type',"email", "password1", "password2"]

class CourseForm(forms.ModelForm):
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    class Meta:
        model = Course
        fields = ['name', 'description']

class ExamForm(forms.ModelForm):
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    
    # New field for the type of the exam
    exam_type = forms.ChoiceField(choices=Exam.EXAM_TYPES, required=True)
    duration = forms.DurationField(required=False)
    class Meta:
        model = Exam
        fields = ['name', 'description', 'exam_type']
        
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'explanation_text', 'explanation_image', 'explanation_video']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("There is no user registered with the specified email address!")
        return email