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
    """Нысан иесі немесе admin рұқсат алады.

    obj — Order, Transaction (user_id өрісі бар) немесе User-дің өзі
    (бұл жағдайда obj.id == request.user.id тексеріледі) болуы мүмкін.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        owner_id = getattr(obj, 'user_id', None)
        if owner_id is None:
            owner_id = getattr(obj, 'id', None)
        return owner_id == request.user.id
