from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth, name='auth'),
    path('journal', views.journal, name='journal'),
    path('logoutpage', views.logoutpage, name='logoutpage'),
    path('admin/homepage', views.admin_homepage, name='admin_homepage'),
    path('admin/users', views.admin_users, name='admin_users'),
    path('admin/create_user', views.admin_create_user, name='admin_create_user'),
    path('admin/groups', views.admin_groups, name='admin_groups'),
    path('admin/create_group', views.admin_create_group, name='admin_create_group'),
    path('journal/create_lesson', views.journal_create_lesson, name='journal_create_lesson'),
    path('journal/create_schedule', views.journal_create_schedule, name='journal_create_schedule'),
    path('schedule', views.schedule, name='schedule'),
    path('report', views.report, name='report'),
    path('report/all', views.report_all, name='report_all'),
    path('report/teacher', views.report_teacher, name='report_teacher')
]