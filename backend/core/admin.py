from django.contrib import admin

from .models import AuthorColumn, NewsItem, NewsSource, OutboxEvent, TelegramChannel, WebsiteSource, RewriterConfig, KeywordFilter, ParserConfig, SitePage


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
	list_display = ("title", "url", "is_active", "created_at")
	list_filter = ("is_active",)
	search_fields = ("title", "url")


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
	list_display = ("title", "source_name", "published_at", "created_at")
	list_filter = ("source_name",)
	search_fields = ("title", "original_url", "source_name")
	readonly_fields = ("created_at", "updated_at")
	fields = ("title", "original_url", "description", "published_at", "source_name", "image_url", "image_file", "created_at", "updated_at")


@admin.register(AuthorColumn)
class AuthorColumnAdmin(admin.ModelAdmin):
	list_display = ("title", "author_name", "published_at", "created_at")
	search_fields = ("title", "author_name")
	readonly_fields = ("created_at", "updated_at")
	fields = ("title", "author_name", "content_body", "published_at", "image_url", "image_file", "created_at", "updated_at")


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
	list_display = ("username", "title", "is_active", "last_message_id", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("username", "title")


@admin.register(WebsiteSource)
class WebsiteSourceAdmin(admin.ModelAdmin):
	list_display = ("name", "url", "is_active", "created_at")
	list_filter = ("is_active",)
	search_fields = ("name", "url")
	fields = ("name", "url", "is_active", "list_selector", "title_selector", "url_selector", "desc_selector", "image_selector")


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


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
	list_display = ("slug", "title", "updated_at")
	search_fields = ("slug", "title")
	readonly_fields = ("created_at", "updated_at")
