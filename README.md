# 🍽 Corporate Dining System

Корпоративтік асхана жүйесі — мәзір, тапсырыс беру, баланс толтыру, рөлдер
бойынша рұқсаттар және күнделікті есептер. Бэкенд **Django REST
Framework**-те, аутентификация **JWT (SimpleJWT)** арқылы жасалған.

## ER-диаграмма

![ERD](ER%20диаграмма.png)

---

## 🚀 Жобаны іске қосу (Quick start)

### 1. Репозиторийді клондау

```bash
git clone https://github.com/Sanzhar425/Corporate-dining-system.git
cd Corporate-dining-system
```

### 2. Виртуалды орта құру

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Тәуелділіктерді орнату

```bash
pip install -r requirements.txt
```

### 4. Дерекқор миграциясы

```bash
python manage.py migrate
```

### 5. (Міндетті емес) Сынақ деректерін жүктеу

Мәзір мен тестілік пайдаланушыларды толтыру:

```bash
python manage.py seed
```

Бұл команда мынадай пайдаланушыларды жасайды (барлығының құпия сөзі —
`password123`):

| username  | role    | balance |
|-----------|---------|---------|
| admin     | admin   | 0       |
| cook1     | cashier | 0       |
| asel      | user    | 5000    |
| daniyar   | user    | 3500    |

Әкімші (superuser) жеке жасағыңыз келсе:

```bash
python manage.py createsuperuser
```

### 6. Серверді іске қосу

```bash
python manage.py runserver
```

API мына мекен-жайда қолжетімді болады: `http://127.0.0.1:8000/`

---

## 📚 API құжаттамасы (Swagger / OpenAPI)

Жоба **drf-spectacular** арқылы автоматты түрде OpenAPI 3 схемасын
генерациялайды:

| Сілтеме | Сипаттама |
|---|---|
| `http://127.0.0.1:8000/api/docs/` | **Swagger UI** — интерактивті құжаттама, эндпоинттерді браузерден тікелей сынап көруге болады |
| `http://127.0.0.1:8000/api/redoc/` | **ReDoc** — оқуға ыңғайлы баламалы көрініс |
| `http://127.0.0.1:8000/api/schema/` | Шикі `openapi.yaml` схемасы |

> Swagger UI ішінде "Authorize" батырмасын басып, `Bearer <access_token>`
> енгізсеңіз, авторизация талап ететін эндпоинттерді де сынай аласыз.

---

## 🔑 Аутентификация (JWT)

| Әдіс | Маршрут | Сипаттама |
|---|---|---|
| POST | `/api/auth/register/` | Тіркелу (`username`, `email`, `password`, `role`) |
| POST | `/api/auth/login/` | Кіру — `access` және `refresh` токен қайтарады |
| POST | `/api/auth/refresh/` | `access` токенді жаңарту |
| POST | `/api/auth/logout/` | Шығу (`refresh` токенді blacklist-ке қосады) |
| GET  | `/api/auth/me/` | Ағымдағы пайдаланушы туралы ақпарат |

Қорғалған эндпоинттерге сұраныс жіберу үшін `Authorization` header-іне
токенді қосу керек:

```
Authorization: Bearer <access_token>
```

### Логин мысалы (cURL)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'
```

---

## 👥 Рөлдік модель

| Рөл | Құқықтары |
|---|---|
| **admin** | Барлық эндпоинттерге толық қолжетімділік: мәзірді басқару, пайдаланушыларды басқару, барлық тапсырыстар мен транзакцияларды көру |
| **cashier** | Тапсырыс статусын өзгерту, баланс толтыру (`topup`), транзакцияларды көру |
| **user** (қызметкер) | Мәзірді көру, өз тапсырыстарын жасау/болдырмау, тек өз тарихын көру |

Рұқсаттар `canteen/permissions.py` файлындағы `IsAdmin`,
`IsAdminOrCashier`, `IsOwnerOrAdmin` кластарымен әр эндпоинтте жеке
тексеріледі.

---

## 🔗 Негізгі эндпоинттер

| Әдіс | Маршрут | Сипаттама |
|---|---|---|
| GET | `/api/menu/` | Мәзірді көру (категория бойынша сүзу: `?category=drink`) |
| POST | `/api/menu/` | Жаңа тағам қосу *(admin)* |
| POST | `/api/orders/` | Тапсырыс жасау: `{"items":[{"menu_item":1,"quantity":2}]}` |
| GET | `/api/orders/` | Тапсырыстар тізімі (admin/cashier — барлығын, user — тек өзінікін) |
| PATCH | `/api/orders/{id}/update_status/` | Тапсырыс статусын өзгерту *(admin/cashier)* |
| POST | `/api/users/{id}/topup/` | Баланс толтыру *(admin/cashier)* |
| GET | `/api/users/{id}/orders_detail/` | **Күрделі сұраулар:** пайдаланушы + барлық тапсырыстары + тағамдары + статистикасы (JOIN арқылы `select_related`/`prefetch_related`) |
| GET | `/api/transactions/` | Транзакциялар тарихы *(admin/cashier)* |

---

## 🖥 Frontend (HTML/CSS) интеграциясы

`login.html`, `menu.html`, `orders.html` файлдары — backend API-мен тікелей
жұмыс істейтін қарапайым frontend үлгілері. Олар `fetch()` арқылы
`http://127.0.0.1:8000/api/...` эндпоинттеріне сұраныс жібереді және JWT
токенді `localStorage`-та сақтайды.

Сынау үшін:

1. `python manage.py runserver` арқылы backend-ті іске қосыңыз.
2. `login.html` файлын браузерде ашыңыз (мысалы, VS Code Live Server
   немесе `python -m http.server` арқылы).
3. `seed` командасынан кейінгі пайдаланушылардың бірімен кіріңіз
   (мысалы, `asel` / `password123`).
4. Сәтті кіргеннен соң `menu.html` бетіне автоматты түрде өтесіз, онда
   мәзір API-дан тартылады.

> ⚠️ CORS барлық домендерге ашық (`CORS_ALLOW_ALL_ORIGINS = True`),
> сондықтан frontend кез келген портта орналасса да сұраныстар өтеді.

---

## 🗂 Жоба құрылымы

```
Corporate-dining-system/
├── canteen/                # Негізгі қосымша
│   ├── models.py           # User, MenuItem, Order, OrderItem, Transaction
│   ├── serializers.py      # DRF serializer-лер
│   ├── auth_serializers.py # Register/Login serializer-лер
│   ├── views.py            # ViewSet-тер (Menu, Order, User, Transaction)
│   ├── auth_views.py       # Register/Login/Logout/Me
│   ├── permissions.py      # IsAdmin, IsAdminOrCashier, IsOwnerOrAdmin
│   ├── urls.py              # /api/ маршруттары
│   └── management/commands/seed.py  # Сынақ деректерін толтыру
├── dining_system/          # Django жоба баптаулары
│   ├── settings.py
│   └── urls.py              # Auth + Swagger/ReDoc маршруттары
├── login.html / menu.html / orders.html  # Frontend үлгілері
├── requirements.txt
└── manage.py
```

---

## 🛠 Технологиялар

- Python 3.12 / Django 6
- Django REST Framework
- djangorestframework-simplejwt (JWT аутентификация)
- django-cors-headers
- drf-spectacular (Swagger / OpenAPI 3)
- SQLite (default)

---

## 📄 Лицензия

Бұл жоба оқу мақсатында жасалған.
