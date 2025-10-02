from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy", "debug": settings.DEBUG})


def api_root(request):
    """API root endpoint."""
    return JsonResponse(
        {
            "message": "Система анализа полетов БАС API",
            "version": "1.0.0",
            "endpoints": {
                "admin": f"/{settings.ADMIN_URL}",
                "health": "/health/",
                "api": "/api/",
                "flights_api": "/api/flights/",
                "flights_api_v1": "/api/v1/flights/",
                "docs": "/api/docs/" if settings.DEBUG else None,
                "schema": "/api/schema/" if settings.DEBUG else None,
                "redoc": "/api/redoc/" if settings.DEBUG else None,
            },
        }
    )


urlpatterns = [
    path("", api_root, name="api_root"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("health/", health_check, name="health_check"),
    path("api/v1/flights/", include("apps.flights.api_urls", namespace="flights_api")),
]

# API Documentation URLs (only in DEBUG mode)
if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar (условно)
    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
    except ImportError:
        pass

# Custom error handlers for production
if not settings.DEBUG:
    from django.views.generic import TemplateView

    handler404 = TemplateView.as_view(template_name="404.html")
    handler500 = TemplateView.as_view(template_name="500.html")
