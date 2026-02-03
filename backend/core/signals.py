from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuthorColumn, NewsItem, OutboxEvent

logger = logging.getLogger(__name__)


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
	"""Create an OutboxEvent. Deduplication is handled in deliver_outbox via telegram_sent_at."""
	OutboxEvent.objects.create(event_type=event_type, payload=payload)


@receiver(post_save, sender=NewsItem)
def on_newsitem_created(sender, instance: NewsItem, created: bool, **kwargs):
	if not created:
		return
	
	img = instance.image_url or ""
	if not img:
		try:
			if instance.image_file:
				img = instance.image_file.url
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
	logger.debug("Created OutboxEvent for news id=%d", instance.pk)


@receiver(post_save, sender=AuthorColumn)
def on_authorcolumn_created(sender, instance: AuthorColumn, created: bool, **kwargs):
	if not created:
		return
	
	img = instance.image_url or ""
	if not img:
		try:
			if instance.image_file:
				img = instance.image_file.url
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
	logger.debug("Created OutboxEvent for column id=%d", instance.pk)


