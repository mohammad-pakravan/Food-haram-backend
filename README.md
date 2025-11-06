# 🍽 Django Multi-Restaurant Management System

سیستم مدیریت چند کاربره برای مجموعه رستوران  

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها)
- [پیش‌نیازها](#پیش‌نیازها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [استفاده](#استفاده)
- [ساختار پروژه](#ساختار-پروژه)
- [نقش‌های کاربری (Panels)](#نقش‌های-کاربری-panels)
- [API Endpoints](#api-endpoints)

## ✨ ویژگی‌ها

- سیستم احراز هویت با JWT و HTTP Only Cookies (امنیت بالا)
- مستندات کامل API با Swagger/ReDoc
- مدیریت مراکز و رستوران‌ها
- مدیریت کاربران با نقش‌های چندگانه
- کاربران مرکزی با دسترسی به تمام رستوران‌ها
- هر کاربر فقط به یک رستوران متصل است
- هر رستوران می‌تواند چندین کاربر داشته باشد
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
- **Is Central**: `True` (دسترسی به تمام رستوران‌ها)

برای تغییر این مقادیر، متغیرهای زیر را در فایل `.env` تنظیم کنید:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin123
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_IS_CENTRAL=True
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
  "password": "your_password",
  "panel": "kitchen_manager"
}
```

**نکته:** فیلد `panel` اجباری است و باید یکی از نقش‌های زیر باشد:

- `kitchen_manager`: مدیر آشپزخانه
- `restaurant_manager`: مدیر رستوران
- `token_issuer`: صدور ژتون
- `delivery_desk`: تحویل غذا

**Response (موفق):**

```json
{
  "message": "ورود موفقیت آمیز بود",
  "user": {
    "id": 1,
    "username": "admin",
    "active_role": "kitchen_manager",
    "restaurant": {
      "id": 34,
      "name": "user-name"
    }
  }
}
```

**Response (عدم دسترسی):**

```json
{
  "detail": "این سطح دسترسی وجود نداره"
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
  "is_central": false,
  "is_central_display": false,
  "restaurants": [
    {
      "id": 34,
      "name": "user - name"
    }
  ]
}
```

**ویرایش اطلاعات کاربری**

```http
PUT /api/auth/me/update/
Content-Type: application/json

{
  "email": "newemail@example.com",
  "first_name": "نام",
  "last_name": "نام خانوادگی"
}
```

**Response:**

```json
{
  "message": "اطلاعات کاربری با موفقیت به‌روزرسانی شد",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "newemail@example.com",
    ...
  }
}
```

**تغییر رمز عبور**

```http
POST /api/auth/me/change-password/
Content-Type: application/json

{
  "old_password": "current_password",
  "new_password": "new_secure_password",
  "new_password_confirm": "new_secure_password"
}
```

**Response:**

```json
{
  "message": "رمز عبور با موفقیت تغییر کرد"
}
```

**دریافت لیست نقش‌های موجود**

```http
GET /api/auth/roles/
```

**Response:**

```json
[
  {
    "value": "kitchen_manager",
    "label": "مدیر آشپزخانه"
  },
  {
    "value": "restaurant_manager",
    "label": "مدیر رستوران"
  },
  {
    "value": "token_issuer",
    "label": "صدور ژتون"
  },
  {
    "value": "delivery_desk",
    "label": "تحویل غذا"
  }
]
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
│   │   ├── authentication.py
│   │   ├── token_serializer.py
│   │   └── admin.py
│   └── restaurants/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── admin.py
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

## 🔐 نقش‌های کاربری (Panels)

سیستم از 4 نوع پنل (نقش) پشتیبانی می‌کند:

### انواع پنل‌ها:

1. **`kitchen_manager`** - مدیر آشپزخانه

   - مدیریت عملیات آشپزخانه
   - نظارت بر تهیه غذا
2. **`restaurant_manager`** - مدیر رستوران

   - مدیریت کلی رستوران
   - نظارت بر عملیات روزانه
3. **`token_issuer`** - صدور ژتون

   - صدور و مدیریت ژتون‌ها
   - ثبت سفارشات
4. **`delivery_desk`** - تحویل غذا

   - مدیریت تحویل غذا
   - ثبت وضعیت تحویل

### قوانین دسترسی:

- **کاربران مرکزی (`is_central=True`)**:

  - دسترسی به تمام رستوران‌ها
  - دسترسی به تمام پنل‌ها
  - نیازی به تعریف رستوران ندارند
- **کاربران عادی**:

  - هر کاربر فقط به یک رستوران متصل است
  - می‌توانند چندین نقش در همان رستوران داشته باشند
  - فقط به رستوران خود دسترسی دارند

### مدیریت دسترسی:

برای تنظیم نقش‌ها و رستوران کاربر از Django Admin استفاده کنید:

- مراکز (Centers) → رستوران‌ها (Restaurants) → کاربران و دسترسی‌ها (User Restaurant Permissions)

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
