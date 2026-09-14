# Eduverse

Eduverse is a full-stack eLearning web application built with Django. It supports two
distinct user roles — **students** and **teachers** — with role-based permissions, course
management, a social feed, real-time chat over WebSockets, and a documented REST API.

## Demo Video
Watch the demonstration [here](https://youtu.be/mbiBiYKImi8).

---

## Features

| # | Requirement | Where it lives |
|---|---|---|
| a | Password-secured account creation | `apps/users` — `register_view`, custom `User` model |
| b | Two account types (student / teacher) with different permissions | `apps/users` — `role` field + Django auth `Group`s (`Student`, `Teacher`) |
| c | Rich user profiles (name, photo, bio, etc.) | `apps/users` — `User`, `StudentProfile`, `TeacherProfile` |
| d | Discoverable home pages with status updates | `apps/users` — `user_detail_view` + `apps/feed` |
| e | Students post status updates | `apps/feed` — `Feed`, `FeedComment` |
| f | Students leave course feedback | `apps/courses` — `CourseFeedback` |
| g | Teachers search students/teachers | `apps/users` — `user_search_view` |
| h | Teachers create courses & upload materials | `apps/courses` — `Course`, `CourseMaterial`, `CourseMaterialAttachment` |
| i | Teachers view enrolled students; block/remove students | `apps/courses` — `course_students_view`, `block_student_view`, `Enrollment.status` |
| j | Students browse and enrol in courses | `apps/courses` — `course_list_view`, `enrol_view` |
| k | Real-time communication via WebSockets | `apps/chat` — Django Channels consumer, per-course auto-created chat rooms |
| l | REST interface for User data | `apps/api` — Django REST Framework + drf-spectacular |

Additional functionality built on top of the core requirements:

- Auto-created chat room per course (teacher + enrolled students added automatically)
- Student-started chat rooms with classmate/teacher invites
- File attachments in chat (uploaded via HTTP, broadcast live over the channel layer)
- In-app notification system (enrolment, new course material, new chat messages, feed comments)
- Global search on courses, users, and feed posts
- Paginated feed, course lists, and notification dropdown
- Interactive OpenAPI docs via Swagger UI

---

## Tech Stack

- **Backend:** Django 5.x, Django Channels (WebSockets), Django REST Framework
- **API docs:** drf-spectacular (OpenAPI 3 schema + Swagger UI)
- **Database:** PostgreSQL
- **Real-time layer:** Django Channels, in-memory channel layer by default (Redis-ready)
- **ASGI server:** Daphne
- **Frontend:** Django templates, Bootstrap 5, vanilla JS (no frontend framework)

---

## Project Structure

```
eduverse/
├── manage.py
├── requirements.txt
├── .env
├── config/                    # project settings & routing
│   ├── asgi.py                # ASGI entrypoint (HTTP + WebSocket routing)
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
└── apps/
    ├── users/                 # custom User model, auth, profiles, dashboard
    ├── courses/                # courses, materials, enrollment, feedback
    ├── feed/                  # status updates, comments, notifications
    ├── chat/                  # chat rooms, messages, WebSocket consumer
    └── api/
        └── v1/
            ├── users/
            ├── courses/
            ├── feed/
            └── chat/
```

Each domain app owns its own `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`,
and templates. `apps/api` is routing-only at the top level; actual serializers and API
views live inside each `apps/api/v1/<app>/` sub-package, grouped by domain rather than
dumped into one monolithic API app.

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip / virtualenv

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd eduverse
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Key packages installed:

```
Django
psycopg2-binary
django-bootstrap5
channels
channels-redis
daphne
djangorestframework
drf-spectacular
python-dotenv
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DB_NAME=eduverse_db
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Create the PostgreSQL database

```sql
CREATE DATABASE eduverse_db;
```

### 5. Apply migrations

```bash
python manage.py migrate
```

This also runs the data migration that creates the **Teacher** and **Student**
permission groups (`apps/users/migrations/0003_create_groups.py`).

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

`python manage.py runserver` also works for local development, since Channels patches
it to be ASGI-aware — use `daphne` explicitly for anything closer to production.

Visit `http://127.0.0.1:8000/`.

---

## Real-Time Chat & Redis

WebSocket support is powered by **Django Channels**. By default, this project uses
`channels.layers.InMemoryChannelLayer`, which requires **no external services** and
works out of the box for a single-process deployment (e.g. local development or a
single-worker demo).

```python
# config/settings/dev.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}
```

If you deploy with **multiple worker processes**, switch to Redis so messages can be
broadcast across processes:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")],
        },
    }
}
```

A local Redis instance can be started with:

```bash
docker run -p 6379:6379 redis
```

---

## Roles & Permissions

Two Django auth `Group`s are created automatically via a data migration:

- **Student** — can enrol in courses, post/comment on the feed, leave course feedback,
  start chat rooms, view course materials.
- **Teacher** — can create/edit/delete their own courses, upload materials, view and
  block enrolled students, manage their own chat rooms.

New users are automatically assigned to the correct group on registration via a
`post_save` signal (`apps/users/signals.py`). Object-level ownership (e.g. "a teacher
can only edit *their own* course") is enforced in view logic on top of these group
permissions, since Django's built-in permission system only expresses model-level
access, not per-object ownership.

---

## REST API

Interactive API documentation is available once the server is running:

- **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
- **Raw OpenAPI schema:** `http://127.0.0.1:8000/api/schema/`

All endpoints are namespaced under `/api/v1/`, grouped by domain:

```
/api/v1/users/            # user profiles, search, "me" endpoint
/api/v1/courses/          # courses, enrollments
/api/v1/feed/             # posts, comments, notifications
/api/v1/chat/             # chat rooms, messages, members
```

Authentication uses Django's session authentication — log in via the normal web UI
(`/users/login/`) and the same session is used for API requests.

---

## Running Tests

```bash
python manage.py test
```

Test suites are included for each app (`apps/*/tests.py`), covering:

- Custom user manager and role-based group assignment
- Registration, login, and profile view permissions
- Course ownership, enrollment constraints, and blocking students
- Feed post/comment creation and notification triggers
- Auto-created chat rooms, membership signals, and access control
- REST API permission boundaries (ownership, role restrictions)

---

## Media Files

User-uploaded content (profile photos, course materials, chat attachments) is stored
under `media/` and served via Django in development:

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

In production, this should be handled by a dedicated web server or object storage
(e.g. nginx, S3) rather than Django itself.

---

## License

This project was built as part of a coursework assignment and is provided as-is for
educational purposes.
