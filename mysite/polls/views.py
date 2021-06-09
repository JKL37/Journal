from django.shortcuts import render, redirect, HttpResponse
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
import datetime
import os
import xlsxwriter
from io import BytesIO


#   Авторизация
def auth(request):
    if request.user.is_authenticated:
        return redirect("/journal")
    else:
        if request.method == "GET":
            return render(request, "polls/auth.html")
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
            try:
                django_user = User.objects.filter(username=username, is_active=True)[0]
            except:
                return render(request, "polls/auth.html", {"error": "В системе не зарегистрировано пользователя с таким логином"})
            else:
                if check_password(password, django_user.password):
                    auth_user = authenticate(username=username, password=password)
                    login(request, auth_user)
                    if request.user.is_staff == True:
                        return redirect("/admin/homepage")
                    else:
                        return redirect("/journal")
                else:
                    return render(request, "polls/auth.html", {"error": "Некорректный пароль для указанного пользователя"})


#   Строка для вывода группы в формате "курс-группа"
def fill_groups_str(lesson, flag):
    tmp_str = ""
    for group in lesson.Groups.all():
        if flag == "course-group":
            if group.Course.CourseNumber == 1:
                tmp_str += "I-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 2:
                tmp_str += "II-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 3:
                tmp_str += "III-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 4:
                tmp_str += "IV-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 5:
                tmp_str += "м I-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 6:
                tmp_str += "м II-" + group.GroupNumber + ", "
            elif group.Course.CourseNumber == 7:
                tmp_str += "асп-" + group.GroupNumber + ", "
        elif flag == "group":
            tmp_str += group.GroupNumber + ", "
    return tmp_str[:len(tmp_str) - 2]

#   Список занятий
def fill_lessons_table(request):
    teacher = Teacher.objects.filter(user_id=request.user)[0]
    teacher_lessons = Lesson.objects.filter(Teacher=teacher).order_by('Date')
    tmp_arr = []
    for lesson in teacher_lessons:
        tmp_arr.append({
            "id": lesson.id,
            "year": lesson.Date.year,
            "month": lesson.Date.month,
            "day": lesson.Date.day,
            "time": lesson.TimeIntervals.all()[0].Interval if len(lesson.TimeIntervals.all()) == 1 else lesson.TimeIntervals.all()[0].Interval.split("-")[0] + "-" + lesson.TimeIntervals.all()[len(lesson.TimeIntervals.all()) - 1].Interval.split("-")[1],
            "groups": fill_groups_str(lesson, "course-group"),
            "groups_number": fill_groups_str(lesson, "group"),
            "course": lesson.Groups.all()[0].Course.CourseNumber,
            "type": lesson.TypeOfLesson.TypeName,
            "real_students": lesson.RealCountOfStudents,
            "all_students": lesson.Groups.all()[0].NumberOfStudents if len(lesson.Groups.all()) == 1 else lesson.Groups.all()[0].NumberOfStudents + lesson.Groups.all()[1].NumberOfStudents
        })         
    return tmp_arr


#   Создание фильтра по дате
def create_date_dict(lessons):
    tmp_arr = {}
    for lesson in lessons:
        if str(lesson["year"]) in tmp_arr.keys():
            if str(lesson["month"]) in tmp_arr[str(lesson["year"])].keys():
                if str(lesson["day"]) in tmp_arr[str(lesson["year"])][str(lesson["month"])].keys():
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
                else:
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])] = []
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
            else:
                tmp_arr[str(lesson["year"])][str(lesson["month"])] = {}
                tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])] = []
                tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
        else:
            tmp_arr[str(lesson["year"])] = {}
            if str(lesson["month"]) in tmp_arr[str(lesson["year"])].keys():
                if str(lesson["day"]) in tmp_arr[str(lesson["year"])][str(lesson["month"])].keys():
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
                else:
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])] = []
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
            else:
                tmp_arr[str(lesson["year"])][str(lesson["month"])] = {}
                if str(lesson["day"]) in tmp_arr[str(lesson["year"])][str(lesson["month"])].keys():
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
                else:
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])] = []
                    tmp_arr[str(lesson["year"])][str(lesson["month"])][str(lesson["day"])].append(lesson)
    return tmp_arr


#   Подсчет академической нагрузки
def calculate_academic_hours(lessons):
    hours = {}
    for lesson in lessons:
        if str(lesson["year"]) + "." + str(lesson["month"]) + "." + str(lesson["day"]) not in hours.keys():
            hours[str(lesson["year"]) + "." + str(lesson["month"]) + "." + str(lesson["day"])] = 0
    to_return_hours = {}
    for date in hours.keys():
        if date.split(".")[0] in to_return_hours.keys():
            if date.split(".")[1] in to_return_hours[date.split(".")[0]].keys():
                if date.split(".")[2] in to_return_hours[date.split(".")[0]][date.split(".")[1]].keys():
                    pass
                else:
                    to_return_hours[date.split(".")[0]][date.split(".")[1]][date.split(".")[2]] = 0
            else:
                to_return_hours[date.split(".")[0]][date.split(".")[1]] = {}
                to_return_hours[date.split(".")[0]][date.split(".")[1]]["count"] = 0
                to_return_hours[date.split(".")[0]][date.split(".")[1]][date.split(".")[2]] = 0
        else:
            to_return_hours[date.split(".")[0]] = {}
            to_return_hours[date.split(".")[0]]["count"] = 0
            to_return_hours[date.split(".")[0]][date.split(".")[1]] = {}
            to_return_hours[date.split(".")[0]][date.split(".")[1]]["count"] = 0
            to_return_hours[date.split(".")[0]][date.split(".")[1]][date.split(".")[2]] = 0
    for year in to_return_hours.keys():
        if year == "count":
            continue
        for month in to_return_hours[year].keys():
            if month == "count":
                continue
            for day in to_return_hours[year][month].keys():
                for lesson in lessons:
                    if lesson["real_students"] == None:
                        continue
                    if str(lesson["year"]) == year and str(lesson["month"]) == month and str(lesson["day"]) == day:
                        delta = (datetime.datetime.strptime(lesson["time"].split("-")[1], '%H:%M') - datetime.datetime.strptime(lesson["time"].split("-")[0], '%H:%M')).total_seconds()/60
                        if int(delta) == 95:
                            to_return_hours[year][month][day] += 2
                            to_return_hours[year][month]["count"] += 2
                            to_return_hours[year]["count"] += 2
                        elif int(delta) == 205:
                            to_return_hours[year][month][day] += 4
                            to_return_hours[year][month]["count"] += 4
                            to_return_hours[year]["count"] += 4
    return to_return_hours

def fill_dicts(shedulelessons):
    interval_dict = {}
    group_dict = {}
    date_dict = {}
    for lesson in shedulelessons:
        interval_dict[lesson.id] = []
        group_dict[lesson.id] = ""
        date_dict[lesson.id] = {}
        if lesson.DateStart.month == 1:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " января " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 2:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " февраля " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 3:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " марта " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 4:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " апреля " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 5:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " мая " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 6:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " июня " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 7:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " июля " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 8:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " августа " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 9:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " сентября " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 10:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " октября " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 11:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " ноября " + str(lesson.DateStart.year)
        elif lesson.DateStart.month == 12:
            date_dict[lesson.id]["Start"] = str(lesson.DateStart.day) + " декабря " + str(lesson.DateStart.year)
        if lesson.DateFinish.month == 1:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " января " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 2:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " февраля " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 3:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " марта " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 4:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " апреля " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 5:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " мая " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 6:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " июня " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 7:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " июля " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 8:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " августа " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 9:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " сентября " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 10:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " октября " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 11:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " ноября " + str(lesson.DateFinish.year)
        elif lesson.DateFinish.month == 12:
            date_dict[lesson.id]["Finish"] = str(lesson.DateFinish.day) + " декабря " + str(lesson.DateFinish.year)
        for interval in lesson.TimeIntervals.all():
            interval_dict[lesson.id].append(interval.id)
        for group in lesson.Groups.all():
            group_dict[lesson.id] += str(group.Course.CourseNumber) + "-" + str(group.GroupNumber) + ", "
    return interval_dict, group_dict, date_dict

def schedule(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('/admin/homepage')
        if request.method == "GET":
            schedulelessons = ScheduleLesson.objects.filter(DateFinish__gte=datetime.datetime.now().date(), Teacher=Teacher.objects.filter(user_id=request.user)[0])
            intervals_dict, group_dict, date_dict = fill_dicts(schedulelessons)
            timeintervals = TimeInterval.objects.all()
            lessontypes = TypeOfLesson.objects.all()
            courses = Course.objects.all()
            if 8 >= datetime.datetime.now().month <= 12:
                min = str(datetime.datetime.now().year) + "-09-01"
                max = str(datetime.datetime.now().year + 1) + "-01-31"
            elif 2 >= datetime.datetime.now().month <= 6:
                min = str(datetime.datetime.now().year) + "-02-01"
                max = str(datetime.datetime.now().year + 1) + "-06-30"
            else:
                min = None
                max = None
            add_flag = False
            if 8 <= datetime.datetime.now().month <= 12:
                add_flag = True
            elif 1 <= datetime.datetime.now().month <= 5:
                add_flag = True
            daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
            if 9 <= datetime.datetime.now().month <= 12:
                semester = "1 Семестр"
                year = str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().year + 1)
            elif 2 <= datetime.datetime.now().month <= 5:
                semester = "2 Семестр"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif datetime.datetime.now().month == 1:
                semester = "Сессия 1 Семестра"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif datetime.datetime.now().month == 6:
                semester = "Сессия 2 Семестра"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif 7 <= datetime.datetime.now().month <= 8:
                semester = "Каникулы"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            return render(request, "polls/schedule.html", {"times": timeintervals, "semester": semester, "year": year, "daysofweek": daysofweek, "min": min, "max":max,
                        "lessontypes": lessontypes, "courses": courses, "lessons": schedulelessons, "intervals_dict": intervals_dict, "group_dict": group_dict, "date_dict": date_dict,
                        "add_flag": add_flag})
            
        elif request.method == "POST":
            tmp_arr = []
            count = 0
            for key in request.POST.keys():
                if "timecheck" in key:
                    tmp_arr.append(key[9:])
                    count += 1
            if count != 0:
                check_lessons_1 = ScheduleLesson.objects.filter(Teacher=Teacher.objects.filter(user_id=request.user)[0],
                                                                DayOfWeek=request.POST.get("DayOfWeek"),
                                                                Week=request.POST.get("Week"),
                                                                DateStart__lte=request.POST.get("LessonStartDate"),
                                                                DateFinish__gte=request.POST.get("LessonFinishDate"),
                                                                TimeIntervals__in=tmp_arr).distinct()
                check_lessons_2 = ScheduleLesson.objects.filter(Teacher=Teacher.objects.filter(user_id=request.user)[0],
                                                                DayOfWeek=request.POST.get("DayOfWeek"),
                                                                Week=request.POST.get("Week"),
                                                                DateStart__gte=request.POST.get("LessonStartDate"),
                                                                DateFinish__lte=request.POST.get("LessonFinishDate"),
                                                                TimeIntervals__in=tmp_arr).distinct()
                if len(check_lessons_1) != 0 or len(check_lessons_2) != 0:
                    schedulelessons = ScheduleLesson.objects.filter(DateFinish__gte=datetime.datetime.now().date(), Teacher=Teacher.objects.filter(user_id=request.user)[0])
                    intervals_dict, group_dict, date_dict = fill_dicts(schedulelessons)
                    timeintervals = TimeInterval.objects.all()
                    lessontypes = TypeOfLesson.objects.all()
                    courses = Course.objects.all()
                    daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
                    if 9 <= datetime.datetime.now().month <= 12:
                        semester = "1 Семестр"
                        year = str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().year + 1)
                    elif 2 <= datetime.datetime.now().month <= 5:
                        semester = "2 Семестр"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif datetime.datetime.now().month == 1:
                        semester = "Сессия 1 Семестра"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif datetime.datetime.now().month == 6:
                        semester = "Сессия 2 Семестра"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif 7 <= datetime.datetime.now().month <= 8:
                        semester = "Каникулы"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    if 8 >= datetime.datetime.now().month <= 12:
                        min = str(datetime.datetime.now().year) + "-09-01"
                        max = str(datetime.datetime.now().year + 1) + "-01-31"
                    elif 2 >= datetime.datetime.now().month <= 6:
                        min = str(datetime.datetime.now().year) + "-02-01"
                        max = str(datetime.datetime.now().year + 1) + "-06-30"
                    return render(request, "polls/schedule.html", {"times": timeintervals, "semestr": semester, "year": year, "daysofweek": daysofweek, "min": min, "max": max,
                                "lessontypes": lessontypes, "courses": courses, "lessons": schedulelessons, "intervals_dict": intervals_dict,
                                "group_dict": group_dict, "date_dict": date_dict, "error": "На выбранные время и дату уже назначено занятие"})
            new_lesson = ScheduleLesson.objects.create(DateStart=request.POST.get("LessonStartDate"),
                                                       DateFinish=request.POST.get("LessonFinishDate"),
                                                       DayOfWeek=request.POST.get("DayOfWeek"),
                                                       Week=request.POST.get("Week"),
                                                       TypeOfLesson=TypeOfLesson.objects.filter(id=request.POST.get("TypeOfLesson"))[0],
                                                       Teacher=Teacher.objects.filter(user_id=request.user)[0],
                                                       LessonName=request.POST.get("LessonName"))
            tmp_arr = []
            count = 0
            for key in request.POST.keys():
                if "timecheck" in key:
                    tmp_arr.append(key[9:])
                    count += 1
            if count == 0:
                schedulelessons = ScheduleLesson.objects.filter(DateFinish__gte=datetime.datetime.now().date(), Teacher=Teacher.objects.filter(user_id=request.user)[0])
                intervals_dict, group_dict, date_dict = fill_dicts(schedulelessons)
                timeintervals = TimeInterval.objects.all()
                lessontypes = TypeOfLesson.objects.all()
                courses = Course.objects.all()
                daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
                if 9 <= datetime.datetime.now().month <= 12:
                    semester = "1 Семестр"
                    year = str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().year + 1)
                elif 2 <= datetime.datetime.now().month <= 5:
                    semester = "2 Семестр"
                    year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                elif datetime.datetime.now().month == 1:
                    semester = "Сессия 1 Семестра"
                    year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                elif datetime.datetime.now().month == 6:
                    semester = "Сессия 2 Семестра"
                    year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                elif 7 <= datetime.datetime.now().month <= 8:
                    semester = "Каникулы"
                    year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                if 8 >= datetime.datetime.now().month <= 12:
                    min = str(datetime.datetime.now().year) + "-09-01"
                    max = str(datetime.datetime.now().year + 1) + "-01-31"
                elif 2 >= datetime.datetime.now().month <= 6:
                    min = str(datetime.datetime.now().year) + "-02-01"
                    max = str(datetime.datetime.now().year + 1) + "-06-30"
                return render(request, "polls/schedule.html", {"times": timeintervals, "semestr": semester, "year": year, "daysofweek": daysofweek, "min": min, "max": max,
                            "lessontypes": lessontypes, "courses": courses, "lessons": schedulelessons, "intervals_dict": intervals_dict,
                            "group_dict": group_dict, "date_dict": date_dict, "error": "Вы не выбрали ни одного времени проведения занятия"})
            for time_id in tmp_arr:
                new_lesson.TimeIntervals.add(int(time_id))
            db_corse = Course.objects.filter(id=request.POST.get("course"))[0]
            try:
                groups = request.POST.get("Groups").split(", ")
            except:
                groups = [request.POST.get("Groups")]
            group_arr = []
            for group in groups:
                try:
                    group_arr.append(Group.objects.filter(Course=db_corse, GroupNumber=group)[0])
                except:
                    schedulelessons = ScheduleLesson.objects.filter(DateFinish__gte=datetime.datetime.now().date(), Teacher=Teacher.objects.filter(user_id=request.user)[0])
                    intervals_dict, group_dict, date_dict = fill_dicts(schedulelessons)
                    timeintervals = TimeInterval.objects.all()
                    lessontypes = TypeOfLesson.objects.all()
                    courses = Course.objects.all()
                    daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
                    if 9 <= datetime.datetime.now().month <= 12:
                        semester = "1 Семестр"
                        year = str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().year + 1)
                    elif 2 <= datetime.datetime.now().month <= 5:
                        semester = "2 Семестр"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif datetime.datetime.now().month == 1:
                        semester = "Сессия 1 Семестра"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif datetime.datetime.now().month == 6:
                        semester = "Сессия 2 Семестра"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    elif 7 <= datetime.datetime.now().month <= 8:
                        semester = "Каникулы"
                        year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
                    if 8 >= datetime.datetime.now().month <= 12:
                        min = str(datetime.datetime.now().year) + "-09-01"
                        max = str(datetime.datetime.now().year + 1) + "-01-31"
                    elif 2 >= datetime.datetime.now().month <= 6:
                        min = str(datetime.datetime.now().year) + "-02-01"
                        max = str(datetime.datetime.now().year + 1) + "-06-30"
                    return render(request, "polls/schedule.html", {"times": timeintervals, "semestr": semester, "year": year, "daysofweek": daysofweek, "min": min, "max": max,
                                  "lessontypes": lessontypes, "courses": courses, "lessons": schedulelessons, "intervals_dict": intervals_dict,
                                  "group_dict": group_dict, "date_dict": date_dict,
                                  "error": "Группы " + str(db_corse.CourseNumber) + "-" + group + " не зарегистрировано в системе"})
            for group in group_arr:
                new_lesson.Groups.add(group.id)
            new_lesson.save()
            fill_lessons_by_new_schedule_lesson(new_lesson)
            schedulelessons = ScheduleLesson.objects.filter(DateFinish__gte=datetime.datetime.now().date(), Teacher=Teacher.objects.filter(user_id=request.user)[0])
            intervals_dict, group_dict, date_dict = fill_dicts(schedulelessons)
            timeintervals = TimeInterval.objects.all()
            lessontypes = TypeOfLesson.objects.all()
            courses = Course.objects.all()
            daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
            if 9 <= datetime.datetime.now().month <= 12:
                semester = "1 Семестр"
                year = str(datetime.datetime.now().year) + "-" + str(datetime.datetime.now().year + 1)
            elif 2 <= datetime.datetime.now().month <= 5:
                semester = "2 Семестр"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif datetime.datetime.now().month == 1:
                semester = "Сессия 1 Семестра"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif datetime.datetime.now().month == 6:
                semester = "Сессия 2 Семестра"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            elif 7 <= datetime.datetime.now().month <= 8:
                semester = "Каникулы"
                year = str(datetime.datetime.now().year - 1) + "-" + str(datetime.datetime.now().year)
            if 8 >= datetime.datetime.now().month <= 12:
                min = str(datetime.datetime.now().year) + "-09-01"
                max = str(datetime.datetime.now().year + 1) + "-01-31"
            elif 2 >= datetime.datetime.now().month <= 6:
                min = str(datetime.datetime.now().year) + "-02-01"
                max = str(datetime.datetime.now().year + 1) + "-06-30"
            return render(request, "polls/schedule.html", {"times": timeintervals, "semestr": semester, "year": year, "daysofweek": daysofweek, "min": min, "max": max,
                                  "lessontypes": lessontypes, "courses": courses, "lessons": schedulelessons, "intervals_dict": intervals_dict,
                                  "group_dict": group_dict, "date_dict": date_dict,
                                   "success": "Занятие успешно создано"})
    else:
        return redirect('/')

def fill_lessons_by_dates(datestart, datefinish):
    tmp_dict = {}
    timedelta_1_semestr = (datetime.datetime.strptime(datefinish, "%Y-%m-%d") - datetime.datetime.strptime(datestart, "%Y-%m-%d")).days
    flag = "week_1"
    tmp = 1000
    for i in range(0, timedelta_1_semestr + 1):
        current_date = datetime.datetime.strptime(datestart, "%Y-%m-%d") + datetime.timedelta(days=i)
        if current_date.isocalendar()[1] == tmp:
            continue
        else:
            if flag == "week_1":
                tmp_dict[current_date.isocalendar()[1]] = 1
                tmp = current_date.isocalendar()[1]
                flag = "week_2"
            elif flag == "week_2":
                tmp_dict[current_date.isocalendar()[1]] = 2
                tmp = current_date.isocalendar()[1]
                flag = "week_1"
    return tmp_dict

def fill_lessons_by_new_schedule_lesson(schedulelesson):
    year = datetime.datetime.now().year
    if 8 <= datetime.datetime.now().month <= 12:
        weeks = fill_lessons_by_dates(str(year) + "-09-01", str(year) + "-12-31")
    elif 1 <= datetime.datetime.now().month <= 5:
        weeks = fill_lessons_by_dates(str(year) + "-02-01", str(year) + "-05-31")
    timedelta = (datetime.datetime.strptime(schedulelesson.DateFinish, "%Y-%m-%d") - datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d")).days
    for i in range(0, timedelta + 1):
        if int(weeks[(datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).isocalendar()[1]]) == int(schedulelesson.Week):
            if (schedulelesson.DayOfWeek == "Понедельник" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 0) or\
                (schedulelesson.DayOfWeek == "Вторник" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 1) or\
                    (schedulelesson.DayOfWeek == "Среда" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 2) or\
                        (schedulelesson.DayOfWeek == "Четверг" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 3) or\
                            (schedulelesson.DayOfWeek == "Пятница" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 4) or\
                                (schedulelesson.DayOfWeek == "Суббота" and (datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)).weekday() == 5):
                new_lesson = Lesson.objects.create(Date=(datetime.datetime.strptime(schedulelesson.DateStart, "%Y-%m-%d") + datetime.timedelta(days=i)),
                                                   TypeOfLesson=schedulelesson.TypeOfLesson,
                                                   RealCountOfStudents=None,
                                                   Teacher=schedulelesson.Teacher)
                for interval in schedulelesson.TimeIntervals.all():
                    new_lesson.TimeIntervals.add(interval.id)
                for group in schedulelesson.Groups.all():
                    new_lesson.Groups.add(group.id)
                new_lesson.save()

#   Журнал преподавателя
def journal(request):
    if request.user.is_authenticated:
        if request.user.is_staff == True:
            return redirect('/admin/homepage')
        if request.method == "GET":
            lessons = fill_lessons_table(request)
            date_dict = create_date_dict(lessons)
            timeintervals = TimeInterval.objects.all()
            lessontypes = TypeOfLesson.objects.all()
            courses = Course.objects.all()
            hours = calculate_academic_hours(lessons)
            try:
                if request.GET.get("success") == "True":
                    return render(request, "polls/journal.html", {"table": date_dict, "times": timeintervals, "types": lessontypes,
                        "courses": courses, "hours": hours, "success": "Занятие успешно создано"})
                else:
                    return render(request, "polls/journal.html", {"table": date_dict, "times": timeintervals, "types": lessontypes,
                        "courses": courses, "hours": hours})
            except:
                return render(request, "polls/journal.html", {"table": date_dict, "times": timeintervals, "types": lessontypes,
                        "courses": courses, "hours": hours})
        elif request.method == "POST":
            lesson = Lesson.objects.filter(id=request.POST.get("lesson_id"))[0]
            lesson.RealCountOfStudents = request.POST.get("lessonstudents")
            lesson.save()
            lessons = fill_lessons_table(request)
            date_dict = create_date_dict(lessons)
            timeintervals = TimeInterval.objects.all()
            lessontypes = TypeOfLesson.objects.all()
            courses = Course.objects.all()
            hours = calculate_academic_hours(lessons)
            return render(request, "polls/journal.html", {"table": date_dict, "hours": hours, "times": timeintervals,
                "types": lessontypes, "courses": courses, "success": "Занятие успешно отмечено проведённым"})
    else:
        return redirect('/')


#   Завершение сессии
def logoutpage(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('/')
    else:
        return redirect('/')


#   Админ/Начальная страница
def admin_homepage(request):
    if request.user.is_authenticated:
        if request.user.is_staff != True:
            return redirect('/journal')
        return render(request, "polls/admin_homepage.html")
    else:
        return redirect('/')


#   Список пользователей
def fill_users_table(request):
    teachers = Teacher.objects.all()
    tmp_arr = []
    count = 0
    for teacher in teachers:
        if request.user.id == 16:
            user = teacher.user_id
            tmp_arr.append({})
            tmp_arr[count]["ID"] = teacher.id
            tmp_arr[count]["Admin"] = user.is_staff
            tmp_arr[count]["Second_Name"] = user.last_name
            tmp_arr[count]["First_Name"] = user.first_name
            tmp_arr[count]["Patronymic"] = teacher.patronymic
            tmp_arr[count]["Username"] = user.username
            tmp_arr[count]["Email"] = user.email
            count += 1
        else:
            if teacher.user_id.id == 16:
                continue
            else:
                user = teacher.user_id
                tmp_arr.append({})
                tmp_arr[count]["ID"] = teacher.id
                tmp_arr[count]["Admin"] = user.is_staff
                tmp_arr[count]["Second_Name"] = user.last_name
                tmp_arr[count]["First_Name"] = user.first_name
                tmp_arr[count]["Patronymic"] = teacher.patronymic
                tmp_arr[count]["Username"] = user.username
                tmp_arr[count]["Email"] = user.email
                count += 1
    return tmp_arr


#   Админ/Пользователи
def admin_users(request):
    if request.user.is_authenticated:
        if request.user.is_staff != True:
            return redirect('/journal')
        if request.method == "GET":
            tmp_arr = fill_users_table(request)
            return render(request, "polls/admin_users.html", {"users": tmp_arr})
        elif request.method == "POST":
            if "username" in request.POST.keys():
                teacher = Teacher.objects.filter(id=request.POST.get("teacher_id"))[0]
                django_user = teacher.user_id
                teacher.patronymic = request.POST.get("patronymic")
                teacher.save()
                django_user.first_name = request.POST.get("name")
                django_user.second_name = request.POST.get("surname")
                django_user.email = request.POST.get("email")
                django_user.username = request.POST.get("username")
                if request.POST.get("superuser") == None:
                    django_user.is_staff = False
                elif request.POST.get("superuser") == "on":
                    django_user.is_staff = True
                if request.POST.get("password") != "":
                    django_user.password = make_password(request.POST.get("password"))
                django_user.save()
                tmp_arr = fill_users_table(request)
                return render(request, "polls/admin_users.html", {"users": tmp_arr, "success": "Данные пользователя успешно изменены"})
            else:
                if request.POST.get("teacher_id") == str(14):
                    tmp_arr = fill_users_table(request)
                    return render(request, "polls/admin_users.html", {"users": tmp_arr, "error": "Данного пользователя запрещено удалять"})
                teacher = Teacher.objects.filter(id=request.POST.get("teacher_id"))[0]
                django_user = teacher.user_id
                teacher.delete()
                django_user.delete()
            return redirect("/admin/users")
    else:
        return redirect('/')


#   Админ/Создание пользователя
def admin_create_user(request):
    if request.user.is_authenticated:
        if request.user.is_staff != True:
            return redirect('/journal')
        if request.method == "GET":
            return render(request, "polls/admin_create_user.html")
        elif request.method == "POST":
            try:
                if request.POST.get("superuser") == None:
                    django_user = User.objects.create(username=request.POST.get("username"), password=make_password(request.POST.get("password")), email=request.POST.get("email"), first_name=request.POST.get("name"), last_name=request.POST.get("surname"))
                elif request.POST.get("superuser") == "on":
                    django_user = User.objects.create(username=request.POST.get("username"), password=make_password(request.POST.get("password")), email=request.POST.get("email"), first_name=request.POST.get("name"), last_name=request.POST.get("surname"), is_staff=True)
                try:
                    new_teacher = Teacher.objects.create(user_id=django_user, patronymic=request.POST.get("patronymic"))
                except Exception as ex:
                    return render(request, "polls/admin_create_user.html", {"error": ex})
                else:
                    return render(request, "polls/admin_create_user.html", {"success": "Пользователь успешно создан"})
            except Exception as ex:
                return render(request, "polls/admin_create_user.html", {"error": ex})
    else:
        return redirect('/')


#   Список групп и курсов
def fill_groups_and_courses():
    groups = Group.objects.all()
    courses = Course.objects.all()
    tmp_arr = []
    for group in groups:
        tmp_arr.append({
            "id": group.id,
            "Course": group.Course.CourseNumber,
            "GroupNumber": group.GroupNumber,
            "NumberOfStudents": group.NumberOfStudents
            })
    return tmp_arr, courses


#   Админ/Группы
def admin_groups(request):
    if request.user.is_authenticated:
        if request.user.is_staff != True:
            return redirect('/journal')
        if request.method == "GET":
            tmp_arr, courses = fill_groups_and_courses()
            return render(request, "polls/admin_groups.html", {"Groups": tmp_arr, "Courses": courses})
        elif request.method == "POST":
            if "groupnumber" in request.POST.keys():
                group = Group.objects.filter(id=request.POST.get("group_id"))[0]
                course = Course.objects.filter(id=request.POST.get("coursenumber"))[0]
                group.Course = course
                group.GroupNumber = request.POST.get("groupnumber")
                group.NumberOfStudents = request.POST.get("numberofstudents")
                group.save()
                tmp_arr, courses = fill_groups_and_courses()
                return render(request, "polls/admin_groups.html", {"Groups": tmp_arr, "Courses": courses, "success": "Данные группы успешно изменены"})
            else:
                group = Group.objects.filter(id=request.POST.get("group_id"))[0]
                group.delete()
                tmp_arr, courses = fill_groups_and_courses()
                return render(request, "polls/admin_groups.html", {"Groups": tmp_arr, "Courses": courses, "success": "Группа успешно удалена"})
    else:
        return redirect('/')


#   Админ/Создание группы
def admin_create_group(request):
    if request.user.is_authenticated:
        if request.user.is_staff != True:
            return redirect('/journal')
        if request.method == "GET":
            tmp_arr, courses = fill_groups_and_courses()
            return render(request, "polls/admin_create_group.html", {"Courses": courses})
        elif request.method == "POST":
            try:
                course = Course.objects.filter(id=request.POST.get("coursenumber"))[0]
                group = Group.objects.create(Course=course, GroupNumber=request.POST.get("groupnumber"), NumberOfStudents=request.POST.get("numberofstudents"))
            except Exception as ex:
                return render(request, "polls/admin_create_group.html", {"error": ex})
            else:
                return render(request, "polls/admin_create_group.html", {"success": "Группа успешно создана"})
    else:
        return redirect('/')


#   Журнал/Создание занятия
def journal_create_lesson(request):
    if request.user.is_authenticated:
        if request.user.is_staff == True:
            return redirect('/admin/homepage')
        if request.method == "GET":
            timeintervals = TimeInterval.objects.all()
            courses = Course.objects.all()
            lessontypes = TypeOfLesson.objects.all()
            if 8 >= datetime.datetime.now().month <= 12:
                min = str(datetime.datetime.now().year) + "-09-01"
                max = str(datetime.datetime.now().year + 1) + "-01-31"
            elif 2 >= datetime.datetime.now().month <= 6:
                min = str(datetime.datetime.now().year) + "-02-01"
                max = str(datetime.datetime.now().year + 1) + "-06-30"
            return render(request, "polls/journal_create_lesson.html", {"times": timeintervals, "courses": courses, "types": lessontypes, "min": min, "max": max})
        elif request.method == 'POST':
            tmp_arr = []
            count = 0
            for key in request.POST.keys():
                if "timecheck" in key:
                    tmp_arr.append(key[9:])
                    count += 1
            if count == 0:
                timeintervals = TimeInterval.objects.all()
                courses = Course.objects.all()
                lessontypes = TypeOfLesson.objects.all()
                if 8 >= datetime.datetime.now().month <= 12:
                    min = str(datetime.datetime.now().year) + "-09-01"
                    max = str(datetime.datetime.now().year + 1) + "-01-31"
                elif 2 >= datetime.datetime.now().month <= 6:
                    min = str(datetime.datetime.now().year) + "-02-01"
                    max = str(datetime.datetime.now().year + 1) + "-06-30"
                return render(request, "polls/journal_create_lesson.html", {"times": timeintervals, "courses": courses, "types": lessontypes, "min": min, "max": max,
                 "error": "Вы не выбрали ни одного времени проведения занятия"})
            check_lesson = Lesson.objects.filter(Date=request.POST.get("RecordDate"), Teacher=Teacher.objects.filter(user_id=request.user)[0], TimeIntervals__in=tmp_arr)
            if len(check_lesson) != 0:
                timeintervals = TimeInterval.objects.all()
                courses = Course.objects.all()
                lessontypes = TypeOfLesson.objects.all()
                if 8 >= datetime.datetime.now().month <= 12:
                    min = str(datetime.datetime.now().year) + "-09-01"
                    max = str(datetime.datetime.now().year + 1) + "-01-31"
                elif 2 >= datetime.datetime.now().month <= 6:
                    min = str(datetime.datetime.now().year) + "-02-01"
                    max = str(datetime.datetime.now().year + 1) + "-06-30"
                return render(request, "polls/journal_create_lesson.html", {"times": timeintervals, "courses": courses, "types": lessontypes, "min": min, "max": max,
                 "error": "На выбранное время и дату уже запланировано другое занятие"})
            db_corse = Course.objects.filter(id=request.POST.get("course"))[0]
            try:
                groups = request.POST.get("lessongroups").split(", ")
            except:
                groups = [request.POST.get("lessongroups")]
            group_arr = []
            for group in groups:
                try:
                    group_arr.append(Group.objects.filter(Course=db_corse, GroupNumber=group)[0])
                except:
                    timeintervals = TimeInterval.objects.all()
                    courses = Course.objects.all()
                    lessontypes = TypeOfLesson.objects.all()
                    if 8 >= datetime.datetime.now().month <= 12:
                        min = str(datetime.datetime.now().year) + "-09-01"
                        max = str(datetime.datetime.now().year + 1) + "-01-31"
                    elif 2 >= datetime.datetime.now().month <= 6:
                        min = str(datetime.datetime.now().year) + "-02-01"
                        max = str(datetime.datetime.now().year + 1) + "-06-30"
                    return render(request, "polls/journal_create_lesson.html", {"times": timeintervals, "courses": courses, "types": lessontypes, "min": min, "max": max,
                     "error": "Группы " + str(db_corse.CourseNumber) + "-" + group + " не зарегистрировано в системе"})
            lesson = Lesson.objects.create(Date=request.POST.get("RecordDate"), TypeOfLesson = TypeOfLesson.objects.filter(id=request.POST.get("lessontype"))[0],
                                    RealCountOfStudents=None, Teacher = Teacher.objects.filter(user_id=request.user)[0])
            for time_id in tmp_arr:
                lesson.TimeIntervals.add(int(time_id))
            for group in group_arr:
                lesson.Groups.add(group.id)
            lesson.save()
            return redirect("/journal?success=True")
    else:
        return redirect('/')

def view_404(request, exception=None):
    if request.user.is_authenticated:
        if request.user.is_staff == True:
            return redirect('/admin/homepage')
        else:
            return redirect('/journal')
    else:
        return redirect('/')


#
def journal_create_schedule(request):
    if request.user.is_authenticated:
        if request.user.is_staff == True:
            return redirect('/admin/homepage')
        if request.method == "GET":
            return render(request, "polls/journal_create_schedule.html")
        elif request.method == 'POST':
            pass
    else:
        return redirect('/')


#   Отчет по кафедре
def report_all(request):
    if request.user.is_authenticated:
        if request.user.is_staff == False:
            return redirect('/journal')
        if request.method == "GET":
            return render(request, "polls/report_all.html")
        elif request.method == 'POST':
            users = User.objects.filter(is_staff=False)
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=report.xlsx'
            xlsx_data = generate_all_users_report_xlsx_file(users, request)
            response.write(xlsx_data)
            return response
    else:
        return redirect('/')

def generate_all_users_report_xlsx_file(users, request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet("Отчет")
    users_count = 1
    for user in users:
        tmp = 0
        count = 1
        teacher = Teacher.objects.filter(user_id=user)[0]
        fio = user.last_name + " " + user.first_name + " " + teacher.patronymic
        lessontypes = TypeOfLesson.objects.all()
        lessons = Lesson.objects.filter(Date__gte=request.POST.get("Start"), Date__lte=request.POST.get("Finish"), Teacher=teacher)
        worksheet_s.write(0, 0, "ФИО")
        worksheet_s.write(users_count, 0, fio)
        for lesson_type in lessontypes:
            lesson_count = 0
            worksheet_s.write(0, count, lesson_type.TypeName)
            for lesson in lessons:
                if lesson.RealCountOfStudents == None:
                    continue
                if lesson.TypeOfLesson.id == lesson_type.id:
                    time = lesson.TimeIntervals.all()[0].Interval if len(lesson.TimeIntervals.all()) == 1 else lesson.TimeIntervals.all()[0].Interval.split("-")[0] + "-" + lesson.TimeIntervals.all()[len(lesson.TimeIntervals.all()) - 1].Interval.split("-")[1]
                    if (datetime.datetime.strptime(time.split("-")[1], '%H:%M') - datetime.datetime.strptime(time.split("-")[0], '%H:%M')).total_seconds()/60 == 95: 
                        lesson_count += 2
                        tmp += 2
                    else:
                        lesson_count += 4
                        tmp += 4
            worksheet_s.write(users_count, count, lesson_count)
            count += 1
        worksheet_s.write(0, count, "Итого")
        worksheet_s.write(users_count, count, tmp)
        users_count += 1
    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data

#   Отчет по преподавателю
def report_teacher(request):
    if request.user.is_authenticated:
        if request.user.is_staff == False:
            return redirect('/journal')
        if request.method == "GET":
            return render(request, "polls/report_teacher.html")
        elif request.method == 'POST':
            try:
                user = User.objects.filter(email=request.POST.get("email"))[0]
            except:
                return render(request, "polls/report_teacher.html", {"error": "Пользователя с таким email не зарегистрировано в системе"})
            else:
                #path = "Академическая нагрузка " + str(request.POST.get("Start")) + " - " + str(request.POST.get("Finish")) + " " + request.user.last_name + " " + request.user.first_name[:1] + "." + " " + Teacher.objects.filter(user_id=request.user)[0].patronymic[:1] + ".xlsx"
                teacher = Teacher.objects.filter(user_id=user)[0]
                fio = user.last_name + " " + user.first_name + " " + teacher.patronymic
                lessontypes = TypeOfLesson.objects.all()
                lessons = Lesson.objects.filter(Date__gte=request.POST.get("Start"), Date__lte=request.POST.get("Finish"), Teacher=teacher)
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=report.xlsx'
                xlsx_data = generate_single_user_report_xlsx_file(lessontypes, lessons, fio)
                response.write(xlsx_data)
                return response
    else:
        return redirect('/')


#   Личный отчет
def report(request):
    if request.user.is_authenticated:
        if request.user.is_staff == True:
            return redirect('/admin/homepage')
        if request.method == "GET":
            return render(request, "polls/report.html")
        elif request.method == 'POST':
            teacher = Teacher.objects.filter(user_id=request.user)[0]
            lessontypes = TypeOfLesson.objects.all()
            lessons = Lesson.objects.filter(Date__gte=request.POST.get("Start"), Date__lte=request.POST.get("Finish"), Teacher=teacher)
            #path = "Академическая нагрузка " + str(request.POST.get("Start")) + " - " + str(request.POST.get("Finish")) + " " + request.user.last_name + " " + request.user.first_name[:1] + "." + " " + Teacher.objects.filter(user_id=request.user)[0].patronymic[:1] + ".xlsx"
            fio = request.user.last_name + " " + request.user.first_name + " " + teacher.patronymic
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=report.xlsx'
            xlsx_data = generate_single_user_report_xlsx_file(lessontypes, lessons, fio)
            response.write(xlsx_data)
            #return render(request, "polls/report.html")
            return response
    else:
        return redirect('/')

def generate_single_user_report_xlsx_file(lesson_types, lessons, fio):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet("Отчет")
    count = 1
    tmp = 0
    worksheet_s.write(0, 0, "ФИО")
    worksheet_s.write(1, 0, fio)
    for lesson_type in lesson_types:
        lesson_count = 0
        worksheet_s.write(0, count, lesson_type.TypeName)
        for lesson in lessons:
            if lesson.RealCountOfStudents == None:
                continue
            if lesson.TypeOfLesson.id == lesson_type.id:
                time = lesson.TimeIntervals.all()[0].Interval if len(lesson.TimeIntervals.all()) == 1 else lesson.TimeIntervals.all()[0].Interval.split("-")[0] + "-" + lesson.TimeIntervals.all()[len(lesson.TimeIntervals.all()) - 1].Interval.split("-")[1]
                if (datetime.datetime.strptime(time.split("-")[1], '%H:%M') - datetime.datetime.strptime(time.split("-")[0], '%H:%M')).total_seconds()/60 == 95:
                    lesson_count += 2
                    tmp += 2
                else:
                    lesson_count += 4
                    tmp += 4
        worksheet_s.write(1, count, lesson_count)
        count += 1
    worksheet_s.write(0, count, "Итого")
    worksheet_s.write(1, count, tmp)
    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data
    