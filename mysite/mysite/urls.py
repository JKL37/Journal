from django.contrib import admin
from django.urls import include, path

handler404 = 'polls.views.view_404'

urlpatterns = [
    path('', include('polls.urls')),
    #path('admin/', admin.site.urls),
]