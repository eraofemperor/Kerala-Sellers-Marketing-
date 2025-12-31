# Kerala Sellers Customer Support AI

A Django REST Framework-based customer support system with bilingual support (English/Malayalam) for e-commerce order management, returns, and AI-powered customer assistance.

## Project Overview

This system provides a comprehensive backend for handling customer support operations including:
- Order tracking and management
- Return/refund request processing
- AI-powered customer support conversations
- Bilingual policy management (English/Malayalam)
- Support message history and analytics

## Tech Stack

- **Framework**: Django 4.2.7 with Django REST Framework 3.14.0
- **Database**: PostgreSQL (with SQLite fallback for development)
- **Language**: Python 3.10+
- **Key Dependencies**:
  - django-environ: Environment variable management
  - django-cors-headers: CORS support
  - psycopg2-binary: PostgreSQL adapter
  - gunicorn: WSGI HTTP server

## Project Structure

```
kerala-sellers-support/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore rules
├── docker-compose.yml       # PostgreSQL container setup
├── config/                  # Django project configuration
│   ├── settings.py         # Project settings
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── support/                 # Main application
│   ├── models.py           # Database models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views
│   ├── urls.py             # App URL configuration
│   ├── admin.py            # Django admin configuration
│   ├── apps.py             # App configuration
│   └── migrations/         # Database migrations
└── README.md               # This file
```

## Database Models

### 1. Order
Tracks customer orders with status updates and delivery information.
- Fields: order_id, user_id, status, tracking_number, timestamps
- Status choices: placed, packed, shipped, out_for_delivery, delivered, cancelled

### 2. ReturnRequest
Manages product return and refund requests.
- Fields: return_id, order, product_id, reason, status, refund_amount
- Status choices: requested, approved, rejected, returned, refunded
- Reason choices: damaged, unwanted, defective

### 3. SupportConversation
Represents a customer support chat session.
- Fields: session_id (UUID), user_id, language, message_count, escalated
- Language support: English (en), Malayalam (ml)

### 4. SupportMessage
Individual messages within a support conversation.
- Fields: conversation, sender, message, query_type, ai_confidence
- Query types: order_status, return_refund, policy, general, escalation

### 5. Policy
Bilingual policy content for customer support responses.
- Fields: policy_type, content_en, content_ml, version

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kerala-sellers-support
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kerala_sellers_support
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Set Up PostgreSQL Database

#### Option A: Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

This will start a PostgreSQL container with the following credentials:
- Database: kerala_sellers_support
- User: postgres
- Password: postgres
- Port: 5432

#### Option B: Using Local PostgreSQL

Install PostgreSQL and create the database:

```bash
sudo -u postgres psql
CREATE DATABASE kerala_sellers_support;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kerala_sellers_support TO postgres;
\q
```

#### Option C: Using SQLite (Development Only)

Update your `.env` file:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Start Development Server

```bash
python manage.py runserver
```

The server will start at `http://localhost:8000/`

## Accessing the Admin Interface

1. Navigate to `http://localhost:8000/admin/`
2. Log in with your superuser credentials
3. You can now manage all models through the admin interface

### Admin Features

- **Orders**: View and manage order status, tracking information
- **Return Requests**: Process returns and refunds
- **Support Conversations**: Monitor customer support sessions
- **Support Messages**: View conversation history
- **Policies**: Manage bilingual policy content

## Database Migration Commands

### Create Migrations

```bash
python manage.py makemigrations
```

### Apply Migrations

```bash
python manage.py migrate
```

### Show Migrations

```bash
python manage.py showmigrations
```

### Rollback Migrations

```bash
python manage.py migrate support 0001  # Rollback to specific migration
```

## Testing in Django Shell

Test model creation and relationships:

```bash
python manage.py shell
```

```python
from support.models import Order, ReturnRequest, SupportConversation, SupportMessage, Policy
from django.utils import timezone
from decimal import Decimal

# Create an Order
order = Order.objects.create(
    order_id='ORD-001',
    user_id='USER-123',
    status='placed',
    estimated_delivery=timezone.now() + timezone.timedelta(days=5)
)

# Create a Return Request
return_request = ReturnRequest.objects.create(
    return_id='RET-001',
    order=order,
    product_id='PROD-456',
    reason='damaged',
    status='requested',
    refund_amount=Decimal('1500.00')
)

# Create a Support Conversation
conversation = SupportConversation.objects.create(
    user_id='USER-123',
    language='en'
)

# Create a Support Message
message = SupportMessage.objects.create(
    conversation=conversation,
    sender='user',
    message='Where is my order?',
    language_detected='en',
    query_type='order_status'
)

# Create a Policy
policy = Policy.objects.create(
    policy_type='refund_policy',
    content_en='Refunds will be processed within 7-10 business days.',
    content_ml='7-10 പ്രവൃത്തി ദിവസങ്ങൾക്കുള്ളിൽ റീഫണ്ട് പ്രോസസ്സ് ചെയ്യപ്പെടും.',
    version=1
)

# Test relationships
print(f"Order: {order.order_id}")
print(f"Returns: {order.returns.count()}")
print(f"Conversation: {conversation.session_id}")
print(f"Messages: {conversation.messages.count()}")
```

## API Endpoints (Coming in Task 2)

The following endpoints will be implemented in future tasks:

- `GET /api/orders/` - List orders
- `GET /api/orders/{id}/` - Order details
- `POST /api/returns/` - Create return request
- `GET /api/conversations/` - List conversations
- `POST /api/messages/` - Create message
- `GET /api/policies/` - List policies

## Development Workflow

1. Make changes to models in `support/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Test in Django shell or admin interface
5. Commit changes including migration files

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| DEBUG | Enable debug mode | True/False |
| SECRET_KEY | Django secret key | random-string |
| DB_ENGINE | Database engine | django.db.backends.postgresql |
| DB_NAME | Database name | kerala_sellers_support |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | your_password |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. Check PostgreSQL is running: `docker-compose ps` or `sudo systemctl status postgresql`
2. Verify credentials in `.env` match your database setup
3. Test connection: `psql -h localhost -U postgres -d kerala_sellers_support`

### Migration Issues

If migrations fail:

1. Check for syntax errors in models
2. Try: `python manage.py migrate --fake-initial`
3. Reset migrations if needed (development only):
   ```bash
   python manage.py migrate support zero
   rm support/migrations/0*.py
   python manage.py makemigrations
   python manage.py migrate
   ```

### Import Errors

If you get import errors:

1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.10+)

## Next Steps

This setup completes Task 1 (Database Schema & Django Setup). Future tasks will include:

- **Task 2**: REST API endpoints and views
- **Task 3**: AI integration for customer support
- **Task 4**: Language detection and translation
- **Task 5**: Authentication and permissions
- **Task 6**: Testing and deployment

## Contributing

When making changes:

1. Create a new branch for your feature
2. Make changes and test thoroughly
3. Create migrations if models changed
4. Update this README if needed
5. Submit pull request with clear description

## License

[Your License Here]

## Support

For issues or questions, please contact [Your Contact Info]
