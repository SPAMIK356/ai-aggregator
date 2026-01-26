"""AI image generation using OpenAI for prompt generation + fal-ai for image creation.

Two-step process:
1. OpenAI generates an optimized image prompt based on article content
2. fal-ai generates the actual image using that prompt
"""
from __future__ import annotations

import json
import logging
import time
import requests
from typing import Optional, Tuple

from django.conf import settings
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

DEFAULT_PROMPT_INSTRUCTIONS = """You are an expert at creating prompts for AI image generation.
Given a news article title and content, generate a detailed, descriptive prompt for creating 
a professional illustration that captures the essence of the article.

Requirements:
- The prompt should be 1-3 sentences, detailed and specific
- Focus on visual elements, style, mood, and composition
- Use professional, modern aesthetic suitable for a tech news website
- Avoid text, logos, watermarks, or specific brand references
- The image should be abstract/conceptual rather than literal news photos

Return ONLY the image generation prompt, nothing else."""


def get_active_image_generator_config() -> Optional[ImageGeneratorConfig]:
    """Get the active image generator config if enabled and properly configured."""
    cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
    if not cfg or not cfg.is_enabled:
        return None
    if not cfg.fal_api_key:
        return None
    # OpenAI API key comes from settings
    if not getattr(settings, "OPENAI_API_KEY", None):
        return None
    return cfg


def generate_image_prompt(title: str, content: str, cfg: ImageGeneratorConfig) -> Optional[str]:
    """Use OpenAI to generate an optimized image prompt based on article content.
    
    Args:
        title: Article title
        content: Article content/description
        cfg: ImageGeneratorConfig with OpenAI settings
        
    Returns:
        Generated image prompt string, or None on failure
    """
    from openai import OpenAI, BadRequestError, APITimeoutError, RateLimitError
    
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        logger.warning("OpenAI API key not configured")
        return None
    
    base_url = getattr(settings, "OPENAI_BASE_URL", None)
    
    system_prompt = cfg.prompt_generator_instructions or DEFAULT_PROMPT_INSTRUCTIONS
    
    user_content = f"""Article Title: {title[:300]}

Article Content: {content[:1500] if content else 'No additional content'}

Generate an image prompt for this article:"""

    max_attempts = 3
    backoff = 2.0
    last_error: Optional[Exception] = None
    
    for attempt in range(max_attempts):
        try:
            timeout = 30.0 * (attempt + 1)
            client = OpenAI(api_key=api_key, timeout=timeout, max_retries=0, base_url=base_url)
            
            # Newer models (gpt-4o, o1, etc.) require max_completion_tokens instead of max_tokens
            model_lower = cfg.openai_model.lower()
            use_new_param = any(m in model_lower for m in ["gpt-4o", "o1-", "o3-"])
            
            completion_kwargs = {
                "model": cfg.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            }
            
            # Add token limit with appropriate parameter name
            if use_new_param:
                completion_kwargs["max_completion_tokens"] = 200
            else:
                completion_kwargs["max_tokens"] = 200
                completion_kwargs["temperature"] = 0.7
            
            response = client.chat.completions.create(**completion_kwargs)
            
            prompt = (response.choices[0].message.content or "").strip()
            if prompt:
                logger.info("Generated image prompt: %s", prompt[:100])
                return prompt
                
        except BadRequestError as e:
            logger.warning("OpenAI BadRequest for prompt generation: %s", e)
            last_error = e
        except (APITimeoutError, RateLimitError) as e:
            logger.warning("OpenAI transient error (attempt %d): %s", attempt + 1, e)
            last_error = e
        except Exception as e:
            logger.exception("OpenAI unexpected error: %s", e)
            last_error = e
        
        if attempt < max_attempts - 1:
            time.sleep(backoff * (2 ** attempt))
    
    logger.error("Prompt generation failed after %d attempts: %s", max_attempts, last_error)
    return None


def generate_image_with_fal(prompt: str, cfg: ImageGeneratorConfig) -> Optional[Tuple[str, ContentFile]]:
    """Generate image using fal-ai with the given prompt.
    
    Args:
        prompt: The image generation prompt (from OpenAI)
        cfg: ImageGeneratorConfig with fal-ai settings
        
    Returns:
        Tuple of (filename, ContentFile) if successful, None otherwise
    """
    # Get dimensions for aspect ratio
    dimensions = ASPECT_RATIO_DIMENSIONS.get(
        cfg.aspect_ratio, 
        ASPECT_RATIO_DIMENSIONS["landscape_16_9"]
    )

    # fal-ai API endpoint
    api_url = f"https://fal.run/{cfg.fal_model}"
    
    headers = {
        "Authorization": f"Key {cfg.fal_api_key}",
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

    max_attempts = 3
    backoff = 2.0
    last_error: Optional[Exception] = None

    for attempt in range(max_attempts):
        try:
            logger.info("Generating image with fal-ai (attempt %d/%d)", attempt + 1, max_attempts)
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120,
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
                    logger.warning("Failed to download generated image: %d", img_response.status_code)
                    continue
                
                # Determine filename
                content_type = img_response.headers.get("content-type", "image/png")
                ext = "png" if "png" in content_type else "jpg"
                filename = f"generated_{int(time.time())}.{ext}"
                
                # Create ContentFile
                content_file = ContentFile(img_response.content, name=filename)
                
                logger.info("Successfully generated image: %s (%d bytes)", filename, len(img_response.content))
                return (filename, content_file)
                
            elif response.status_code == 429:
                logger.warning("fal-ai rate limited, backing off...")
                time.sleep(backoff * (2 ** attempt))
                continue
            else:
                logger.warning("fal-ai API error %d: %s", response.status_code, response.text[:500])
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
        
        if attempt < max_attempts - 1:
            time.sleep(backoff * (2 ** attempt))

    logger.error("Image generation failed after %d attempts: %s", max_attempts, last_error)
    return None


def generate_image_for_article(
    title: str,
    content: str,
) -> Optional[Tuple[str, ContentFile]]:
    """Generate an image for the given article using OpenAI + fal-ai.

    Two-step process:
    1. OpenAI generates an optimized image prompt
    2. fal-ai generates the actual image
    
    Args:
        title: Article title
        content: Article content/description

    Returns:
        Tuple of (filename, ContentFile) if successful, None otherwise.
    """
    cfg = get_active_image_generator_config()
    if not cfg:
        return None

    # Step 1: Generate prompt with OpenAI
    logger.info("Generating image prompt for: %s", title[:50])
    prompt = generate_image_prompt(title, content, cfg)
    
    if not prompt:
        logger.warning("Failed to generate image prompt, skipping image generation")
        return None
    
    # Step 2: Generate image with fal-ai
    return generate_image_with_fal(prompt, cfg)


def should_generate_image() -> bool:
    """Check if image generation is enabled and configured."""
    cfg = get_active_image_generator_config()
    return cfg is not None


def test_image_generation() -> dict:
    """Test image generation with a sample prompt.
    
    Returns a dict with status, message, and details about each step.
    """
    import traceback
    
    cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
    
    if not cfg:
        return {"status": "error", "message": "No ImageGeneratorConfig found. Please create one first."}
    
    if not cfg.fal_api_key:
        return {"status": "error", "message": "fal-ai API key is not configured."}
    
    openai_key = getattr(settings, "OPENAI_API_KEY", None)
    if not openai_key:
        return {"status": "error", "message": "OpenAI API key not configured in environment (OPENAI_API_KEY)."}
    
    status_note = ""
    if not cfg.is_enabled:
        status_note = "⚠️ Note: Image generation is disabled. Testing anyway...\n\n"
    
    # Test with a sample article
    test_title = "AI Revolution: New Breakthrough in Machine Learning"
    test_content = "Scientists have developed a new algorithm that significantly improves neural network efficiency, potentially transforming how we approach complex computational problems."
    
    # Step 1: Test prompt generation with OpenAI
    try:
        prompt = generate_image_prompt(test_title, test_content, cfg)
    except Exception as e:
        return {
            "status": "error",
            "message": f"{status_note}❌ Step 1 FAILED: OpenAI prompt generation\n\nModel: {cfg.openai_model}\nError: {type(e).__name__}: {str(e)}\n\nTraceback:\n{traceback.format_exc()[-500:]}"
        }
    
    if not prompt:
        return {
            "status": "error",
            "message": f"{status_note}❌ Step 1 FAILED: OpenAI returned empty prompt\n\nModel: {cfg.openai_model}\nCheck your OpenAI API key and model settings.\n\nTip: Check backend logs for more details."
        }
    
    step1_success = f"✅ Step 1 OK: OpenAI prompt generation\nModel: {cfg.openai_model}\nGenerated prompt: \"{prompt[:200]}{'...' if len(prompt) > 200 else ''}\"\n\n"
    
    # Step 2: Test image generation with fal-ai
    try:
        result = generate_image_with_fal(prompt, cfg)
    except Exception as e:
        return {
            "status": "error",
            "message": f"{status_note}{step1_success}❌ Step 2 FAILED: fal-ai image generation\n\nModel: {cfg.fal_model}\nError: {type(e).__name__}: {str(e)}\n\nTraceback:\n{traceback.format_exc()[-500:]}"
        }
    
    if result:
        filename, content_file = result
        size = len(content_file.read())
        return {
            "status": "success",
            "message": f"{status_note}{step1_success}✅ Step 2 OK: fal-ai image generation\nModel: {cfg.fal_model}\nImage: {filename} ({size:,} bytes)\n\n🎉 Image generation is working!",
        }
    else:
        return {
            "status": "error", 
            "message": f"{status_note}{step1_success}❌ Step 2 FAILED: fal-ai returned no image\n\nModel: {cfg.fal_model}\nCheck your fal-ai API key and model name.\n\nTip: Check backend logs for detailed error."
        }
