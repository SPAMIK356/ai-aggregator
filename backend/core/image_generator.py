"""AI image generation using fal-ai API.

When ImageGeneratorConfig is enabled, this module generates images for news items
instead of using images from the parsed sources.
"""
from __future__ import annotations

import logging
import time
import requests
from io import BytesIO
from typing import Optional, Tuple
from pathlib import Path

from django.core.files.base import ContentFile

from .models import ImageGeneratorConfig

logger = logging.getLogger(__name__)

# Aspect ratio mappings for fal-ai
ASPECT_RATIO_DIMENSIONS = {
    "square": {"width": 1024, "height": 1024},
    "landscape_16_9": {"width": 1344, "height": 768},
    "landscape_4_3": {"width": 1152, "height": 896},
    "portrait_16_9": {"width": 768, "height": 1344},
    "portrait_4_3": {"width": 896, "height": 1152},
}


def get_active_image_generator_config() -> Optional[ImageGeneratorConfig]:
    """Get the active image generator config if enabled."""
    cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
    return cfg if cfg and cfg.is_enabled and cfg.api_key else None


def generate_image_for_article(
    title: str,
    content: str,
    save_path: Optional[str] = None,
) -> Optional[Tuple[str, ContentFile]]:
    """Generate an image for the given article using fal-ai.

    Args:
        title: Article title
        content: Article content/description
        save_path: Optional path hint for the saved file

    Returns:
        Tuple of (filename, ContentFile) if successful, None otherwise.
    """
    cfg = get_active_image_generator_config()
    if not cfg:
        return None

    # Build the prompt from template
    prompt_template = cfg.prompt_template or (
        "Professional digital illustration for a tech news article. "
        "Topic: {title}. Style: modern, clean, corporate, high quality. "
        "No text, no watermarks, no logos."
    )
    
    try:
        prompt = prompt_template.format(
            title=title[:200],  # Limit title length
            content=(content[:500] if content else "")  # Limit content length
        )
    except KeyError:
        # If template has invalid placeholders, use title only
        prompt = f"Professional digital illustration for a tech news article about: {title[:200]}"

    # Get dimensions for aspect ratio
    dimensions = ASPECT_RATIO_DIMENSIONS.get(
        cfg.aspect_ratio, 
        ASPECT_RATIO_DIMENSIONS["landscape_16_9"]
    )

    # fal-ai API endpoint
    api_url = f"https://fal.run/{cfg.model}"
    
    headers = {
        "Authorization": f"Key {cfg.api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "prompt": prompt,
        "image_size": dimensions,
        "num_inference_steps": cfg.num_inference_steps,
        "num_images": 1,
        "enable_safety_checker": True,
    }
    
    # Add negative prompt if specified
    if cfg.negative_prompt:
        payload["negative_prompt"] = cfg.negative_prompt

    # Retry logic with backoff
    max_attempts = 3
    backoff = 2.0
    last_error: Optional[Exception] = None

    for attempt in range(max_attempts):
        try:
            logger.info(
                "Generating image (attempt %d/%d) for: %s",
                attempt + 1, max_attempts, title[:50]
            )
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120,  # Image generation can take time
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # fal-ai returns images in different formats depending on model
                images = result.get("images") or result.get("output") or []
                if not images:
                    logger.warning("No images in fal-ai response: %s", result)
                    continue
                
                # Get the first image
                image_data = images[0] if isinstance(images, list) else images
                image_url = (
                    image_data.get("url") 
                    if isinstance(image_data, dict) 
                    else image_data
                )
                
                if not image_url:
                    logger.warning("No image URL in response: %s", image_data)
                    continue
                
                # Download the image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code != 200:
                    logger.warning(
                        "Failed to download generated image: %d",
                        img_response.status_code
                    )
                    continue
                
                # Determine filename
                content_type = img_response.headers.get("content-type", "image/png")
                ext = "png" if "png" in content_type else "jpg"
                
                # Generate a safe filename from title
                safe_title = "".join(
                    c if c.isalnum() or c in "-_" else "_" 
                    for c in title[:50]
                ).strip("_")
                filename = f"generated_{safe_title}_{int(time.time())}.{ext}"
                
                # Create ContentFile
                content_file = ContentFile(img_response.content, name=filename)
                
                logger.info("Successfully generated image: %s", filename)
                return (filename, content_file)
                
            elif response.status_code == 429:
                # Rate limited
                logger.warning("fal-ai rate limited, backing off...")
                time.sleep(backoff * (2 ** attempt))
                continue
            else:
                logger.warning(
                    "fal-ai API error %d: %s",
                    response.status_code,
                    response.text[:500]
                )
                last_error = Exception(f"API error {response.status_code}")
                
        except requests.Timeout:
            logger.warning("fal-ai request timeout (attempt %d)", attempt + 1)
            last_error = Exception("Request timeout")
        except requests.RequestException as e:
            logger.warning("fal-ai request error: %s", e)
            last_error = e
        except Exception as e:
            logger.exception("Unexpected error in image generation: %s", e)
            last_error = e
        
        # Backoff before retry
        if attempt < max_attempts - 1:
            time.sleep(backoff * (2 ** attempt))

    logger.error(
        "Image generation failed after %d attempts: %s",
        max_attempts, last_error
    )
    return None


def should_generate_image() -> bool:
    """Check if image generation is enabled and configured."""
    cfg = get_active_image_generator_config()
    return cfg is not None


def test_image_generation() -> dict:
    """Test image generation with a sample prompt.
    
    Returns a dict with status, message, and optionally image_url on success.
    """
    cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
    
    if not cfg:
        return {"status": "error", "message": "No ImageGeneratorConfig found. Please create one first."}
    
    if not cfg.api_key:
        return {"status": "error", "message": "API key is not configured."}
    
    if not cfg.is_enabled:
        return {"status": "warning", "message": "Image generation is disabled. Enable it to use in production."}
    
    # Test with a sample article
    test_title = "AI Revolution: New Breakthrough in Machine Learning"
    test_content = "Scientists have developed a new algorithm that significantly improves neural network efficiency."
    
    try:
        result = generate_image_for_article(test_title, test_content)
        
        if result:
            filename, content_file = result
            # Don't actually save the test image, just report success
            return {
                "status": "success",
                "message": f"Image generation working! Generated test image: {filename} ({len(content_file.read())} bytes)",
            }
        else:
            return {
                "status": "error", 
                "message": "Image generation returned no result. Check logs for details."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Image generation failed: {str(e)}"
        }

