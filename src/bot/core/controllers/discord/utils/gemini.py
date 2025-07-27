from google import genai

from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG

log = logger.get_logger(__name__)

gemini_enabled = True if CONFIG.geminiToken else False

if gemini_enabled:
    try:
        gemini = genai.Client(api_key=CONFIG.geminiToken)
    except Exception as e:
        log.error("Failed to initialize Google GenAI client: %s", e)
        gemini_enabled = False


async def get_gemini_response(query: str):
    if not gemini_enabled:
        return None

    response = await gemini.aio.models.generate_content(
        model="gemini-2.5-flash", contents=query
    )

    return response.text if response else None
