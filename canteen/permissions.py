from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Тек admin рөліндегі пайдаланушыға рұқсат береді."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrCashier(BasePermission):
    """Admin немесе cashier рөліндегі пайдаланушыға рұқсат береді."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('admin', 'cashier')
        )


class IsOwnerOrAdmin(BasePermission):
    """Нысан иесі немесе admin рұқсат алады."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # obj — Order немесе Transaction болуы мүмкін
        return getattr(obj, 'user_id', None) == request.user.id
