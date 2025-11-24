import os
import json
import urllib.request
import urllib.error
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Use environment variable for the API key
PERSPECTIVE_API_KEY = os.environ.get("GOOGLE_API_KEY")
API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

class PerspectiveError(Exception):
    """Custom exception for Perspective API errors."""
    pass

class SafetyViolationError(Exception):
    """Raised when content violates safety policies."""
    pass

def check_toxicity(text: str, threshold: float = 0.7) -> dict:
    """
    Check text for toxicity using Google's Perspective API.
    
    Args:
        text: The text to analyze.
        threshold: The toxicity score threshold (0.0 to 1.0).
        
    Returns:
        dict: {"safe": bool, "score": float, "reason": str}
        
    Raises:
        PerspectiveError: If the API call fails.
    """
    logger.info(f"🔍 Perspective API Check - text_length={len(text)} chars, threshold={threshold}")
    
    if not PERSPECTIVE_API_KEY:
        # If no key is configured, we log a warning but default to safe
        # so we don't block the application in dev environments without keys.
        # In production, this should probably enforce a key.
        logger.warning("⚠️  Perspective API Key not set. Skipping safety check.")
        print("WARNING: PERSPECTIVE_API_KEY not set. Skipping safety check.")
        return {"safe": True, "score": 0.0, "reason": "No API key configured"}

    url = f"{API_URL}?key={PERSPECTIVE_API_KEY}"
    
    data = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        logger.debug(f"📤 Sending request to Perspective API: {API_URL}")
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Extract score
        # Structure: attributeScores -> TOXICITY -> summaryScore -> value
        score = result.get('attributeScores', {}).get('TOXICITY', {}).get('summaryScore', {}).get('value', 0.0)
        
        logger.info(f"📥 Perspective API Response - score={score:.3f}, threshold={threshold}")
        
        if score > threshold:
            logger.warning(f"⚠️  Content REJECTED - Toxicity score ({score:.3f}) exceeds threshold ({threshold})")
            return {
                "safe": False, 
                "score": score, 
                "reason": f"Toxicity score ({score:.2f}) exceeds threshold ({threshold})"
            }
        
        logger.info(f"✅ Content SAFE - score={score:.3f} below threshold={threshold}")
        return {"safe": True, "score": score, "reason": "Safe"}
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        logger.error(f"❌ Perspective API HTTP Error: {e.code} - {error_body}")
        print(f"Perspective API Error: {e.code} - {error_body}")
        raise PerspectiveError(f"Perspective API request failed: {e.code} - {error_body}")
    except Exception as e:
        logger.error(f"❌ Perspective API Exception: {type(e).__name__}: {e}")
        print(f"Error checking perspective: {e}")
        raise PerspectiveError(f"Error checking perspective: {e}")

