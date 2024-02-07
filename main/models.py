import datetime
from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

Group.objects.get_or_create(name='Teacher')
Group.objects.get_or_create(name='Student')


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return self.name

class Exam(models.Model):
    EXAM_TYPES = [
        ('Quiz', 'Quiz'),
        ('Exam', 'Exam'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    created_at = models.DateTimeField(default=timezone.now)
    duration = models.DurationField(null=True, blank=True)
    # New field for the type of the exam
    exam_type = models.CharField(max_length=4, choices=EXAM_TYPES, default='Exam')
    
    exam_hash = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return self.name

class Question(models.Model):
    question_text = models.TextField(blank=True, null=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    explanation_text = models.TextField(blank=True, null=True)
    explanation_image = models.ImageField(upload_to='explanations/', blank=True, null=True)
    explanation_video = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.question_text

    @property
    def correct_answer(self):
        return self.choices.filter(is_correct=True).first()

class Choice(models.Model):
    choice_text = models.TextField(blank=True, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text
    
class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, blank=True, null=True)
    


class AnswerInterval(models.Model):
    useranswer = models.ForeignKey(UserAnswer, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)


class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField(null=True, blank=True)
    unanswered_questions = models.IntegerField(null=True, blank=True)
    incorrect_answers = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(default=timezone.now)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    submitted = models.BooleanField(default=False)
    time_up = models.BooleanField(default=False)
