# route/urls.py
from django.urls import path
from route.views import RouteOptimizationAPIView

urlpatterns = [
    path('optimize-route/', RouteOptimizationAPIView.as_view(), name='optimize-route'),
]