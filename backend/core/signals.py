from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuthorColumn, NewsItem, OutboxEvent


@dataclass
class CreatedEvent:
	post_type: str
	id: int
	title: str
	body: str
	image_url: str

	def to_payload(self) -> Dict[str, str]:
		return asdict(self)


def enqueue_outbox(event_type: str, payload: Dict) -> None:
	OutboxEvent.objects.create(event_type=event_type, payload=payload)


@receiver(post_save, sender=NewsItem)
def on_newsitem_created(sender, instance: NewsItem, created: bool, **kwargs):
	if not created:
		return
	# Prevent duplicate outbox events for the same news item
	# Check recent events (last 1000) to avoid scanning entire table
	try:
		recent_events = OutboxEvent.objects.filter(
			event_type=OutboxEvent.EVENT_NEWS_CREATED
		).order_by("-created_at")[:1000]
		for evt in recent_events:
			try:
				if (evt.payload or {}).get("id") == instance.pk:
					return  # Already have an event for this news item
			except (TypeError, AttributeError):
				pass
	except Exception:
		pass  # If check fails, proceed with creating event
	img = instance.image_url or ""
	if not img:
		try:
			if instance.image_file:
				img = instance.image_file.url  # type: ignore[attr-defined]
		except Exception:
			img = ""
	payload = CreatedEvent(
		post_type="news",
		id=instance.pk,
		title=instance.title,
		body=instance.description or "",
		image_url=img,
	).to_payload()
	enqueue_outbox(OutboxEvent.EVENT_NEWS_CREATED, payload)


@receiver(post_save, sender=AuthorColumn)
def on_authorcolumn_created(sender, instance: AuthorColumn, created: bool, **kwargs):
	if not created:
		return
	# Prevent duplicate outbox events for the same column
	try:
		recent_events = OutboxEvent.objects.filter(
			event_type=OutboxEvent.EVENT_COLUMN_CREATED
		).order_by("-created_at")[:1000]
		for evt in recent_events:
			try:
				if (evt.payload or {}).get("id") == instance.pk:
					return  # Already have an event for this column
			except (TypeError, AttributeError):
				pass
	except Exception:
		pass
	img = instance.image_url or ""
	if not img:
		try:
			if instance.image_file:
				img = instance.image_file.url  # type: ignore[attr-defined]
		except Exception:
			img = ""
	payload = CreatedEvent(
		post_type="column",
		id=instance.pk,
		title=instance.title,
		body=instance.content_body or "",
		image_url=img,
	).to_payload()
	enqueue_outbox(OutboxEvent.EVENT_COLUMN_CREATED, payload)


