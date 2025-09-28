from django.apps import AppConfig


class CoreConfig(AppConfig):
	default_auto_field = "django.db.models.BigAutoField"
	name = "core"

	def ready(self) -> None:
		# Import signals on app ready
		from . import signals  # noqa: F401
		return super().ready()


