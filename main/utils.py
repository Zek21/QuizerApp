from django.http import request
from django.contrib.auth.models import Group

def get_user_group_context(request):
    context = {
        'is_teacher': request.user.groups.filter(name='Teacher').exists(),
        'is_student': request.user.groups.filter(name='Student').exists(),
    }
    return context