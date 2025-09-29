from __future__ import annotations

import json
from typing import Dict, Optional
import re

import logging
from django.conf import settings
from openai import OpenAI
from openai import BadRequestError, APITimeoutError, RateLimitError

from .models import RewriterConfig


def get_active_config() -> Optional[RewriterConfig]:
    # Global kill switch via env
    from django.conf import settings as dj_settings
    if not getattr(dj_settings, "REWRITER_ENABLED", False):
        return None
    cfg = RewriterConfig.objects.order_by("-updated_at").first()
    return cfg if cfg and cfg.is_enabled else None


def _lenient_json_parse(text: str) -> Optional[Dict[str, str]]:
	"""Attempts to parse JSON even if the model wrapped it or added prose."""
	try:
		# Fast path
		return json.loads(text)
	except Exception:
		pass
	# Extract the first top-level {...}
	start = text.find("{")
	end = text.rfind("}")
	if start != -1 and end != -1 and end > start:
		maybe = text[start : end + 1]
		try:
			return json.loads(maybe)
		except Exception:
			return None
	return None


def rewrite_article(title: str, content: str) -> Optional[Dict[str, str]]:
	cfg = get_active_config()
	if not cfg:
		return None
	api_key = getattr(settings, "OPENAI_API_KEY", None)
	if not api_key:
		return None

	# Short timeouts and a couple of retries; all configurable
	timeout = float(getattr(settings, "REWRITER_TIMEOUT", 20.0))
	base_url = getattr(settings, "OPENAI_BASE_URL", None)
	client = OpenAI(api_key=api_key, timeout=timeout, max_retries=2, base_url=base_url)
	logger = logging.getLogger(__name__)

	system_prompt = cfg.prompt or (
		"You rewrite and clean AI-related articles into concise Russian. Return json with keys 'title' and 'content'."
	)
	# Ensure the word 'json' (lowercase) is present to satisfy response_format requirements
	if "json" not in system_prompt.lower():
		system_prompt = system_prompt.strip() + " Return json object with keys 'title' and 'content'."
	# Truncate to avoid excessive payload timeouts; configurable
	max_chars = int(getattr(settings, "REWRITER_MAX_CHARS", 4000))
	trimmed_content = content[:max_chars]
	user_payload = {
		"title": title,
		"content": trimmed_content,
	}

	try:
		# Primary attempt: enforce JSON mode
		response = client.chat.completions.create(
			model=cfg.model,
			messages=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
			],
			response_format={"type": "json_object"},
		)
		text = response.choices[0].message.content or "{}"
		data = _lenient_json_parse(text) or {}
		return {"title": data.get("title") or title, "content": data.get("content") or content}
	except BadRequestError as e:
		msg = str(e)
		logger.warning("Rewriter BadRequest on model=%s: %s", cfg.model, msg)
		# Try fallback model if model seems invalid
		fallback_model = getattr(settings, "REWRITER_FALLBACK_MODEL", "gpt-4o-mini")
		if "model" in msg.lower() or "does not exist" in msg.lower() or "unknown" in msg.lower():
			try:
				response = client.chat.completions.create(
					model=fallback_model,
					messages=[
						{"role": "system", "content": system_prompt},
						{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
					],
					response_format={"type": "json_object"},
				)
				text = response.choices[0].message.content or "{}"
				data = _lenient_json_parse(text) or {}
				return {"title": data.get("title") or title, "content": data.get("content") or content}
			except Exception as e2:
				logger.warning("Rewriter fallback model failed: %s", e2)
		# Fallback attempt: no response_format, but still ask for JSON in the prompt
		try:
			response = client.chat.completions.create(
				model=cfg.model,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
				],
			)
			text = response.choices[0].message.content or "{}"
			data = _lenient_json_parse(text) or {}
			return {"title": data.get("title") or title, "content": data.get("content") or content}
		except Exception:
			return None
	except (APITimeoutError, RateLimitError) as e:
		logger.warning("Rewriter transient error: %s", e)
		return None
	except Exception as e:
		logger.exception("Rewriter unexpected error: %s", e)
		return None


