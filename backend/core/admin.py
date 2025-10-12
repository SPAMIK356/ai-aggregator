from django.contrib import admin
from django import forms
from django.conf import settings as dj_settings

from .models import AuthorColumn, NewsItem, NewsSource, OutboxEvent, TelegramChannel, WebsiteSource, RewriterConfig, KeywordFilter, ParserConfig, SitePage, Hashtag, SocialLink, AdBanner


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
	list_display = ("title", "url", "is_active", "created_at")
	list_filter = ("is_active",)
	search_fields = ("title", "url")


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
	list_display = ("title", "source_name", "theme", "published_at", "created_at")
	list_filter = ("source_name", "theme")
	search_fields = ("title", "original_url", "source_name")
	readonly_fields = ("created_at", "updated_at")
	filter_horizontal = ("hashtags",)
	fields = ("title", "original_url", "description", "published_at", "source_name", "theme", "hashtags", "image_url", "image_file", "created_at", "updated_at")


@admin.register(AuthorColumn)
class AuthorColumnAdmin(admin.ModelAdmin):
	list_display = ("title", "author_name", "theme", "published_at", "created_at")
	search_fields = ("title", "author_name")
	readonly_fields = ("created_at", "updated_at")
	filter_horizontal = ("hashtags",)
	fields = ("title", "author_name", "content_body", "published_at", "theme", "hashtags", "image_url", "image_file", "created_at", "updated_at")


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
	list_display = ("username", "title", "is_active", "default_theme", "last_message_id", "updated_at")
	list_filter = ("is_active", "default_theme")
	search_fields = ("username", "title")


@admin.register(WebsiteSource)
class WebsiteSourceAdmin(admin.ModelAdmin):
	list_display = ("name", "url", "is_active", "default_theme", "created_at")
	list_filter = ("is_active", "default_theme")
	search_fields = ("name", "url")
	fields = ("name", "url", "is_active", "default_theme", "list_selector", "title_selector", "url_selector", "desc_selector", "image_selector")


@admin.register(RewriterConfig)
class RewriterConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "model", "max_output_tokens", "updated_at")


@admin.register(KeywordFilter)
class KeywordFilterAdmin(admin.ModelAdmin):
	list_display = ("phrase", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("phrase",)


@admin.register(ParserConfig)
class ParserConfigAdmin(admin.ModelAdmin):
	list_display = ("is_enabled", "min_chars", "updated_at")
	readonly_fields = ("created_at", "updated_at")


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


@admin.register(AdBanner)
class AdBannerAdmin(admin.ModelAdmin):
	list_display = ("name", "is_active", "weight", "updated_at")
	list_filter = ("is_active",)
	readonly_fields = ("created_at", "updated_at")
	search_fields = ("name", "url")
	fields = ("name", "url", "image", "is_active", "weight", "created_at", "updated_at")
