from django.contrib.auth.models import User
from django.db import models 

# Учитель
class Teacher(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    patronymic = models.CharField(max_length=50, null=True, blank=True)

# Номер курса
class Course(models.Model):
    CourseNumber = models.PositiveSmallIntegerField(unique=True)

# Тип занятия
class TypeOfLesson(models.Model):
    TypeName = models.CharField(max_length=50)

# Время занятия
class TimeInterval(models.Model):
    Interval = models.CharField(max_length=12)

# Группа
class Group(models.Model):
    Course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)
    GroupNumber = models.CharField(max_length=4)
    NumberOfStudents = models.PositiveSmallIntegerField()

# Занятие
class Lesson(models.Model):
    Date = models.DateField()
    TimeIntervals = models.ManyToManyField(TimeInterval)
    Groups = models.ManyToManyField(Group)
    TypeOfLesson = models.ForeignKey(TypeOfLesson, on_delete=models.SET_NULL, blank=True, null=True)
    RealCountOfStudents = models.PositiveSmallIntegerField(blank=True, null=True)
    Teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class ScheduleLesson(models.Model):
    DateStart = models.DateField()
    DateFinish = models.DateField()
    DayOfWeek = models.CharField(max_length=20)
    Week = models.PositiveSmallIntegerField()
    TimeIntervals = models.ManyToManyField(TimeInterval)
    Groups = models.ManyToManyField(Group)
    TypeOfLesson = models.ForeignKey(TypeOfLesson, on_delete=models.SET_NULL, blank=True, null=True)
    Teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    LessonName = models.TextField()




