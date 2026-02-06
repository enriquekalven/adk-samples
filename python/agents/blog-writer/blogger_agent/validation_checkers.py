from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from collections.abc import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

class OutlineValidationChecker(BaseAgent):
    """Checks if the blog outline is valid."""

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        if context.session.state.get('blog_outline'):
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)

class BlogPostValidationChecker(BaseAgent):
    """Checks if the blog post is valid."""

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        if context.session.state.get('blog_post'):
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)