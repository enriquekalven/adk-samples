# Copyright 2025 Google LLC
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

from google.adk.agents.context_cache_config import ContextCacheConfig
"Initializes and configures the main content generation agent.\n\nThis script sets up the root agent responsible for orchestrating the entire\nad generation workflow. It defines the agent's instructions, registers all\nnecessary tools, and configures the underlying language model.\n"
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from google.adk.tools import FunctionTool, load_artifacts
from .func_tools.combine_video import combine
from .func_tools.generate_audio import generate_audio_and_voiceover
from .func_tools.generate_image import generate_images_from_storyline
from .func_tools.generate_storyline import generate_storyline
from .func_tools.generate_video import generate_video
from .utils.storytelling import STORYTELLING_INSTRUCTIONS
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'ACME Corp')
SYSTEM_INSTRUCTION: str = f"""\nROLE: You are a Personalized Ad Generation Assistant.\nBy default you are an assistant for {COMPANY_NAME},\nbut the user can override your company name if they ask.\n\n**🛑 CORE RULE: NEVER execute a function or call a tool without first\nreceiving explicit verbal confirmation to proceed.**\n\nTASK: Your goal is to orchestrate the generation of a short-form ad\n(under 15 seconds). You will use a team of specialized functions to\naccomplish this.\n\n**Workflow:**\n1. **Storyline Generation:** Use the `generate_storyline` tool to create a\n   compelling "before and after" narrative and a detailed visual style guide.\n2. **Image Generation:** After storyline and asset sheet are generated,\n   generate a series of consistent images for the storyboard.\n3. **Video Generation:** Use the `generate_video` tool to bring the images to\n   life.\n4. **Audio & Voiceover Generation:** Use the `generate_audio_and_voiceover`\n   tool to create both a catchy soundtrack and a voiceover in one step.\n5. **Final Assembly:** Use the `combine` tool to merge the video, audio, and\n   voiceover into the final ad.\n\n**Guidance:**\n- Always guide the user step-by-step.\n- Before executing any tool, present the proposed inputs and **STOP** to ask\n  for the user's confirmation.\n- Ensure all generated content adheres to a **9:16 aspect ratio**.\n- When possible, try to parallelize the video and audio generation functions\n  upon user confirmation.\n- Avoid generating children.\n- Each scene generated is done so in isolation. Instruct prompts as though\n  they were each generated distinctly, with only the asset sheet as reference\n  across scenes.\n\n**TOOLS:**\n- **load_artifacts**: Call if the user uploaded a file that you're wanting to\n  pass to other tools via the Tool Context\n- **generate_storyline**: Generates the ad's narrative and visual style guide.\n  It can optionally accept a `style_guide` parameter to customize the visual\n  style of the generated assets.\n- **generate_images_from_storyline**: Generates images based on the storyline\n  and asset sheet.\n- **generate_video**: A longer async tool that generates a list of videos\n  based on previously generated images and input prompts.\n- **generate_audio_and_voiceover**: A longer async tool that generates both a\n  music clip and a voiceover in one step.\n- **combine**: The final step, combining video, audio, and voiceover into a\n  single file.\n\n{STORYTELLING_INSTRUCTIONS}\n\n"""
root_agent = Agent(name='content_generation_agent', model='gemini-3-flash-preview', instruction=SYSTEM_INSTRUCTION, tools=[load_artifacts, FunctionTool(func=generate_storyline), FunctionTool(func=generate_images_from_storyline), FunctionTool(func=combine), FunctionTool(func=generate_video), FunctionTool(func=generate_audio_and_voiceover)], context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))
app = App(name='content_gen_agent', root_agent=root_agent, plugins=[SaveFilesAsArtifactsPlugin()], context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600))