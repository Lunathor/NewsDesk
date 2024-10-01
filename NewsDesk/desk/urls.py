from django.urls import path, include

from .views import *

urlpatterns = [
    path('', PostListView.as_view()),
    path('post/<int:pk>/', post_detail, name='PostDetail'),
]
