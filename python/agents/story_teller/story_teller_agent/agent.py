from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.genai import types
from . import instructions
APP_NAME = 'collaborative_story_writer'
SESSION_ID = 'story_session_v1'
MODEL_NAME = 'gemini-2.0-flash'
USER_ID = 'author_user_01'
N_CHAPTERS = 3
MAX_WORDS = 100
KEY_USER_PROMPT = 'user_prompt'
KEY_ENHANCED_PROMPT = 'enhanced_prompt'
KEY_CURRENT_STORY = 'current_story'
KEY_CREATIVE_CANDIDATE = 'creative_chapter_candidate'
KEY_FOCUSED_CANDIDATE = 'focused_chapter_candidate'
KEY_FINAL_STORY = 'final_story'

def set_initial_story(callback_context, llm_request):
    callback_context.state[KEY_CURRENT_STORY] = 'Chapter 1'
prompt_enhancer = LlmAgent(name='PromptEnhancerAgent', model=MODEL_NAME, instruction=instructions.PROMPT_ENHANCER_INSTRUCTION, description='Expands user prompt into a full story premise.', output_key=KEY_ENHANCED_PROMPT, before_model_callback=set_initial_story)
creative_writer = LlmAgent(name='CreativeStoryTellerAgent', model=MODEL_NAME, generate_content_config=types.GenerateContentConfig(temperature=0.9), instruction=instructions.CREATIVE_WRITER_INSTRUCTION.format(max_words=MAX_WORDS), description='Writes a creative, high-temperature chapter draft.', output_key=KEY_CREATIVE_CANDIDATE)
focused_writer = LlmAgent(name='FocusedStoryTellerAgent', model=MODEL_NAME, generate_content_config=types.GenerateContentConfig(temperature=0.2), instruction=instructions.FOCUSED_WRITER_INSTRUCTION.format(max_words=MAX_WORDS), description='Writes a consistent, low-temperature chapter draft.', output_key=KEY_FOCUSED_CANDIDATE)
critique_agent = LlmAgent(name='CritiqueAgent', model=MODEL_NAME, instruction=instructions.CRITIQUE_AGENT_INSTRUCTION, description='Selects the best chapter and updates the story state.', output_key=KEY_CURRENT_STORY)
editor_agent = LlmAgent(name='EditorAgent', model=MODEL_NAME, instruction=instructions.EDITOR_AGENT_INSTRUCTION, description='Polishes the final draft.', output_key=KEY_FINAL_STORY)
parallel_writers = ParallelAgent(name='ParallelChapterGenerators', sub_agents=[creative_writer, focused_writer], description='Generates two chapter options in parallel.')
chapter_cycle = SequentialAgent(name='ChapterGenerationCycle', sub_agents=[parallel_writers, critique_agent], description='Runs parallel writers then selects the best chapter.')
story_loop = LoopAgent(name='StoryBuildingLoop', sub_agents=[chapter_cycle], max_iterations=N_CHAPTERS, description=f'Iteratively writes {N_CHAPTERS} chapters.')
root_agent = SequentialAgent(name='CollaborativeStoryWorkflow', sub_agents=[prompt_enhancer, story_loop, editor_agent], description='End-to-end story generation pipeline.')