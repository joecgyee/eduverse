"""
URL configuration for eduverse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Apps
    path('', include(('apps.core.urls', 'core'), namespace='core')),
    path('users/', include(('apps.users.urls', 'users'), namespace='users')),
    path('courses/', include(('apps.courses.urls', 'courses'), namespace='courses')),
    path('feed/', include(('apps.feed.urls', 'feed'), namespace='feed')),
    path('chat/', include(('apps.chat.urls', 'chat'), namespace='chat')),

    path('api/', include(('apps.api.urls', 'api'), namespace='api')),
    # OpenAPI schema + interactive docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Serve user-uploaded media files during development only.
# In production, a real webserver (nginx, etc.) or cloud storage handles this instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)