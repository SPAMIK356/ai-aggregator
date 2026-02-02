from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict

from django.db import transaction
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


def enqueue_outbox_if_not_exists(event_type: str, payload: Dict, item_id: int) -> bool:
	"""Create an OutboxEvent only if one doesn't already exist for this item.
	
	Uses database-level locking to prevent race conditions.
	Returns True if event was created, False if it already existed.
	"""
	try:
		with transaction.atomic():
			# Check if an event already exists for this item ID
			# Use select_for_update to prevent race conditions
			existing = OutboxEvent.objects.filter(
				event_type=event_type
			).select_for_update(skip_locked=True)
			
			for evt in existing:
				try:
					evt_id = (evt.payload or {}).get("id")
					if evt_id is not None and int(evt_id) == int(item_id):
						logger.debug("OutboxEvent already exists for %s id=%d", event_type, item_id)
						return False
				except (TypeError, ValueError, AttributeError):
					continue
			
			# No existing event found, create new one
			OutboxEvent.objects.create(event_type=event_type, payload=payload)
			logger.info("Created OutboxEvent for %s id=%d", event_type, item_id)
			return True
	except Exception as e:
		logger.exception("Error in enqueue_outbox_if_not_exists: %s", e)
		# Fallback: try to create anyway (might cause duplicate, but better than losing event)
		try:
			OutboxEvent.objects.create(event_type=event_type, payload=payload)
			return True
		except Exception:
			return False


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
	
	enqueue_outbox_if_not_exists(OutboxEvent.EVENT_NEWS_CREATED, payload, instance.pk)


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
	
	enqueue_outbox_if_not_exists(OutboxEvent.EVENT_COLUMN_CREATED, payload, instance.pk)


