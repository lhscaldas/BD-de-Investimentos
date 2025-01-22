from django.urls import path
from .views import IndexLoginView

urlpatterns = [
     path('', IndexLoginView.as_view(), name='index'),
]