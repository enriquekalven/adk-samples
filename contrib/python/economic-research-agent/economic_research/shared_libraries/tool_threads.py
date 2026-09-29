# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run blocking (sync) tools off the event loop.

ADK awaits async tools but calls sync tools directly on the event loop
(``RunConfig.tool_thread_pool_config`` only applies to live mode). Every tool
in this recipe does blocking HTTP, so one slow upstream API would stall every
concurrent session served by the same process. ``run_in_thread`` wraps a sync
tool in an async function that runs it via ``asyncio.to_thread``.

``functools.wraps`` keeps ``__name__``, ``__doc__``, ``__annotations__`` and
``__wrapped__``, which is what ADK uses to build the function declaration, so
the schema the model sees does not change. ``asyncio.to_thread`` copies the
current ``contextvars`` context, so per-session API keys stay visible.
"""

import asyncio
import functools
import inspect
from collections.abc import Callable
from typing import Any


def run_in_thread(func: Callable[..., Any]) -> Callable[..., Any]:
    """Returns an async wrapper that runs sync ``func`` in a worker thread."""
    if inspect.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def run_all_in_threads(
    funcs: list[Callable[..., Any]],
) -> list[Callable[..., Any]]:
    """Applies :func:`run_in_thread` to every function in ``funcs``."""
    return [run_in_thread(f) for f in funcs]
