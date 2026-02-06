from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents.context_cache_config import ContextCacheConfig
'Google Maps Places API search tool for competitor mapping.'
import os
import googlemaps
from google.adk.tools import ToolContext

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def search_places(query: str, tool_context: ToolContext) -> dict:
    """Search for places using Google Maps Places API.

    This tool searches for businesses/places matching the query using the
    Google Maps Places API. It returns real competitor data including names,
    addresses, ratings, and other relevant information.

    Args:
        query: Search query combining business type and location.
               Example: "fitness studio near KR Puram, Bangalore, India"

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - results: List of places found with details
            - count: Number of results found
            - error_message: Error details if status is "error"
    """
    try:
        maps_api_key = tool_context.state.get('maps_api_key', '') or os.environ.get('MAPS_API_KEY', '')
        if not maps_api_key:
            return {'status': 'error', 'error_message': "Maps API key not found. Set MAPS_API_KEY environment variable or 'maps_api_key' in session state.", 'results': [], 'count': 0}
        gmaps = googlemaps.Client(key=maps_api_key)
        result = gmaps.places(query)
        places = []
        for place in result.get('results', []):
            places.append({'name': place.get('name', 'Unknown'), 'address': place.get('formatted_address', place.get('vicinity', 'N/A')), 'rating': place.get('rating', 0), 'user_ratings_total': place.get('user_ratings_total', 0), 'price_level': place.get('price_level', 'N/A'), 'types': place.get('types', []), 'business_status': place.get('business_status', 'UNKNOWN'), 'location': {'lat': place.get('geometry', {}).get('location', {}).get('lat'), 'lng': place.get('geometry', {}).get('location', {}).get('lng')}, 'place_id': place.get('place_id', '')})
        return {'status': 'success', 'results': places, 'count': len(places), 'next_page_token': result.get('next_page_token')}
    except Exception as e:
        return {'status': 'error', 'error_message': str(e), 'results': [], 'count': 0}