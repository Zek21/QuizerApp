from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .forms import RegisterForm
from .models import *


# define a function to get the groups of a user as a string
def get_user_groups(user):
    return ', '.join([group.name for group in user.groups.all()])



admin.site.register(Course)
admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(ExamResult)
admin.site.register(UserAnswer)
admin.site.register(AnswerInterval)
