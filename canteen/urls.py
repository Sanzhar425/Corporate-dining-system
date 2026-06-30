from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('menu', views.MenuItemViewSet, basename='menu')
router.register('orders', views.OrderViewSet, basename='orders')
router.register('users', views.UserViewSet, basename='users')
router.register('transactions', views.TransactionViewSet, basename='transactions')
router.register('reports', views.ReportViewSet, basename='reports')

urlpatterns = [
    path('api/', include(router.urls)),
]
