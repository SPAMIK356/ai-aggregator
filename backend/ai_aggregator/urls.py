from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def health(_request):
	return JsonResponse({"status": "ok"})


urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/", include("core.urls")),
	path("health/", health),
]

# Serve MEDIA files in all environments for MVP (containerized deployment)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


