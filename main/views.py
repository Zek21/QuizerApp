import datetime
import uuid
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, render, redirect
from django.db import models
from django.db.models import Q
from django.db.models import Sum, ExpressionWrapper, DurationField
from django.contrib.auth.decorators import login_required
from main.models import Course, Exam, Choice, Question, ExamResult, UserAnswer, AnswerInterval
from .forms import RegisterForm, LoginForm, CourseForm, ExamForm, QuestionForm, ChoiceForm, CustomPasswordResetForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import Group, User
from django.utils import timezone
from .utils import get_user_group_context
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from uuid import UUID
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import logging
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = '/password-reset-done/'


logger = logging.getLogger(__name__)
# Create your views here.
def home(request):
    context = get_user_group_context(request)
    return render(request, 'main/home.html', context)

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_user = authenticate(request, username=user.username, password=form.cleaned_data['password'])
            if auth_user is not None:
                login(request, auth_user)
                messages.success(request, 'You are now logged in.')
                
                # Set session expiry here
                if user.groups.filter(name='Teacher').exists():
                    request.session.set_expiry(3600)  # 1 hour for teachers
                elif user.groups.filter(name='Student').exists():
                    request.session.set_expiry(3600)  # 1 hour for students
                else:
                    request.session.set_expiry(None)  # none minutes for others

                # Check if 'next' exists in the session and redirect to it
                next_url = request.session.get('next', None)
                if next_url:
                    del request.session['next']  # Remove 'next' from session
                    return redirect(next_url)

                return redirect(reverse('home'))
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already registered. Please contact the admin to reset the password')
            else:
                user = form.save()
                user_type = form.cleaned_data['user_type']
                group = Group.objects.get(name=user_type)
                user.groups.add(group)
                messages.success(request, 'Your account has been created! You are now logged in.')
                login(request, user)
                return redirect('/home')
        else:   
            messages.error(request, 'Error with your registration! Please try again.')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        if 'start_time' in request.session:
            del request.session['start_time']
        logout(request)
        messages.error(request, 'You have been logged out.')
        return redirect(reverse('home'))
    else:
        return redirect(reverse('login_user'))


def teacher_home(request):
    context = get_user_group_context(request)
    return render(request, 'teacher/teacher_home.html', context)


@login_required
def create_course(request):
    if request.user.groups.filter(name='Teacher').exists():
        if request.method == 'POST':
            form = CourseForm(request.POST)
            if form.is_valid():
                course = form.save(commit=False)
                course.teacher = request.user
                course.save()
                course_name = course.name
                messages.error(request, f'You have successfully created the course {course_name}.')
                return redirect('course_list')
        else:
            form = CourseForm()
        return render(request, 'teacher/create_course.html', {'form': form})
    else:
        messages.error('Error')
        return redirect('home')

@login_required    
def course_delete(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def course_edit(request, id):
    course = get_object_or_404(Course, id=id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'You have successfully updated the course {course.name}.')
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'teacher/course_edit.html', {'form': form})
    
@login_required
def course_list(request):
    # Get the search query from the user.
    search_query = request.GET.get('search', '')

    # Filter the list of courses based on the search query and the current user.
    courses = Course.objects.filter(
        Q(name__icontains=search_query) | Q(description__icontains=search_query),
        teacher=request.user  # Only include courses created by the current user.
    )

    # Get the number of rows to display per page from the user.
    per_page = request.GET.get('per_page', 10)

    pagination = Paginator(courses, per_page=per_page)

    # Get the current page.
    course_page = request.GET.get('course_page')

    # Get the courses for the current page.
    try:
        courses_on_page = pagination.page(course_page)
    except PageNotAnInteger:
        # If course_page is not an integer, show the first page.
        courses_on_page = pagination.page(1)
    except EmptyPage:
        # If course_page is out of range, show the last page.
        courses_on_page = pagination.page(pagination.num_pages)

    context = {
        
        'courses': courses_on_page,
        'num_pages': pagination.num_pages,
        'search_query': search_query,
        'per_page': per_page,
    }

    return render(request, 'teacher/course_list.html', context)
@login_required
def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    context = {'course': course}
    return render(request, 'teacher_exam_list', context)

@login_required
def create_exam(request, course_id):
    if request.user.groups.filter(name='Teacher').exists():
        course = get_object_or_404(Course, id=course_id)
        if request.method == 'POST':
            form = ExamForm(request.POST)
            if form.is_valid():
                # Get the duration fields from the form
                hours = int(request.POST.get('hours', 0) or 0)
                minutes = int(request.POST.get('minutes', 0) or 0)
                seconds = int(request.POST.get('seconds', 0) or 0)

                # Calculate the total duration in seconds
                total_seconds = hours * 3600 + minutes * 60 + seconds

                # Create a new Exam object with the form data and the calculated duration
                exam = form.save(commit=False)
                exam.course = course
                exam.duration = datetime.timedelta(seconds=total_seconds)
                exam.save()

                messages.error(request, f'You have successfully created the exam {exam.name}.')
                return redirect('teacher_exam_list', course_id=course_id)
        else:
            form = ExamForm()
        return render(request, 'teacher/create_exam.html', {'form': form, 'course': course})
    else:
        messages.error('Error')
        return redirect('teacher_exam_list')


@login_required
def exam_list(request, course_id):
     
    # Get the search query from the user.
    
    search_query = request.GET.get('search', '')

    # Filter the list of exams based on the search query and the given course_id.
    exams = Exam.objects.filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(exam_type__icontains=search_query) |
        Q(course__name__icontains=search_query)
    )

    # Get the number of rows to display per page from the user.
    per_page = request.GET.get('per_page', 10)

    pagination = Paginator(exams, per_page=per_page)

    # Get the current page.
    exam_page = request.GET.get('exam_page')

    # Get the exams for the current page.
    try:
        exams_on_page = pagination.page(exam_page)
    except PageNotAnInteger:
        # If exam_page is not an integer, show the first page.
        exams_on_page = pagination.page(1)
    except EmptyPage:
        # If exam_page is out of range, show the last page.
        exams_on_page = pagination.page(pagination.num_pages)
    course = get_object_or_404(Course, id=course_id)
    context = {
        'course': course,
        'exams': exams_on_page,
        'num_pages': pagination.num_pages,
        'search_query': search_query,
        'per_page': per_page,
    }

    return render(request, 'teacher/exam_list.html', context)


@login_required
def search_exam_list(request):
     

    # Get the search query from the user.
    
    search_query = request.GET.get('search', '')
    current_user = request.user
    # Filter the list of exams based on the search query and the given course_id.
    exams = Exam.objects.filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(exam_type__icontains=search_query) |
        Q(course__name__icontains=search_query),
        course__teacher=current_user
    )

    # Get the number of rows to display per page from the user.
    per_page = request.GET.get('per_page', 10)

    pagination = Paginator(exams, per_page=per_page)

    # Get the current page.
    exam_page = request.GET.get('exam_page')

    # Get the exams for the current page.
    try:
        exams_on_page = pagination.page(exam_page)
    except PageNotAnInteger:
        # If exam_page is not an integer, show the first page.
        exams_on_page = pagination.page(1)
    except EmptyPage:
        # If exam_page is out of range, show the last page.
        exams_on_page = pagination.page(pagination.num_pages)
    course = get_object_or_404(Course)
    context = {
        'course': course,
        'exams': exams_on_page,
        'num_pages': pagination.num_pages,
        'search_query': search_query,
        'per_page': per_page,
    }

    return render(request, 'teacher/teacher_search_exam.html', context)



@login_required
def exam_delete(request, id):
    exam = get_object_or_404(Exam, id=id)
    exam.delete()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def exam_edit(request, id):
    exam = get_object_or_404(Exam, id=id)
    course_id = exam.course.id  # Get the course_id from the exam

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            # Get the duration fields from the form
            hours = int(request.POST.get('hours', 0) or 0)
            minutes = int(request.POST.get('minutes', 0) or 0)
            seconds = int(request.POST.get('seconds', 0) or 0)

            # Calculate the total duration in seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds

            # Update the Exam object with the form data and the calculated duration
            exam = form.save(commit=False)
            exam.duration = datetime.timedelta(seconds=total_seconds)
            exam.save()

            messages.success(request, f'You have successfully updated the exam {exam.name}.')
            return redirect('teacher_exam_list', course_id=course_id)
    else:
        form = ExamForm(instance=exam)

        # Calculate hours, minutes and seconds from the duration
        total_seconds = exam.duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int((total_seconds % 3600) % 60)

    return render(request, 'teacher/edit_exam.html', {'form': form, 'course_id': course_id, 'hours': hours, 'minutes': minutes, 'seconds': seconds})


@login_required
def create_question(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.exam = exam
            question.save()
            # Handle creation of choices
            correct_choices = 0  # Initialize counter for correct choices
            for i, choice_text in enumerate(request.POST.getlist('choice_text[]')):
                is_correct_value = request.POST.get(f'is_correct_{i}', '') == 'on'
                if is_correct_value:
                    correct_choices += 1  # Increment counter if choice is correct
                # Create new choice
                choice_form = ChoiceForm({'choice_text': choice_text, 'is_correct': is_correct_value})
                if choice_form.is_valid():
                    choice = choice_form.save(commit=False)
                    choice.question = question
                    choice.save()
            if correct_choices == 0:  # If no choices are marked as correct
                messages.error(request, 'Error: At least one choice must be marked as correct.')
                return redirect('create_question', exam_id=exam_id)  # Redirect back to the form
            return redirect('question_list', exam_id=exam_id)
    else:
        question_form = QuestionForm()
    return render(request, 'teacher/create_question.html', {'form': question_form, 'exam': exam})


@login_required   
def question_list(request, exam_id):
    search_query = request.GET.get('search', '')
    per_page = int(request.GET.get('per_page', 10))
    exam = Exam.objects.get(pk=exam_id)
    questions = Question.objects.filter(exam_id=exam_id, question_text__icontains=search_query)
    paginator = Paginator(questions, per_page)
    page_number = request.GET.get('question_page')
    questions = paginator.get_page(page_number)
    context = {
        'questions': questions,
        'search_query': search_query,
        'per_page': per_page,
        'exam_id': exam_id,
        'exam_name': exam.name,
        'course_id': exam.course.id,
    }
    return render(request, 'teacher/question_list.html', context)
    

@login_required
def answer_exam(request, exam_id, page_number=1):
    exam = get_object_or_404(Exam, pk=exam_id)
    exam_result = ExamResult.objects.filter(user=request.user, exam=exam).first()
    if exam_result:
        return redirect('student_view_results', exam_result_id=exam_result.pk)

    questions = exam.questions.all()
    paginator = Paginator(questions, 1)
    page_obj = paginator.get_page(page_number)
    
    if page_obj:
        question = page_obj.object_list[0]
        user_answer = UserAnswer.objects.filter(user=request.user, question=question).first()
        intervals = AnswerInterval.objects.filter(useranswer=user_answer)
        total_time_previous_sessions = sum((interval.end_time - interval.start_time).total_seconds() for interval in intervals if interval.start_time and interval.end_time)
    else:
        question = None
        user_answer = None
        total_time_previous_sessions = 0

    start_time = request.session.get('start_time')
    if not start_time:
        start_time = timezone.now()
        request.session['start_time'] = start_time.isoformat()
    else:
        start_time = datetime.datetime.fromisoformat(start_time)

    elapsed_time = (timezone.now() - start_time).total_seconds()
    remaining_time = max(0, exam.duration.total_seconds() - elapsed_time)

    # Get all question IDs for the current exam
    all_question_ids = set(question.id for question in questions)

    # Get answered question IDs for the current user and exam
    answered_question_ids = set(UserAnswer.objects.filter(user=request.user, question__in=questions).exclude(choice__isnull=True).values_list('question__id', flat=True))

    # Get unanswered question IDs by subtracting the sets
    unanswered_question_ids = list(all_question_ids - answered_question_ids)

    # Store unanswered_question_ids in the session
    request.session['unanswered_question_ids'] = unanswered_question_ids
    # Add this line to reload the session data
    request.session.modified = True
    if request.method == 'POST':
        answer = request.POST.get(f'question_{question.id}')
    
        choice = Choice.objects.filter(pk=answer).first() if answer else None
        user_answer, created = UserAnswer.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={'choice': choice} if choice else {}
        )
        
        latest_interval = AnswerInterval.objects.filter(useranswer=user_answer).latest('start_time')
        latest_interval.end_time = timezone.now()
        latest_interval.save()

        if 'next' in request.POST and page_obj.has_next():
            return redirect('answer_exam', exam_id=exam_id, page_number=page_obj.next_page_number())
        
        elif 'back' in request.POST and page_obj.has_previous():
            return redirect('answer_exam', exam_id=exam_id, page_number=page_obj.previous_page_number())
        
        elif 'submit' in request.POST or int(request.POST.get('remaining_time', 0)) <= 0:
            score = 0
            incorrect_answers = 0
            unanswered_questions = 0
            total_questions = paginator.count
            for question in questions:
                user_answer = UserAnswer.objects.filter(user=request.user, question=question).first()
                if user_answer and user_answer.choice:
                    if user_answer.choice.is_correct:
                        score += 1
                    else:
                        incorrect_answers += 1
                else:
                    unanswered_questions += 1

            percentage = round((score / total_questions) * 100, 2)
            
            end_time = timezone.now()

            exam_result = ExamResult.objects.create(
                exam=exam,
                user=request.user,
                score=score,
                total_questions=total_questions,
                percentage=percentage,
                unanswered_questions=unanswered_questions,
                incorrect_answers=incorrect_answers,
                answered_at=end_time,
                start_time=start_time,
                end_time=end_time,
                submitted=True  
            )
            return redirect('student_view_results', exam_result_id=exam_result.pk)
        
    else:
        user_answer, created = UserAnswer.objects.get_or_create(
            user=request.user,
            question=question
        )
        AnswerInterval.objects.create(
            useranswer=user_answer,
            start_time=timezone.now(),
            end_time=None
        )
    
    # Calculate the page number of the first unanswered question
    first_unanswered_question_id = unanswered_question_ids[0] if unanswered_question_ids else None
    first_unanswered_page_number = None
    if first_unanswered_question_id:
        for i, question in enumerate(questions, start=1):
            if question.id == first_unanswered_question_id:
                first_unanswered_page_number = (i - 1) // paginator.per_page + 1
                break
    
    # If there are no unanswered questions, set first_unanswered_page_number to the last page
    if first_unanswered_page_number is None:
        first_unanswered_page_number = paginator.num_pages
   
    context = {
        'exam': exam,
        'page_obj': page_obj,
        'user_answer': user_answer,
        'total_time_previous_sessions': total_time_previous_sessions,
        'remaining_time': remaining_time,
        'unanswered_question_ids': unanswered_question_ids, # Add this line to pass the list to the template.
        'first_unanswered_page_number': first_unanswered_page_number,
    }

    return render(request, 'student/answer_exam.html', context)

@login_required
def save_answer(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        choice_id = request.POST.get('choice_id')
        
        question = get_object_or_404(Question, pk=question_id)
        choice = get_object_or_404(Choice, pk=choice_id) if choice_id else None
        
        user_answer, created = UserAnswer.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={'choice': choice}
        )
        
        return JsonResponse({'status': 'success'})

@login_required
def remove_unanswered_question(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        
        # Remove question_id from unanswered_question_ids in the session
        unanswered_question_ids = request.session.get('unanswered_question_ids', [])
        if question_id in unanswered_question_ids:
            unanswered_question_ids.remove(question_id)
            request.session['unanswered_question_ids'] = unanswered_question_ids
        
        return JsonResponse({'status': 'success'})

@login_required
def results(request, exam_result_id):
    exam_result = get_object_or_404(ExamResult, pk=exam_result_id)
    student = exam_result.user
    course = exam_result.exam.course
    questions = exam_result.exam.questions.all()
    user_answers = []
    for question in questions:
        user_answer = UserAnswer.objects.filter(user=exam_result.user, question=question).first()
        user_answers.append((question, user_answer))
    
    # Calculate total time taken for the exam
    total_time = exam_result.end_time - exam_result.start_time

    context = {
        'exam_result': exam_result,
        'user_answers': user_answers,
        'student': student,
        'course': course,
        'total_time': total_time,  # Pass total_time to the context
    }
    
    return render(request, 'teacher/teacher_view_exam_result.html', context)


@login_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    exam_results = ExamResult.objects.filter(exam=exam)
    context = {'exam': exam, 'exam_results': exam_results}
    return render(request, 'teacher/exam_results.html', context)

@login_required
def student_view_results(request, exam_result_id):
    exam_result = get_object_or_404(ExamResult, pk=exam_result_id)
    student = exam_result.user
    course = exam_result.exam.course
    questions = exam_result.exam.questions.all()
    user_answers = []
    for question in questions:
        user_answer = UserAnswer.objects.filter(user=exam_result.user, question=question).first()
        user_answers.append((question, user_answer))

    context = {
        'exam_result': exam_result,
        'user_answers': user_answers,
        'student': student,
        'course': course,
    }
    
    return render(request, 'student/student_view_results.html', context)

@login_required
def edit_question(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES, instance=question)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.exam = exam
            question.save()
            # Handle deletion of choices
            for choice in question.choices.all():
                if f'delete_choice_{choice.id}' in request.POST:
                    choice.delete()
            # Handle updating and creation of choices
            correct_choices = 0  # Initialize counter for correct choices
            for i, choice_text in enumerate(request.POST.getlist('choice_text[]')):
                is_correct_value = request.POST.get(f'is_correct_{i}', '') == 'on'
                if is_correct_value:
                    correct_choices += 1  # Increment counter if choice is correct
                choice_id = request.POST.get(f'choice_id_{i}')
                if choice_id:
                    # Update existing choice
                    choice = Choice.objects.get(pk=choice_id)
                    choice.choice_text = choice_text
                    choice.is_correct = is_correct_value
                    choice.save()
                else:
                    # Create new choice
                    choice_form = ChoiceForm({'choice_text': choice_text, 'is_correct': is_correct_value})
                    if choice_form.is_valid():
                        choice = choice_form.save(commit=False)
                        choice.question = question
                        choice.save()
            if correct_choices == 0:  # If no choices are marked as correct
                messages.error(request, 'Error: At least one choice must be marked as correct.')
                return redirect('edit_question', exam_id=exam_id, question_id=question_id)  # Redirect back to the form
            return redirect('question_list', exam_id=exam_id)
    else:
        question_form = QuestionForm(instance=question)
    return render(request, 'teacher/edit_question.html', {'form': question_form, 'exam': exam})


@login_required
def delete_choice(request, choice_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        logger.info('Received AJAX request to delete choice')
        choice = get_object_or_404(Choice, pk=choice_id)
        choice.delete()
        logger.info(f'Deleted choice with ID {choice_id}')
        return JsonResponse({'success': True})
    else:
        logger.warning('Received non-AJAX request to delete choice')
        return JsonResponse({'success': False})

# View to search for a student
@login_required
def teacher_search_student(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        current_user = request.user
        students = User.objects.filter(username__icontains=search_query, groups__name='Student', examresult__exam__course__teacher=current_user)
        context = {'students': students}
        return render(request, 'teacher/teacher_search_student.html', context)

# View to display a student's exams
@login_required
def teacher_student_exams(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    exam_results = ExamResult.objects.filter(user=student)
    context = {'student': student, 'exam_results': exam_results}
    return render(request, 'teacher/teacher_student_exams.html', context)

# View to view the result of a specific exam
@login_required
def teacher_view_exam_result(request, exam_result_id):
    exam_result = get_object_or_404(ExamResult, pk=exam_result_id)
    student = exam_result.user
    course = exam_result.exam.course
    questions = exam_result.exam.questions.all()
    user_answers = []
    for question in questions:
        user_answer = UserAnswer.objects.filter(user=exam_result.user, question=question).first()
        
        # Calculate total time spent on this question in this session
        intervals = AnswerInterval.objects.filter(useranswer=user_answer)
        total_time_question = datetime.timedelta(seconds=sum((interval.end_time - interval.start_time).total_seconds() for interval in intervals if interval.start_time and interval.end_time))
        
        user_answers.append((question, user_answer, total_time_question))
    
    # Calculate total time taken for the exam
    total_time = exam_result.end_time - exam_result.start_time

    context = {
        'exam_result': exam_result,
        'user_answers': user_answers,
        'student': student,
        'course': course,
        'total_time': total_time,  # Pass total_time to the context
    }
    
    return render(request, 'teacher/teacher_view_exam_result.html', context)

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    exam_id = question.exam.id  # Get the exam_id associated with the deleted question
    question.delete()
    # Redirect to the 'question_list' view with the 'exam_id' parameter
    return redirect('question_list', exam_id=exam_id)

def student_search_exam(request):
    exams = []  # Initialize an empty list to store exam objects
    if request.method == 'GET' and 'search' in request.GET:
        exam_hash = request.GET.get('search', '')

        try:
            exam_uuid = uuid.UUID(exam_hash)
            exam = Exam.objects.get(exam_hash=exam_uuid)
            exams.append(exam)  # Add the exam to the list
        except (ValueError, Exam.DoesNotExist):
            messages.error(request, 'Exam not found. Please enter a valid code.')  # Add an error message

    return render(request, 'student/exam_search.html', {'exams': exams})