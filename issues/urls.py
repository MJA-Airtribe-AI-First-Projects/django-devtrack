from django.urls import path
from rest_framework.views import APIView

from issues.views import ReporterView, IssueView

urlpatterns = [path('reporters/', ReporterView.as_view()),
               path('reporters/<str:id>/', ReporterView.as_view()),
               path('issues/', IssueView.as_view()),
               path('issues/<str:id>/', IssueView.as_view()),]