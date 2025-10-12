from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class NewsSource(TimeStampedModel):
	title = models.CharField(max_length=255, blank=True)
	url = models.URLField(unique=True)
	is_active = models.BooleanField(default=True)
	# Optional default theme to assign to items ingested from this source
	default_theme = models.CharField(max_length=16, choices=[("AI", "AI"), ("CRYPTO", "CRYPTO")], blank=True)

	def __str__(self) -> str:
		return self.title or self.url


class NewsItem(TimeStampedModel):
	title = models.CharField(max_length=500)
	original_url = models.URLField(unique=True)
	description = models.TextField(blank=True)
	published_at = models.DateTimeField(default=timezone.now, db_index=True)
	source_name = models.CharField(max_length=255, blank=True)
	image_url = models.CharField(max_length=1000, blank=True)
	image_file = models.ImageField(upload_to="news/", null=True, blank=True)

	class Theme(models.TextChoices):
		AI = "AI", "AI"
		CRYPTO = "CRYPTO", "CRYPTO"

	theme = models.CharField(max_length=16, choices=Theme.choices, default=Theme.AI, db_index=True)
	hashtags = models.ManyToManyField("Hashtag", blank=True, related_name="news_items")

	def __str__(self) -> str:
		return self.title


class AuthorColumn(TimeStampedModel):
	title = models.CharField(max_length=500)
	author_name = models.CharField(max_length=255)
	content_body = models.TextField()
	published_at = models.DateTimeField(default=timezone.now, db_index=True)
	image_url = models.CharField(max_length=1000, blank=True)
	image_file = models.ImageField(upload_to="columns/", null=True, blank=True)
	theme = models.CharField(max_length=16, choices=NewsItem.Theme.choices, default=NewsItem.Theme.AI, db_index=True)
	hashtags = models.ManyToManyField("Hashtag", blank=True, related_name="author_columns")

	def __str__(self) -> str:
		return f"{self.title} — {self.author_name}"


class Hashtag(TimeStampedModel):
	"""Admin-editable hashtag enum used to tag posts and find similar items.

	- slug: unique, lowercase stable identifier (e.g. "ai", "crypto")
	- name: display label (e.g. "ИИ", "Крипта")
	"""
	slug = models.SlugField(max_length=64, unique=True)
	name = models.CharField(max_length=128)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [models.Index(fields=["slug"])]

	def __str__(self) -> str:
		return self.name


class OutboxEvent(TimeStampedModel):
	EVENT_NEWS_CREATED = "news.created"
	EVENT_COLUMN_CREATED = "column.created"

	EVENT_CHOICES = [
		(EVENT_NEWS_CREATED, "News created"),
		(EVENT_COLUMN_CREATED, "Column created"),
	]

	event_type = models.CharField(max_length=64, choices=EVENT_CHOICES)
	payload = models.JSONField()
	delivered_at = models.DateTimeField(null=True, blank=True)
	delivery_attempts = models.PositiveIntegerField(default=0)
	last_error = models.TextField(blank=True)

	class Meta:
		indexes = [
			models.Index(fields=["created_at"]),
		]

	def mark_delivered(self) -> None:
		self.delivered_at = timezone.now()
		self.save(update_fields=["delivered_at"])


class TelegramChannel(TimeStampedModel):
	username = models.CharField(max_length=255, unique=True)
	title = models.CharField(max_length=255, blank=True)
	is_active = models.BooleanField(default=True)
	last_message_id = models.BigIntegerField(null=True, blank=True)
	# Optional default theme to assign to items from this channel
	default_theme = models.CharField(max_length=16, choices=NewsItem.Theme.choices, blank=True)

	def __str__(self) -> str:
		return self.title or self.username


class RewriterConfig(TimeStampedModel):
	"""Admin-configurable prompt and toggles for AI rewriting."""
	is_enabled = models.BooleanField(default=False)
	model = models.CharField(max_length=64, default="gpt-4o-mini")
	prompt = models.TextField(blank=True, help_text="System instructions for rewriting. Use placeholders like {title} {content}")
	max_output_tokens = models.PositiveIntegerField(default=2048)

	def __str__(self) -> str:
		return f"Rewriter ({'on' if self.is_enabled else 'off'})"


class WebsiteSource(TimeStampedModel):
	"""Generic website source with CSS selectors to extract items.

	- list_selector: CSS selector for article containers
	- title_selector: CSS selector relative to container to get title text
	- url_selector: CSS selector relative to container to get link href
	- desc_selector: optional CSS selector for description/summary
	"""
	name = models.CharField(max_length=255)
	url = models.URLField(unique=True)
	is_active = models.BooleanField(default=True)
	list_selector = models.CharField(max_length=255)
	title_selector = models.CharField(max_length=255)
	url_selector = models.CharField(max_length=255)
	desc_selector = models.CharField(max_length=255, blank=True)
	image_selector = models.CharField(max_length=255, blank=True)
	# Optional default theme to assign to items from this website
	default_theme = models.CharField(max_length=16, choices=NewsItem.Theme.choices, blank=True)

	def __str__(self) -> str:
		return self.name



class SocialLink(TimeStampedModel):
	name = models.CharField(max_length=128)
	url = models.URLField()
	icon = models.ImageField(upload_to="social/", null=True, blank=True)
	is_active = models.BooleanField(default=True)
	order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ("order", "id")

	def __str__(self) -> str:
		return self.name


class AdBanner(TimeStampedModel):
	name = models.CharField(max_length=255)
	url = models.URLField()
	image = models.ImageField(upload_to="ads/")
	is_active = models.BooleanField(default=True)
	weight = models.PositiveIntegerField(default=1)

	class Meta:
		ordering = ("-updated_at", "id")

	def __str__(self) -> str:
		return self.name


class KeywordFilter(TimeStampedModel):
	"""Global list of phrases to skip before rewriting/posting.

	If any active phrase is found (case-insensitive substring) in the original
	text of a potential news item, that item is skipped entirely.
	"""
	phrase = models.CharField(max_length=255)
	is_active = models.BooleanField(default=True)

	def __str__(self) -> str:
		return self.phrase


class ParserConfig(TimeStampedModel):
	"""Global toggle for all parsing tasks."""
	is_enabled = models.BooleanField(default=True)
	min_chars = models.PositiveIntegerField(default=0, help_text="Skip posts shorter than this many characters (0 to disable)")
	max_image_width = models.PositiveIntegerField(default=1280, help_text="Max image width in pixels (0 to disable)")
	max_image_height = models.PositiveIntegerField(default=720, help_text="Max image height in pixels (0 to disable)")
	image_quality = models.PositiveIntegerField(default=85, help_text="JPEG/WebP quality 1-95")

	def __str__(self) -> str:
		return f"Parser ({'on' if self.is_enabled else 'off'})"


class SitePage(TimeStampedModel):
	"""Simple CMS-like page content by slug (e.g., footer, about, contact)."""
	slug = models.SlugField(max_length=64, unique=True)
	title = models.CharField(max_length=255)
	body = models.TextField(blank=True)

	class Meta:
		indexes = [models.Index(fields=["slug"])]

	def __str__(self) -> str:
		return self.title

