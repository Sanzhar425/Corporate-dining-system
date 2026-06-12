from django.core.management.base import BaseCommand
from canteen.models import MenuItem, User

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Тағамдар
        items = [
            {'name': 'Борщ',         'category': 'first',  'price': 350, 'quantity_available': 50},
            {'name': 'Сорпа',        'category': 'first',  'price': 280, 'quantity_available': 40},
            {'name': 'Лагман',       'category': 'first',  'price': 420, 'quantity_available': 30},
            {'name': 'Бефстроганов', 'category': 'second', 'price': 650, 'quantity_available': 25},
            {'name': 'Балық',        'category': 'second', 'price': 590, 'quantity_available': 20},
            {'name': 'Пилав',        'category': 'second', 'price': 480, 'quantity_available': 35},
            {'name': 'Цезарь',       'category': 'salad',  'price': 320, 'quantity_available': 0},
            {'name': 'Оливье',       'category': 'salad',  'price': 280, 'quantity_available': 45},
            {'name': 'Шай',          'category': 'drink',  'price': 80,  'quantity_available': 100},
            {'name': 'Компот',       'category': 'drink',  'price': 120, 'quantity_available': 60},
        ]
        for item in items:
            MenuItem.objects.get_or_create(**item)

        # Сынақ қызметкерлер
        users = [
            {'username': 'asel',    'email': 'asel@company.kz',    'role': 'user',    'balance': 5000},
            {'username': 'daniyar', 'email': 'daniyar@company.kz', 'role': 'user',    'balance': 3500},
            {'username': 'admin',   'email': 'admin@company.kz',   'role': 'admin',   'balance': 0},
            {'username': 'cook1',   'email': 'cook@company.kz',    'role': 'cashier', 'balance': 0},
        ]
        for u in users:
            if not User.objects.filter(username=u['username']).exists():
                user = User.objects.create_user(
                    username=u['username'],
                    email=u['email'],
                    password='password123',
                    role=u['role'],
                    balance=u['balance']
                )

        self.stdout.write(self.style.SUCCESS('✅ Деректер сәтті қосылды!'))