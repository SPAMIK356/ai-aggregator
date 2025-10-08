from __future__ import annotations

import json
from typing import Dict, Optional, List
import re
import time

import logging
from django.conf import settings
from openai import OpenAI
from openai import BadRequestError, APITimeoutError, RateLimitError

from .models import RewriterConfig, Hashtag


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


def rewrite_article(title: str, content: str) -> Optional[Dict[str, object]]:
	cfg = get_active_config()
	if not cfg:
		return None
	api_key = getattr(settings, "OPENAI_API_KEY", None)
	if not api_key:
		return None

	# Configurable
	base_url = getattr(settings, "OPENAI_BASE_URL", None)
	base_timeout = float(getattr(settings, "REWRITER_TIMEOUT", 30.0))
	max_timeout = float(getattr(settings, "REWRITER_MAX_TIMEOUT", 90.0))
	attempts = int(getattr(settings, "REWRITER_ATTEMPTS", 6))
	backoff = float(getattr(settings, "REWRITER_BACKOFF_SECONDS", 5.0))
	logger = logging.getLogger(__name__)

	system_prompt = cfg.prompt or (
		"You rewrite and clean AI/crypto articles into concise Russian. Return json with keys 'title', 'content', and 'hashtags' (array of slugs). Hashtags must be chosen ONLY from the allowed set provided."
	)
	# Ensure the word 'json' (lowercase) is present to satisfy response_format requirements
	if "json" not in system_prompt.lower():
		system_prompt = system_prompt.strip() + " Return json object with keys 'title' and 'content'."
	# No trimming by env; send full content (API timeouts still apply)
	# Provide active hashtag slugs as the allowed enum set
	allowed = list(Hashtag.objects.filter(is_active=True).values_list("slug", flat=True))
	user_payload = {
		"title": title,
		"content": content,
		"allowed_hashtags": allowed,
	}

	last_err: Optional[Exception] = None
	for i in range(attempts):
		attempt_timeout = min(base_timeout * (2 ** i), max_timeout)
		client = OpenAI(api_key=api_key, timeout=attempt_timeout, max_retries=0, base_url=base_url)
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
			out = {"title": data.get("title") or title, "content": data.get("content") or content}
			if isinstance(data.get("hashtags"), list):
				out["hashtags"] = [str(s).strip().lower() for s in data.get("hashtags") if s]
			return out
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
					out = {"title": data.get("title") or title, "content": data.get("content") or content}
					if isinstance(data.get("hashtags"), list):
						out["hashtags"] = [str(s).strip().lower() for s in data.get("hashtags") if s]
					return out
				except Exception as e2:
					last_err = e2
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
				out = {"title": data.get("title") or title, "content": data.get("content") or content}
				if isinstance(data.get("hashtags"), list):
					out["hashtags"] = [str(s).strip().lower() for s in data.get("hashtags") if s]
				return out
			except Exception as e3:
				last_err = e3
		except (APITimeoutError, RateLimitError) as e:
			last_err = e
			logger.warning("Rewriter transient error (attempt %s/%s, timeout=%ss): %s", i+1, attempts, int(attempt_timeout), e)
		except Exception as e:
			last_err = e
			logger.exception("Rewriter unexpected error: %s", e)
		# Backoff before next attempt
		if i < attempts - 1:
			time.sleep(backoff * (2 ** i))

	logger.error("Rewriter failed after %s attempts: %s", attempts, last_err)
	return None


