import os
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.static import serve as media_serve


def health(_request):
	return JsonResponse({"status": "ok"})


urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/", include("core.urls")),
	path("health/", health),
]

# Serve media in dev and optionally in containers when SERVE_MEDIA=1
if getattr(settings, "DEBUG", False) or os.getenv("SERVE_MEDIA", "1") == "1":
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Always provide a fallback explicit media route (useful in containers)
urlpatterns += [
	re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
]


