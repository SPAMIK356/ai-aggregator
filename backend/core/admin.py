from django.contrib import admin
from django import forms
from django.conf import settings as dj_settings
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .models import (
	AuthorColumn,
	NewsItem,
	NewsSource,
	OutboxEvent,
	TelegramChannel,
	WebsiteSource,
	RewriterConfig,
	TelegramRewriterConfig,
	AdClassifierConfig,
	TranslatorConfig,
	ImageGeneratorConfig,
	KeywordFilter,
	ParserConfig,
	SitePage,
	Hashtag,
	SocialLink,
	AdBanner,
	LinkFilter,
)


@admin.action(description="Activate selected")
def mark_active(modeladmin, request, queryset):
	updated = queryset.update(is_active=True)
	modeladmin.message_user(request, f"Activated {updated} item(s)")


@admin.action(description="Deactivate selected")
def mark_inactive(modeladmin, request, queryset):
	updated = queryset.update(is_active=False)
	modeladmin.message_user(request, f"Deactivated {updated} item(s)")


@admin.action(description="Enable image parsing for selected")
def enable_parse_images(modeladmin, request, queryset):
	# Works for models that have parse_images boolean
	if not queryset.model._meta.get_field("parse_images"):
		return
	updated = queryset.update(parse_images=True)
	modeladmin.message_user(request, f"Enabled image parsing on {updated} item(s)")


@admin.action(description="Disable image parsing for selected")
def disable_parse_images(modeladmin, request, queryset):
	# Works for models that have parse_images boolean
	if not queryset.model._meta.get_field("parse_images"):
		return
	updated = queryset.update(parse_images=False)
	modeladmin.message_user(request, f"Disabled image parsing on {updated} item(s)")


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
	list_display = ("title", "url", "is_active", "parse_images", "created_at")
	list_filter = ("is_active", "parse_images")
	search_fields = ("title", "url")
	actions = (mark_active, mark_inactive, enable_parse_images, disable_parse_images)


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
	list_display = ("title", "source_name", "theme", "published_at", "created_at")
	list_filter = ("source_name", "theme")
	search_fields = ("title", "original_url", "source_name")
	readonly_fields = ("created_at", "updated_at")
	filter_horizontal = ("hashtags",)
	fieldsets = (
		(None, {"fields": ("title", "original_url", "description", "published_at", "source_name", "theme", "hashtags", "image_url", "image_file")}),
		("Russian Translation", {"fields": ("title_ru", "description_ru"), "classes": ("collapse",)}),
		("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)


@admin.register(AuthorColumn)
class AuthorColumnAdmin(admin.ModelAdmin):
	list_display = ("title", "author_name", "theme", "published_at", "created_at")
	search_fields = ("title", "author_name")
	readonly_fields = ("created_at", "updated_at")
	filter_horizontal = ("hashtags",)
	fieldsets = (
		(None, {"fields": ("title", "author_name", "content_body", "published_at", "theme", "hashtags", "image_url", "image_file")}),
		("Russian Translation", {"fields": ("title_ru", "content_body_ru"), "classes": ("collapse",)}),
		("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
	list_display = (
		"event_type",
		"created_at",
		"delivered_at",
		"delivery_attempts",
	)
	readonly_fields = ("created_at", "updated_at", "delivery_attempts")


@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
	list_display = ("username", "title", "is_active", "parse_images", "default_theme", "last_message_id", "updated_at")
	list_filter = ("is_active", "parse_images", "default_theme")
	search_fields = ("username", "title")
	actions = (mark_active, mark_inactive, enable_parse_images, disable_parse_images)


@admin.register(WebsiteSource)
class WebsiteSourceAdmin(admin.ModelAdmin):
	list_display = ("name", "url", "is_active", "parse_images", "default_theme", "created_at")
	list_filter = ("is_active", "parse_images", "default_theme")
	search_fields = ("name", "url")
	fields = ("name", "url", "is_active", "parse_images", "default_theme", "list_selector", "title_selector", "url_selector", "desc_selector", "image_selector")
	actions = (mark_active, mark_inactive, enable_parse_images, disable_parse_images)


@admin.register(RewriterConfig)
class RewriterConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "model", "max_output_tokens", "updated_at")


@admin.register(TelegramRewriterConfig)
class TelegramRewriterConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "model", "max_output_tokens", "updated_at")


@admin.register(AdClassifierConfig)
class AdClassifierConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "model", "updated_at")


@admin.register(TranslatorConfig)
class TranslatorConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "model", "updated_at")


@admin.register(ImageGeneratorConfig)
class ImageGeneratorConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "openai_model", "fal_model", "aspect_ratio", "updated_at")
	fieldsets = (
		(None, {"fields": ("is_enabled",)}),
		("OpenAI Settings (Prompt Generation)", {"fields": ("openai_model", "prompt_generator_instructions")}),
		("fal-ai Settings (Image Generation)", {"fields": ("fal_api_key", "fal_model")}),
		("Image Settings", {"fields": ("negative_prompt", "aspect_ratio", "num_inference_steps")}),
	)
	change_form_template = "admin/image_generator_change_form.html"

	def get_urls(self):
		from django.urls import path
		urls = super().get_urls()
		custom_urls = [
			path(
				"test-generation/",
				self.admin_site.admin_view(self.test_generation_view),
				name="core_imagegeneratorconfig_test",
			),
		]
		return custom_urls + urls

	def test_generation_view(self, request):
		from django.http import JsonResponse
		from .image_generator import test_image_generation
		result = test_image_generation()
		return JsonResponse(result)


@admin.register(KeywordFilter)
class KeywordFilterAdmin(admin.ModelAdmin):
	list_display = ("phrase", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("phrase",)
	actions = (mark_active, mark_inactive)


@admin.register(LinkFilter)
class LinkFilterAdmin(admin.ModelAdmin):
	list_display = ("prefix", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("prefix",)
	actions = (mark_active, mark_inactive)


@admin.register(ParserConfig)
class ParserConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "min_chars", "max_posts_per_day", "max_posts_per_source_per_day", "updated_at")
	readonly_fields = ("created_at", "updated_at")
	fieldsets = (
		(None, {"fields": ("is_enabled",)}),
		("Content Filters", {"fields": ("min_chars",)}),
		("Daily Limits", {
			"fields": ("max_posts_per_day", "max_posts_per_source_per_day"),
			"description": "Set to 0 for unlimited. Limits reset at midnight (server time)."
		}),
		("Image Settings", {"fields": ("max_image_width", "max_image_height", "image_quality")}),
		("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)


class HashtagAdminForm(forms.ModelForm):
	"""Render slug as a dropdown of allowed options to avoid manual input errors.

	Read from settings.HASHTAG_SLUG_CHOICES if provided. Accepts either:
	- ["ai", "crypto", ...] or
	- [("ai", "AI"), ("crypto", "CRYPTO"), ...]
	"""
	slug = forms.ChoiceField(choices=(), required=True)

	class Meta:
		model = Hashtag
		fields = "__all__"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		allowed = getattr(dj_settings, "HASHTAG_SLUG_CHOICES", ["ai", "crypto"]) or ["ai", "crypto"]
		choices = []
		if allowed and isinstance(allowed, (list, tuple)):
			first = allowed[0] if len(allowed) > 0 else None
			if isinstance(first, (list, tuple)) and len(first) >= 1:
				choices = [(str(a[0]), str(a[1] if len(a) > 1 else a[0])) for a in allowed]
			else:
				choices = [(str(x), str(x)) for x in allowed]
		# Ensure existing value stays selectable
		current = getattr(self.instance, "slug", None)
		if current and current not in [c[0] for c in choices]:
			choices = [(current, current)] + choices
		self.fields["slug"].choices = choices


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
	form = HashtagAdminForm
	list_display = ("slug", "name", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("slug", "name")
	actions = (mark_active, mark_inactive)


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
	list_display = ("slug", "title", "updated_at")
	search_fields = ("slug", "title")
	readonly_fields = ("created_at", "updated_at")


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
	list_display = ("name", "url", "is_active", "order", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("name", "url")
	readonly_fields = ("created_at", "updated_at")
	actions = (mark_active, mark_inactive)


@admin.register(AdBanner)
class AdBannerAdmin(admin.ModelAdmin):
	list_display = ("name", "is_active", "weight", "updated_at")
	list_filter = ("is_active",)
	readonly_fields = ("created_at", "updated_at")
	search_fields = ("name", "url")
	fields = ("name", "url", "image", "is_active", "weight", "created_at", "updated_at")
	actions = (mark_active, mark_inactive)


# ----- System Diagnostics Admin View -----

class DiagnosticsAdminView:
	"""Custom admin view for system diagnostics."""
	
	@staticmethod
	def diagnostics_view(request):
		"""Render the diagnostics page."""
		return render(request, "admin/diagnostics.html", {
			"title": "System Diagnostics",
			"site_header": admin.site.site_header,
			"site_title": admin.site.site_title,
		})
	
	@staticmethod
	def run_diagnostics_api(request):
		"""API endpoint to run diagnostics."""
		from .diagnostics import run_full_diagnostic
		
		test_title = request.GET.get("title", "Test Article: AI Breakthrough in 2024")
		test_content = request.GET.get("content", "Scientists have developed a revolutionary new algorithm that improves neural network efficiency by 50%.")
		send_telegram = request.GET.get("send_telegram", "false").lower() == "true"
		
		result = run_full_diagnostic(
			test_title=test_title,
			test_content=test_content,
			send_to_telegram=send_telegram,
		)
		return JsonResponse(result.to_dict())
	
	@staticmethod
	def cleanup_duplicates_api(request):
		"""API endpoint to clean up duplicate outbox events."""
		from django.db.models import Count
		
		deleted_count = 0
		try:
			dupes = list(OutboxEvent.objects
				.filter(delivered_at__isnull=True, event_type='news.created')
				.values('payload__id')
				.annotate(cnt=Count('id'))
				.filter(cnt__gt=1))
			
			for d in dupes:
				nid = d['payload__id']
				events = list(OutboxEvent.objects.filter(
					delivered_at__isnull=True,
					event_type='news.created',
					payload__id=nid
				).order_by('created_at'))
				for e in events[1:]:
					e.delete()
					deleted_count += 1
			
			return JsonResponse({
				"status": "success",
				"deleted_count": deleted_count,
				"duplicate_groups_found": len(dupes),
			})
		except Exception as e:
			return JsonResponse({
				"status": "error",
				"error": str(e),
			})
	
	@staticmethod
	def get_outbox_details_api(request):
		"""API endpoint to get detailed outbox status."""
		from django.db.models import Count
		from django.utils import timezone
		
		try:
			# Pending events
			pending = list(OutboxEvent.objects.filter(
				delivered_at__isnull=True
			).order_by('-created_at')[:20].values(
				'id', 'event_type', 'created_at', 'delivery_attempts', 'last_error', 'payload'
			))
			
			# Recent delivered
			delivered = list(OutboxEvent.objects.filter(
				delivered_at__isnull=False
			).order_by('-delivered_at')[:20].values(
				'id', 'event_type', 'created_at', 'delivered_at', 'delivery_attempts', 'payload'
			))
			
			# Format for JSON
			for item in pending + delivered:
				if item.get('created_at'):
					item['created_at'] = item['created_at'].isoformat()
				if item.get('delivered_at'):
					item['delivered_at'] = item['delivered_at'].isoformat()
			
			return JsonResponse({
				"pending": pending,
				"recent_delivered": delivered,
			})
		except Exception as e:
			return JsonResponse({"error": str(e)})


# Register custom URLs with the admin site
original_get_urls = admin.site.get_urls

def custom_admin_urls():
	custom_urls = [
		path('diagnostics/', staff_member_required(DiagnosticsAdminView.diagnostics_view), name='system_diagnostics'),
		path('diagnostics/run/', staff_member_required(DiagnosticsAdminView.run_diagnostics_api), name='run_diagnostics'),
		path('diagnostics/cleanup-duplicates/', staff_member_required(DiagnosticsAdminView.cleanup_duplicates_api), name='cleanup_duplicates'),
		path('diagnostics/outbox-details/', staff_member_required(DiagnosticsAdminView.get_outbox_details_api), name='outbox_details'),
	]
	return custom_urls + original_get_urls()

admin.site.get_urls = custom_admin_urls

# Customize admin site
admin.site.site_header = "News Aggregator Admin"
admin.site.site_title = "News Aggregator"
admin.site.index_title = "Dashboard"
