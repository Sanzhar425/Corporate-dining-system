from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView,
)
from canteen.auth_views import RegisterView, LoginView, LogoutView, MeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('canteen.urls')),
    # Frontend (HTML) беттері — сол бэкендтен қызмет көрсетіледі
    path('', TemplateView.as_view(template_name='login.html')),
    path('login.html', TemplateView.as_view(template_name='login.html')),
    path('menu.html', TemplateView.as_view(template_name='menu.html')),
    path('orders.html', TemplateView.as_view(template_name='orders.html')),
    path('cashier.html', TemplateView.as_view(template_name='cashier.html')),

    # Auth endpoints
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/',    LoginView.as_view(),    name='login'),
    path('api/auth/logout/',   LogoutView.as_view(),   name='logout'),
    path('api/auth/me/',       MeView.as_view(),        name='me'),
    path('api/auth/refresh/',  TokenRefreshView.as_view(), name='token_refresh'),

    # API құжаттамасы (Swagger / ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

from django.http import JsonResponse

def handler404(request, exception):
    return JsonResponse({'error': 'Бет табылмады.', 'status': 404}, status=404)

def handler500(request):
    return JsonResponse({'error': 'Сервер қатесі.', 'status': 500}, status=500)

handler404 = handler404
handler500 = handler500
