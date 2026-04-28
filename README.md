# SprintBoard — Agile Project Management API

A production-ready REST API for sprint-based project management, built with **Django 5.1**, **Django REST Framework**, and **PostgreSQL**.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Django 5.1, Django REST Framework 3.15 |
| **Database** | PostgreSQL 16 (via psycopg3) |
| **Auth** | JWT (SimpleJWT) with token rotation & blacklisting |
| **Task Queue** | Celery + Redis |
| **API Docs** | OpenAPI 3.0 via drf-spectacular (Swagger + ReDoc) |
| **Testing** | pytest-django + factory_boy |
| **Deployment** | Docker, docker-compose, Gunicorn, WhiteNoise |

## Architecture

```
config/
├── settings/          # Split settings (base/dev/prod)
├── urls.py            # Root URL conf with API versioning
├── celery.py          # Celery app configuration
├── wsgi.py / asgi.py
apps/
├── accounts/          # Custom User model (email auth), JWT, RBAC
│   ├── models.py      # UUID PK, role-based users
│   ├── serializers.py # Registration, profile, custom JWT claims
│   ├── permissions.py # IsAdmin, IsManagerOrAdmin, IsOwnerOrReadOnly
│   └── tests/
├── projects/          # Core domain: Projects, Sprints, Tasks
│   ├── models.py      # Project, Membership, Sprint, Task, Comment, ActivityLog
│   ├── serializers.py # Nested serializers with computed fields
│   ├── views.py       # ViewSets with dashboard, sprint lifecycle, task transitions
│   ├── signals.py     # Auto-generated audit trail
│   ├── filters.py     # Advanced filtering (django-filter)
│   ├── tasks.py       # Celery: overdue flagging, async notifications
│   └── tests/
```

## Key Features

- **Custom User Model** — Email-based auth with roles (admin/manager/developer)
- **JWT Authentication** — Access + refresh tokens with rotation and blacklisting
- **Role-Based Access Control** — Custom permissions per endpoint
- **Sprint Management** — Start/complete lifecycle with velocity tracking
- **Task Board** — Full CRUD with status transitions, assignment, and priority
- **Activity Audit Trail** — Auto-generated via Django signals on task events
- **Comments** — Threaded discussion on tasks
- **Advanced Filtering** — By status, priority, assignee, sprint, labels, due date
- **Periodic Tasks** — Celery beat for overdue task detection
- **API Documentation** — Auto-generated Swagger UI + ReDoc

## Quick Start

```bash
# Clone and set up
git clone https://github.com/Lostinaa/sprintboard.git
cd sprintboard

# Environment
cp .env.example .env

# Docker (recommended)
docker-compose up -d

# Or local setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data   # populate sample data
python manage.py runserver
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/login/` | Obtain JWT tokens |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| GET/PATCH | `/api/v1/auth/profile/` | View/update profile |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/projects/` | List/create projects |
| GET/PUT/DELETE | `/api/v1/projects/{slug}/` | Project detail |
| GET | `/api/v1/projects/{slug}/dashboard/` | Aggregated metrics |
| POST | `/api/v1/projects/{slug}/add-member/` | Add team member |

### Sprints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/projects/{slug}/sprints/` | List/create sprints |
| POST | `/api/v1/projects/{slug}/sprints/{id}/start/` | Activate sprint |
| POST | `/api/v1/projects/{slug}/sprints/{id}/complete/` | Complete sprint |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/projects/{slug}/tasks/` | List/create tasks |
| POST | `/api/v1/projects/{slug}/tasks/{id}/transition/` | Change status |
| POST | `/api/v1/projects/{slug}/tasks/{id}/assign/` | Assign task |

### Documentation
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

## Running Tests

```bash
pytest
pytest --cov=apps --cov-report=html
```

## License

MIT
