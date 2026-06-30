from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.db import transaction as db_transaction
from decimal import Decimal, InvalidOperation
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import MenuItem, Order, OrderItem, Transaction, User
from .serializers import (MenuItemSerializer, OrderSerializer,
                          TransactionSerializer, UserSerializer)
from .permissions import IsAdmin, IsAdminOrCashier, IsOwnerOrAdmin


@extend_schema_view(
    list=extend_schema(summary="Мәзірді тізімдеу", tags=["Menu"]),
    retrieve=extend_schema(summary="Тағам туралы ақпарат", tags=["Menu"]),
    create=extend_schema(summary="Жаңа тағам қосу (тек admin)", tags=["Menu"]),
    update=extend_schema(summary="Тағамды толық жаңарту (тек admin)", tags=["Menu"]),
    partial_update=extend_schema(summary="Тағамды ішінара жаңарту (тек admin)", tags=["Menu"]),
    destroy=extend_schema(summary="Тағамды өшіру (soft-delete, тек admin)", tags=["Menu"]),
)
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.filter(is_active=True)
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception:
            return Response(
                {'error': 'Тағам табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        item.is_active = False
        item.save()
        return Response({'detail': 'Тағам өшірілді.'}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary="Тапсырыстар тізімі", tags=["Orders"]),
    retrieve=extend_schema(summary="Бір тапсырыс туралы ақпарат", tags=["Orders"]),
    create=extend_schema(summary="Жаңа тапсырыс жасау", tags=["Orders"]),
    destroy=extend_schema(summary="Тапсырысты болдырмау", tags=["Orders"]),
)
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create', 'destroy'):
            return [IsAuthenticated()]
        if self.action == 'update_status':
            return [IsAdminOrCashier()]
        return [IsAdmin()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        if user.role in ('admin', 'cashier'):
            return Order.objects.all().select_related('user').prefetch_related('items__menu_item')
        return Order.objects.filter(user=user).prefetch_related('items__menu_item')

    def create(self, request, *args, **kwargs):
        """
        POST /api/orders/
        Body: { "items": [{"menu_item": 1, "quantity": 2}, ...] }
        """
        items_data = request.data.get('items', [])
        if not items_data:
            return Response(
                {'error': 'Тапсырыста тағам болуы керек.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            total = 0
            order_items = []

            for item_data in items_data:
                menu_item_id = item_data.get('menu_item')
                quantity = int(item_data.get('quantity', 1))

                if quantity <= 0:
                    return Response(
                        {'error': 'Саны кемінде 1 болуы керек.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    menu_item = MenuItem.objects.select_for_update().get(
                        pk=menu_item_id, is_active=True
                    )
                except MenuItem.DoesNotExist:
                    return Response(
                        {'error': f'Тағам (id={menu_item_id}) табылмады.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                if menu_item.quantity_available < quantity:
                    return Response(
                        {'error': f'«{menu_item.name}» жеткіліксіз. Қалған: {menu_item.quantity_available}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                subtotal = menu_item.price * quantity
                total += subtotal
                order_items.append((menu_item, quantity, menu_item.price))

            user = request.user
            if user.balance < total:
                return Response(
                    {'error': f'Баланс жеткіліксіз. Қажет: {total}₸, Сізде: {user.balance}₸'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Тапсырыс жасау
            order = Order.objects.create(
                user=user,
                total_amount=total,
                status='pending'
            )

            # OrderItem жасау + quantity азайту
            for menu_item, quantity, unit_price in order_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    unit_price=unit_price
                )
                menu_item.quantity_available -= quantity
                menu_item.save()

            # Балансты шегеру
            user.balance -= total
            user.save()

            # Транзакция жазу
            Transaction.objects.create(
                user=user,
                amount=total,
                type='payment',
                description=f'Тапсырыс #{order.id} төлемі'
            )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(pk=kwargs['pk'])
        except Order.DoesNotExist:
            return Response(
                {'error': 'Тапсырыс табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user.role == 'user' and order.user != request.user:
            return Response(
                {'error': 'Бұл тапсырысқа рұқсатыңыз жоқ.', 'status': 401},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(OrderSerializer(order).data)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status not in ('pending', 'preparing'):
            return Response(
                {'error': 'Тек күтілуде немесе дайындалуда тапсырысты болдырмауға болады.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'cancelled'
        order.save()
        return Response({'detail': 'Тапсырыс болдырылмады.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Тапсырыс табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )
        new_status = request.data.get('status')
        valid = ['pending', 'preparing', 'ready', 'completed', 'cancelled']
        if not new_status:
            return Response(
                {'error': 'Статус көрсетілмеген.', 'status': 400},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_status not in valid:
            return Response(
                {'error': f'Қате статус. Рұқсат етілген: {valid}', 'status': 400},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)


@extend_schema_view(
    list=extend_schema(summary="Пайдаланушылар тізімі (тек admin)", tags=["Users"]),
    retrieve=extend_schema(summary="Пайдаланушы туралы ақпарат (тек admin)", tags=["Users"]),
    create=extend_schema(summary="Пайдаланушы жасау (тек admin)", tags=["Users"]),
    update=extend_schema(summary="Пайдаланушыны жаңарту (тек admin)", tags=["Users"]),
    partial_update=extend_schema(summary="Пайдаланушыны ішінара жаңарту (тек admin)", tags=["Users"]),
    destroy=extend_schema(summary="Пайдаланушыны өшіру (тек admin)", tags=["Users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception:
            return Response(
                {'error': 'Пайдаланушы табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrCashier])
    def topup(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пайдаланушы табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )
        amount = request.data.get('amount', 0)
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError, InvalidOperation):
            return Response(
                {'error': 'Сома дұрыс емес! 0-ден үлкен болуы керек.', 'status': 400},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.balance += amount
        user.save()
        Transaction.objects.create(
            user=user, amount=amount,
            type='deposit', description='Баланс толтыру'
        )
        return Response({'balance': float(user.balance)})

    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrAdmin])
    def orders_detail(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пайдаланушы табылмады.', 'status': 404},
                status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, user)

        orders = Order.objects.filter(user=user)\
            .prefetch_related('items__menu_item')\
            .order_by('-ordered_at')

        orders_data = []
        for order in orders:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'menu_item_id': item.menu_item.id,
                    'name': item.menu_item.name,
                    'category': item.menu_item.category,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.unit_price * item.quantity),
                })
            orders_data.append({
                'order_id': order.id,
                'status': order.status,
                'ordered_at': order.ordered_at.isoformat(),
                'total_amount': float(order.total_amount),
                'items': items_data,
            })

        stats = Order.objects.filter(user=user).aggregate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
        )

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'balance': float(user.balance),
            },
            'stats': {
                'total_orders': stats['total_orders'] or 0,
                'total_spent': float(stats['total_spent'] or 0),
            },
            'orders': orders_data,
        })


@extend_schema_view(
    list=extend_schema(summary="Транзакциялар тізімі (admin/cashier)", tags=["Transactions"]),
    retrieve=extend_schema(summary="Бір транзакция (admin/cashier)", tags=["Transactions"]),
)
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    http_method_names = ['get']

    def get_permissions(self):
        return [IsAdminOrCashier()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Transaction.objects.all().select_related('user')
        return Transaction.objects.filter(user=user)
