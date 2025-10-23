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
	# Skip Telegram-origin items so the bot posts only site news
	orig = (instance.original_url or "").lower()
	if "t.me/" in orig or "telegram." in orig:
		return
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


