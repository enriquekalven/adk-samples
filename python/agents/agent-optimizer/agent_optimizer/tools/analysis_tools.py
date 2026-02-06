from tenacity import retry, wait_exponential, stop_after_attempt
import logging
import os
from google.adk.tools import ToolContext
logger = logging.getLogger(__name__)

def read_agent_file(file_path: str) -> str:
    """Reads the content of an agent source file for optimization analysis.

    Args:
        file_path (str): The absolute path to the .py or .md prompt file.

    Returns:
        str: The content of the file.
    """
    try:
        with open(file_path, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f'Error reading file: {e!s}'

def list_agent_directory(directory_path: str) -> list[str]:
    """Lists files in an agent directory to identify components for review.

    Args:
        directory_path (str): The absolute path to the agent directory.

    Returns:
        list[str]: A list of filenames.
    """
    try:
        return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    except Exception as e:
        return [f'Error listing directory: {e!s}']

async def save_optimization_report(report_content: str, filename: str, tool_context: ToolContext) -> str:
    """Saves the final optimization report as an ADK session artifact.

    Args:
        report_content (str): The markdown content of the optimization report.
        filename (str): The name of the file to save (e.g., 'optimization_report.md').
        tool_context (ToolContext): The ADK tool context for saving artifacts.

    Returns:
        str: A success message with the artifact path or an error message.
    """
    from google.genai import types
    try:
        path = await tool_context.save_artifact(filename=filename, artifact=types.Part.from_bytes(data=report_content.encode('utf-8'), mime_type='text/markdown'))
        return f'Report saved to {path}'
    except Exception as e:
        logger.error(f'Failed to save artifact: {e!s}')
        return f'Error saving report: {e!s}'

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def clone_github_repo(repo_url: str, destination_folder: str | None=None) -> str:
    """Clones a public GitHub repository into a local directory for analysis.

    Args:
        repo_url (str): The URL of the GitHub repository (e.g., 'https://github.com/user/repo').
        destination_folder (str | None): Optional. Name of the folder to clone into.
                                        If None, it will be parsed from the URL.

    Returns:
        str: Success message with the destination path or an error message.
    """
    import re
    import shutil
    import subprocess
    try:
        if not destination_folder:
            match = re.search('github\\.com/[\\w-]+/([\\w-]+)', repo_url)
            if match:
                destination_folder = match.group(1)
            else:
                destination_folder = 'cloned_repo'
        cwd = os.getcwd()
        dest_path = os.path.join(cwd, destination_folder)
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, dest_path], capture_output=True, text=True, check=True)
        return f"Repository successfully cloned to {dest_path}.\nYou MUST now use `list_agent_directory('{dest_path}')` and `read_agent_file()` to explore the codebase. Do not assume any standard file names."
    except subprocess.CalledProcessError as e:
        return f'Failed to clone repository: {e.stderr}'
    except Exception as e:
        return f'Error during GitHub cloning: {e!s}'

def get_token_counts(text: str) -> dict:
    """Provides an estimate of token counts and business impact (cost/latency).

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary with token metrics and business impact estimates.
    """
    import re
    char_count = len(text)
    words = re.findall('\\w+', text)
    word_count = len(words)
    token_estimate = int(char_count / 4)
    estimated_cost_usd = token_estimate / 1000000 * 0.075
    return {'token_estimate': token_estimate, 'char_count': char_count, 'word_count': word_count, 'estimated_cost_usd': f'${estimated_cost_usd:.6f}', 'monthly_recurring_cost_est': f'${estimated_cost_usd * 1000:.2f} (per 1k sessions)', 'latency_impact': '⚡ Ultra-Low (<200ms)' if token_estimate < 1000 else '🏃 Balanced (<2s)' if token_estimate < 10000 else '🐢 Significant (>5s)'}

async def generate_mermaid_diagram(markup: str, filename: str, tool_context: ToolContext) -> str:
    """Saves a Mermaid diagram markup as an artifact for visualization in reports.

    Args:
        markup (str): The mermaid.js diagram markup.
        filename (str): The name of the file (e.g., 'workflow.mermaid').
        tool_context (ToolContext): The ADK tool context.

    Returns:
        str: Success message with artifact path.
    """
    from google.genai import types
    try:
        path = await tool_context.save_artifact(filename=filename, artifact=types.Part.from_bytes(data=markup.encode('utf-8'), mime_type='text/vnd.mermaid'))
        return f'Mermaid diagram saved to {path}. This can be used to visualize agent orchestration logic.'
    except Exception as e:
        logger.error(f'Failed to save mermaid artifact: {e!s}')
        return f'Error saving diagram: {e!s}'

def analyze_resource_efficiency(framework: str, code_snippet: str) -> dict:
    """Analyzes a code snippet for memory usage and cost efficiency specific to a framework.

    Args:
        framework (str): The framework being used (e.g., 'CrewAI', 'LangGraph', 'ADK').
        code_snippet (str): The code to analyze.

    Returns:
        dict: A dictionary containing efficiency metrics and optimization tips.
    """
    framework = framework.lower()
    metrics = {'memory_risk': 'Low', 'cost_efficiency': 'High', 'potential_bottlenecks': [], 'optimization_tips': []}
    if 'history' in code_snippet.lower() or 'memory' in code_snippet.lower():
        if 'max_tokens' not in code_snippet.lower() and 'trim' not in code_snippet.lower():
            metrics['memory_risk'] = 'Moderate'
            metrics['optimization_tips'].append('Implement memory trimming or sliding window history.')
    if 'loop' in code_snippet.lower() or 'while' in code_snippet.lower():
        metrics['cost_efficiency'] = 'Moderate'
        metrics['optimization_tips'].append('Ensure loops have strict exit conditions and exponential backoff.')
    if 'crewai' in framework:
        if 'process=Process.sequential' in code_snippet:
            metrics['potential_bottlenecks'].append('Sequential processing may increase latency for independent tasks.')
    elif 'langgraph' in framework:
        if 'checkpoint' not in code_snippet.lower():
            metrics['memory_risk'] = 'High'
            metrics['optimization_tips'].append('Add checkpointers to manage state persistence and memory growth.')
    elif 'openai' in framework or 'agentkit' in framework or 'ag2' in framework or ('autogen' in framework):
        if 'handoff' in code_snippet.lower() or 'initiate_chat' in code_snippet.lower():
            metrics['cost_efficiency'] = 'Moderate'
            metrics['optimization_tips'].append('Optimize agent interaction/handoff loops to prevent redundant history re-injection.')
        if len(code_snippet) > 5000 and 'tools' in code_snippet.lower():
            metrics['potential_bottlenecks'].append('Large tool definitions can bloat prompt overhead.')
    elif 'pydantic' in framework and 'ai' in framework:
        if 'Agent' in code_snippet:
            metrics['optimization_tips'].append("Leverage Pydantic AI's dependency injection for cleaner tool state management.")
    elif 'llamaindex' in framework:
        if 'StorageContext' not in code_snippet:
            metrics['memory_risk'] = 'Moderate'
            metrics['optimization_tips'].append('Ensure Index persistence is managed via StorageContext to avoid memory spikes with large datasets.')
    elif 'adk' in framework:
        if 'ContextCacheConfig' not in code_snippet:
            metrics['cost_efficiency'] = 'Sub-optimal'
            metrics['optimization_tips'].append('Use ContextCacheConfig to reduce costs for recurring prompt headers.')
    return metrics