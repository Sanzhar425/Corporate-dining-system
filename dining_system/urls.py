from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from canteen.auth_views import RegisterView, LoginView, LogoutView, MeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('canteen.urls')),

    # Auth endpoints
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/',    LoginView.as_view(),    name='login'),
    path('api/auth/logout/',   LogoutView.as_view(),   name='logout'),
    path('api/auth/me/',       MeView.as_view(),        name='me'),
    path('api/auth/refresh/',  TokenRefreshView.as_view(), name='token_refresh'),
]

from django.http import JsonResponse

def handler404(request, exception):
    return JsonResponse({'error': 'Бет табылмады.', 'status': 404}, status=404)

def handler500(request):
    return JsonResponse({'error': 'Сервер қатесі.', 'status': 500}, status=500)

handler404 = handler404
handler500 = handler500
