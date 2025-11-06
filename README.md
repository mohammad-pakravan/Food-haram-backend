# 🍽 Django Multi-Restaurant Management System

سیستم مدیریت چند کاربره برای مجموعه رستوران خیریه

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها)
- [پیش‌نیازها](#پیش‌نیازها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [استفاده](#استفاده)
- [ساختار پروژه](#ساختار-پروژه)
- [API Endpoints](#api-endpoints)

## ✨ ویژگی‌ها

- سیستم احراز هویت با JWT و HTTP Only Cookies (امنیت بالا)
- مستندات کامل API با Swagger/ReDoc
- مدیریت کاربران با نقش‌های چندگانه:
  - مدیر آشپزخانه (Kitchen Manager)
  - مدیر رستوران (Restaurant Manager)
  - صدور ژتون (Token Issuer)
  - تحویل غذا (Delivery Desk)
- Dockerization برای محیط توسعه
- REST API با Django REST Framework

## 🔧 پیش‌نیازها

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (یا استفاده از Docker)

## 🚀 نصب و راه‌اندازی

### 1. کلون پروژه

```bash
git clone <repository-url>
cd kitchen-managment
```

### 2. ایجاد فایل .env

فایل `.env.example` را کپی کنید و به `.env` تغییر نام دهید:

```bash
cp .env.example .env
```

سپس مقادیر را مطابق نیاز خود تنظیم کنید.

### 3. راه‌اندازی با Docker

```bash
# ساخت و اجرای کانتینرها
docker-compose up --build

# یا در حالت background
docker-compose up -d --build
```

پروژه در آدرس `http://localhost:8001` در دسترس خواهد بود.

### 4. ایجاد کاربر superuser

یک superuser به صورت خودکار با مقادیر پیش‌فرض ایجاد می‌شود:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`
- **Roles**: `restaurant_manager`, `kitchen_manager`

برای تغییر این مقادیر، متغیرهای زیر را در فایل `.env` تنظیم کنید:
```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin123
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_ROLES=restaurant_manager,kitchen_manager
```

**نکته:** اگر superuser با این username از قبل وجود داشته باشد، ایجاد نمی‌شود.

### 5. دسترسی به Django Admin

به آدرس `http://localhost:8001/admin` بروید و با کاربر superuser وارد شوید.

### 6. دسترسی به Swagger Documentation

- **Swagger UI**: `http://localhost:8001/swagger/`
- **ReDoc**: `http://localhost:8001/redoc/`
- **Swagger JSON**: `http://localhost:8001/swagger.json`
- **Swagger YAML**: `http://localhost:8001/swagger.yaml`

## 💻 استفاده

### API Endpoints

#### احراز هویت (HTTP Only Cookies)

**ورود (Login)**
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "message": "Login successful"
}
```

Tokens به صورت HTTP Only Cookies تنظیم می‌شوند:
- `access_token`: برای دسترسی به API (1 ساعت)
- `refresh_token`: برای refresh کردن token (7 روز)

**Refresh Token**
```http
POST /api/auth/refresh/
Content-Type: application/json
```

**Response:**
```json
{
  "message": "Token refreshed successfully"
}
```

Token جدید به صورت خودکار در Cookie تنظیم می‌شود.

**خروج (Logout)**
```http
POST /api/auth/logout/
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

Cookies پاک می‌شوند.

**اطلاعات کاربر فعلی**
```http
GET /api/auth/me/
```

Token از Cookie به صورت خودکار خوانده می‌شود.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "roles": ["restaurant_manager"],
  "restaurant_name": "رستوران خیریه"
}
```

### استفاده در Frontend

برای استفاده از API در frontend (مثلاً React یا Vue)، باید `credentials: 'include'` را در درخواست‌ها تنظیم کنید:

**JavaScript/Fetch:**
```javascript
// Login
fetch('http://localhost:8001/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // مهم: برای ارسال cookies
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
});

// Fetch user data
fetch('http://localhost:8001/api/auth/me/', {
  method: 'GET',
  credentials: 'include',  // مهم: برای ارسال cookies
});
```

**Axios:**
```javascript
axios.defaults.withCredentials = true;

// Login
axios.post('http://localhost:8001/api/auth/login/', {
  username: 'your_username',
  password: 'your_password'
});

// Fetch user data
axios.get('http://localhost:8001/api/auth/me/');
```

**نکته مهم:** در production، باید `CORS_ALLOWED_ORIGINS` را در تنظیمات به دامنه frontend خود تنظیم کنید.

### استفاده از Permissions در Views

برای استفاده از permission های مخصوص هر پنل:

```python
from apps.accounts.permissions import KitchenAccess

class MyKitchenView(APIView):
    permission_classes = [KitchenAccess]
    # ...
```

## 📁 ساختار پروژه

```
restaurant_manager/
├── compose/
│   ├── dev/
│   │   ├── Dockerfile
│   │   └── django-entrypoint.sh
│   └── prod/
│       ├── Dockerfile
│       ├── nginx.conf
│       └── gunicorn.conf.py
├── core/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── admin.py
│   └── __init__.py
├── manage.py
├── requirements.txt
├── docker-compose.yml
└── .env
```

## 🧪 تست

برای اجرای تست‌ها:

```bash
docker-compose exec web python manage.py test
```

## 📝 Migration

برای ایجاد migration جدید:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## 🔐 نقش‌های کاربری

هر کاربر می‌تواند چند نقش همزمان داشته باشد. نقش‌های موجود:

- `kitchen_manager`: مدیر آشپزخانه
- `restaurant_manager`: مدیر رستوران
- `token_issuer`: صدور ژتون
- `delivery_desk`: تحویل غذا

برای تنظیم نقش کاربر از Django Admin استفاده کنید.

## 🐳 Docker Commands

```bash
# مشاهده لاگ‌ها
docker-compose logs -f web

# دسترسی به shell
docker-compose exec web sh

# متوقف کردن کانتینرها
docker-compose down

# متوقف کردن و حذف volume ها
docker-compose down -v
```

## 📚 توسعه

برای توسعه محلی بدون Docker:

```bash
# نصب dependencies
pip install -r requirements.txt

# ایجاد migration
python manage.py makemigrations

# اجرای migration
python manage.py migrate

# اجرای سرور
python manage.py runserver
```

## 🚧 فازهای بعدی

- [ ] پنل مدیریت آشپزخانه
- [ ] پنل مدیریت رستوران
- [ ] پنل صدور ژتون
- [ ] پنل تحویل غذا
- [ ] سیستم گزارش‌گیری

## 📄 License

[License information]

## 👥 Contributors

[Contributors information]

