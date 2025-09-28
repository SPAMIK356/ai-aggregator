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

	def __str__(self) -> str:
		return self.title or self.url


class NewsItem(TimeStampedModel):
	title = models.CharField(max_length=500)
	original_url = models.URLField(unique=True)
	description = models.TextField(blank=True)
	published_at = models.DateTimeField(default=timezone.now, db_index=True)
	source_name = models.CharField(max_length=255, blank=True)

	def __str__(self) -> str:
		return self.title


class AuthorColumn(TimeStampedModel):
	title = models.CharField(max_length=500)
	author_name = models.CharField(max_length=255)
	content_body = models.TextField()
	published_at = models.DateTimeField(default=timezone.now, db_index=True)

	def __str__(self) -> str:
		return f"{self.title} — {self.author_name}"


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

	def __str__(self) -> str:
		return self.title or self.username


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

	def __str__(self) -> str:
		return self.name


