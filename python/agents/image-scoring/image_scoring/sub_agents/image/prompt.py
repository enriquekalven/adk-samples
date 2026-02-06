from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
IMAGEGEN_PROMPT = "\nYour job is to invoke the 'generate_images' tool by passing the `image generation prompt` provided\nto you as a parameter .\n"