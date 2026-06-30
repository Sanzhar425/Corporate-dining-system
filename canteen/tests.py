from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from canteen.models import MenuItem, Order, OrderItem, Transaction

User = get_user_model()


class AuthTests(APITestCase):
    def test_register_and_login(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'password123',
            'role': 'user'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        res = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)


class MenuItemTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.client.force_authenticate(user=self.admin)
        
    def test_create_menu_item(self):
        res = self.client.post('/api/menu/', {
            'name': 'Борщ',
            'category': 'first',
            'price': '1200.00',
            'quantity_available': 10
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuItem.objects.count(), 1)


class OrderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1', password='pass', role='user', balance=Decimal('5000')
        )
        self.item = MenuItem.objects.create(
            name='Плов', category='second', price=Decimal('1500'), quantity_available=5
        )
        self.client.force_authenticate(user=self.user)
        
    def test_create_order(self):
        res = self.client.post('/api/orders/', {
            'items': [{'menu_item': self.item.id, 'quantity': 2}]
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('2000'))
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 3)
        
    def test_cancel_order_returns_money_and_stock(self):
        res = self.client.post('/api/orders/', {
            'items': [{'menu_item': self.item.id, 'quantity': 1}]
        })
        order_id = res.data['id']
        
        res = self.client.delete(f'/api/orders/{order_id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal('5000'))
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 5)
        
        self.assertTrue(Transaction.objects.filter(type='deposit').exists())


class ReportTests(APITestCase):
    def setUp(self):
        self.cashier = User.objects.create_user(username='cash', password='pass', role='cashier')
        self.client.force_authenticate(user=self.cashier)
        
    def test_daily_report(self):
        res = self.client.get('/api/reports/daily/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('revenue', res.data)
        self.assertIn('popular_items', res.data)
