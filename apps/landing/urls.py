from django.urls import path
from . import views
app_name = 'landing'
urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('test',views.api_testing, name= 'api-testing'),
]
