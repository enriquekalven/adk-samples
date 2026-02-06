from typing import Dict, List, Any
import ast
import os
import logging

logger = logging.getLogger(__name__)

class CodeRemediator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def apply_fixes(self) -> List[str]:
        """Triggers the CodeRemediator to inject caching and compaction patterns."""
        fixes_applied = []
        for root, dirs, files in os.walk(self.root_dir):
            # Exclude venvs, hidden dirs, and other irrelevant folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and 'venv' not in d.lower()]
            for file in files:
                if file.endswith(".py") and "agent" in file:
                    path = os.path.join(root, file)
                    if self._remediate_file(path):
                        fixes_applied.append(path)
        return fixes_applied

    def _remediate_file(self, file_path: str) -> bool:
        modified = False
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 1. Inject ContextCacheConfig into App
            if "App(" in content and "context_cache_config=" not in content:
                import_stmt = "from google.adk.agents.context_cache_config import ContextCacheConfig"
                if import_stmt not in content:
                    content = f"{import_stmt}\n{content}"
                
                content = content.replace("App(", "App(\n    context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=3600),")
                modified = True

            # 2. Inject EventsCompactionConfig
            if "App(" in content and "events_compaction_config=" not in content:
                import_stmt = "from google.adk.apps.events_compaction_config import EventsCompactionConfig"
                if import_stmt not in content:
                    content = f"{import_stmt}\n{content}"
                
                content = content.replace("App(", "App(\n    events_compaction_config=EventsCompactionConfig(compaction_interval=10, overlap_size=2),")
                modified = True

            # 3. Inject @retry decorators (simplified detection)
            if "def call_llm" in content and "@retry" not in content:
                import_stmt = "from tenacity import retry, wait_exponential, stop_after_attempt"
                if import_stmt not in content:
                    content = f"{import_stmt}\n{content}"
                
                content = content.replace("def call_llm", "@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))\ndef call_llm")
                modified = True
                
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True
        except Exception as e:
            logger.error(f"Failed to remediate {file_path}: {e}")
        return False

def apply_fixes(directory_path: str) -> Dict[str, Any]:
    """Triggers the CodeRemediator to inject caching and compaction patterns.
    
    Args:
        directory_path (str): The absolute path to the directory to fix.
    """
    remediator = CodeRemediator(directory_path)
    fixed_files = remediator.apply_fixes()
    return {
        "status": "success",
        "fixed_files": fixed_files,
        "summary": f"Auto-remediation complete. Applied patterns to {len(fixed_files)} files."
    }
