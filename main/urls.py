from django.urls import path
from . import views
from django.urls import include
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from .views import CustomPasswordResetView

urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.home, name='home'),
    path('', include('django.contrib.auth.urls')),
    path('sign-up', views.sign_up, name='sign_up'),
    path('login-user', views.login_user, name='login_user'),
    path('logout-user', views.logout_view, name='logout_view'),

    path('teacher-home', login_required(views.teacher_home), name='teacher_home'),  # Protected view
    path('teacher-course', login_required(views.create_course), name='teacher_course'),  # Protected view

    path('course/<int:course_id>/teacher-exam', login_required(views.create_exam), name='teacher_exam'),  # Protected view
    path('course/<int:course_id>/teacher-exam-list', login_required(views.exam_list), name='teacher_exam_list'),  # Protected view
    path('search-teacher-exam-list', login_required(views.search_exam_list), name='search_teacher_exam_list'),  # Protected view


    path('<int:id>/exam-delete/', login_required(views.exam_delete), name='exam_delete'),  # Protected view
    path('<int:id>/exam-edit/', login_required(views.exam_edit), name='exam_edit'),  # Protected view

    path('course-list', login_required(views.course_list), name='course_list'),  # Protected view
    path('<int:id>/', login_required(views.course_detail), name='course_detail'),  # Protected view
    path('<int:id>/course-delete/', login_required(views.course_delete), name='course_delete'),  # Protected view
    path('<int:id>/course-edit/', login_required(views.course_edit), name='course_edit'),  # Protected view
    path('question/<int:question_id>/delete/', login_required(views.delete_question), name='delete_question'),  # Protected view
    path('teacher-exam/<int:exam_id>/create-question/', login_required(views.create_question), name='create_question'),  # Protected view
    path('question-list/<int:exam_id>/', login_required(views.question_list), name='question_list'),  # Protected view

    path('edit-exam/<int:exam_id>/edit_question/<int:question_id>/', login_required(views.edit_question), name='edit_question'),  # Protected view
    
    path('delete_choice/<int:choice_id>/', login_required(views.delete_choice), name='delete_choice'),  # Protected view
    path('teacher/search-student/', login_required(views.teacher_search_student), name='teacher_search_student'),  # Protected view
    path('teacher/student-exams/<int:student_id>/', login_required(views.teacher_student_exams), name='teacher_student_exams'),  # Protected view
    path('teacher/exam-result/<int:exam_result_id>/', login_required(views.teacher_view_exam_result), name='teacher_view_exam_result'),  # Protected view


    path('answer-exam/<int:exam_id>/<int:page_number>/', login_required(views.answer_exam), name='answer_exam'),  # Protected view
    path('answer-exam/<int:exam_id>/', login_required(views.answer_exam), name='answer_exam'),
    path('results/<int:exam_result_id>/', login_required(views.results), name='results'),  # Protected view
    path('exam-search/',  login_required(views.student_search_exam), name='student_search_exam'),
    path('exam-results/<int:exam_id>/', login_required(views.exam_results), name='exam_results'),  # Protected view
    path('student-view-results/<int:exam_result_id>/', login_required(views.student_view_results), name='student_view_results'),
    path('save-answer/', login_required(views.save_answer), name='save_answer'),
    path('remove-unanswered-question/', login_required(views.remove_unanswered_question), name='remove_unanswered_question'),

    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),

]   
