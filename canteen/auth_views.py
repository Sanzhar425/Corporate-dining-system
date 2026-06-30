from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import User
from .auth_serializers import RegisterSerializer, LoginSerializer
from .serializers import UserSerializer


@extend_schema(tags=["Auth"], summary="Тіркелу (Register)")
class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Body: { username, email, password, role }
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Auth"],
    summary="Жүйеге кіру (Login)",
    request=LoginSerializer,
    responses={200: UserSerializer},
)
class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { username, password }
    Returns: { user, access, refresh }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        )


@extend_schema(
    tags=["Auth"],
    summary="Жүйеден шығу (Logout)",
    request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
)
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body: { refresh }
    Blacklist-ке қосады (refresh токенді жарамсыз етеді)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Сәтті шықтыңыз.'})
        except Exception:
            return Response(
                {'error': 'Жарамсыз токен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["Auth"], summary="Ағымдағы пайдаланушы (Me)", responses={200: UserSerializer})
class MeView(APIView):
    """
    GET /api/auth/me/
    Ағымдағы авторизацияланған пайдаланушы туралы ақпарат
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
