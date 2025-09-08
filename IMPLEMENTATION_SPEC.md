# STARLOG MCP Implementation Specification

## File Structure

```
/home/GOD/starlog_mcp/
├── starlog_mcp/
│   ├── __init__.py                 # Package init
│   ├── models.py                   # Pydantic models
│   ├── debug_diary.py              # DebugDiaryMixin
│   ├── starlog_sessions.py         # StarlogSessionsMixin
│   ├── rules.py                    # RulesMixin
│   ├── hpi_system.py               # HpiSystemMixin
│   ├── starlog.py                  # Main Starlog singleton class
│   └── starlog_mcp.py              # FastMCP server wrapper
├── setup.py                        # Package setup
├── STARLOG_SPECIFICATION.md        # System spec
├── CARTON_INTEGRATION.md            # Future integration
└── IMPLEMENTATION_SPEC.md           # This file
```

## Core Models (`models.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RulesEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    rule: str
    category: str = "general"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class DebugDiaryEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str
    current_state: str
    next_steps: List[str]

class StarlogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    session_title: str
    start: str
    context_from_docs: str
    session_goals: List[str]
    key_discoveries: List[str] = Field(default_factory=list)
    files_updated: List[str] = Field(default_factory=list)
    testing_results: List[str] = Field(default_factory=list)
    end: Optional[str] = None
```

## Debug Diary Mixin (`debug_diary.py`)

```python
from typing import Dict, Any
from .models import DebugDiaryEntry
import json

class DebugDiaryMixin:
    """Handles debug diary operations for current project status."""
    
    def view_debug_diary(self, path: str) -> str:
        """Get current project status from debug diary."""
        project_name = self._get_project_name_from_path(path)
        registry_data = self._load_registry(project_name, "debug_diary")
        
        current_status = registry_data.get("current_status")
        if not current_status:
            return "No debug diary entries found."
        
        entry = DebugDiaryEntry(**current_status)
        return self._format_debug_diary_entry(entry)
    
    def update_debug_diary(self, content: str, path: str) -> str:
        """Update current project status in debug diary."""
        project_name = self._get_project_name_from_path(path)
        
        # Parse content (could be structured or free-form)
        entry = self._parse_debug_diary_content(content)
        
        registry_data = self._load_registry(project_name, "debug_diary")
        registry_data["current_status"] = entry.dict()
        
        self._save_registry(project_name, "debug_diary", registry_data)
        return f"Debug diary updated for {project_name}"
    
    def _parse_debug_diary_content(self, content: str) -> DebugDiaryEntry:
        """Parse free-form content into structured DebugDiaryEntry."""
        # Implementation: parse content intelligently
        pass
    
    def _format_debug_diary_entry(self, entry: DebugDiaryEntry) -> str:
        """Format debug diary entry for display."""
        # Implementation: format entry as readable text
        pass
```

## Starlog Sessions Mixin (`starlog_sessions.py`)

```python
from typing import List, Optional
from .models import StarlogEntry

class StarlogSessionsMixin:
    """Handles starlog session management and history."""
    
    def view_starlog(self, path: str) -> str:
        """Get recent session history."""
        project_name = self._get_project_name_from_path(path)
        registry_data = self._load_registry(project_name, "starlog")
        
        sessions = registry_data.get("sessions", [])
        recent_sessions = sessions[-5:]  # Last 5 sessions
        
        return self._format_session_history(recent_sessions)
    
    def start_starlog(self, content: str, path: str) -> str:
        """Begin new session with context."""
        project_name = self._get_project_name_from_path(path)
        
        # Parse content into structured session start
        session = self._parse_session_start_content(content)
        
        registry_data = self._load_registry(project_name, "starlog")
        if "sessions" not in registry_data:
            registry_data["sessions"] = []
        
        registry_data["sessions"].append(session.dict())
        registry_data["latest_session"] = session.dict()
        
        self._save_registry(project_name, "starlog", registry_data)
        return f"Started session: {session.session_title}"
    
    def end_starlog(self, content: str, path: str) -> str:
        """End current session with summary."""
        project_name = self._get_project_name_from_path(path)
        registry_data = self._load_registry(project_name, "starlog")
        
        # Update the latest session with END content
        if "latest_session" in registry_data:
            self._update_session_end(registry_data["latest_session"], content)
            
            # Update in sessions array
            sessions = registry_data.get("sessions", [])
            if sessions:
                sessions[-1] = registry_data["latest_session"]
        
        self._save_registry(project_name, "starlog", registry_data)
        return "Session ended successfully"
    
    def retrieve_starlog(self, project: str, session_id: Optional[str] = None, 
                        date_range: Optional[str] = None, paths: bool = False) -> str:
        """Selective historical retrieval."""
        if not session_id and not date_range:
            raise ValueError("Either session_id or date_range must be provided")
        
        if paths:
            # Return file paths to registry data
            return self._get_registry_paths(project)
        
        registry_data = self._load_registry(project, "starlog")
        sessions = registry_data.get("sessions", [])
        
        if session_id:
            filtered = [s for s in sessions if s.get("id") == session_id]
        else:
            filtered = self._filter_sessions_by_date_range(sessions, date_range)
        
        return self._format_session_history(filtered)
```

## Rules Mixin (`rules.py`)

```python
from .models import RulesEntry

class RulesMixin:
    """Handles project rules and guidelines management."""
    
    def rules(self, path: str) -> str:
        """Get all project rules."""
        project_name = self._get_project_name_from_path(path)
        registry_data = self._load_registry(project_name, "rules")
        
        rules = registry_data.get("rules", [])
        return self._format_rules_list(rules)
    
    def update_rules(self, content: str, path: str) -> str:
        """Replace all project rules."""
        project_name = self._get_project_name_from_path(path)
        
        # Parse content into rules list
        rules = self._parse_rules_content(content)
        
        registry_data = {"rules": [rule.dict() for rule in rules]}
        self._save_registry(project_name, "rules", registry_data)
        
        return f"Updated {len(rules)} rules for {project_name}"
    
    def add_rule(self, rule: str, path: str, category: str = "general") -> str:
        """Add single rule."""
        project_name = self._get_project_name_from_path(path)
        
        rule_entry = RulesEntry(rule=rule, category=category)
        
        registry_data = self._load_registry(project_name, "rules")
        if "rules" not in registry_data:
            registry_data["rules"] = []
        
        registry_data["rules"].append(rule_entry.dict())
        self._save_registry(project_name, "rules", registry_data)
        
        return f"Added rule: {rule}"
    
    def delete_rule(self, rule_id: str, path: str) -> str:
        """Remove specific rule."""
        project_name = self._get_project_name_from_path(path)
        registry_data = self._load_registry(project_name, "rules")
        
        rules = registry_data.get("rules", [])
        rules = [r for r in rules if r.get("id") != rule_id]
        
        registry_data["rules"] = rules
        self._save_registry(project_name, "rules", registry_data)
        
        return f"Deleted rule {rule_id}"
```

## HPI System Mixin (`hpi_system.py`)

```python
import os
import json
from heaven_base.tool_utils.prompt_injection_system_vX1 import (
    PromptInjectionSystemVX1,
    PromptInjectionSystemConfigVX1,
    PromptStepDefinitionVX1,
    PromptBlockDefinitionVX1,
    BlockTypeVX1
)
from heaven_base.baseheavenagent import HeavenAgentConfig

class HpiSystemMixin:
    """Handles HPI integration and context rendering."""
    
    def orient(self, path: str) -> str:
        """Load project's starlog.hpi and render complete context."""
        hpi_path = os.path.join(path, "starlog.hpi")
        
        if not os.path.exists(hpi_path):
            return f"No starlog.hpi found at {path} - not a STARLOG project"
        
        return self._render_hpi_file(hpi_path)
    
    def _render_hpi_file(self, hpi_path: str) -> str:
        """Load and render .hpi file using PIS."""
        with open(hpi_path, 'r') as f:
            hpi_data = json.load(f)
        
        # Convert to PromptStepDefinitionVX1
        blocks = []
        for block_data in hpi_data["blocks"]:
            block = PromptBlockDefinitionVX1(
                type=BlockTypeVX1(block_data["type"]),
                content=block_data["content"]
            )
            blocks.append(block)
        
        step = PromptStepDefinitionVX1(
            name=hpi_data["name"],
            blocks=blocks
        )
        
        # Create PIS config
        agent_config = HeavenAgentConfig(
            name="starlog_agent",
            system_prompt="",
            tools=[],
            provider=ProviderEnum.ANTHROPIC
        )
        
        pis_config = PromptInjectionSystemConfigVX1(
            steps=[step],
            template_vars={},
            agent_config=agent_config
        )
        
        # Render using PIS
        pis = PromptInjectionSystemVX1(pis_config)
        rendered_context = pis.get_next_prompt()
        
        return rendered_context or "No context generated"
    
    def _create_default_hpi_content(self, project_name: str) -> dict:
        """Create default starlog.hpi content."""
        return {
            "name": "starlog_context",
            "blocks": [
                {"type": "freestyle", "content": "## Project Rules\n\n"},
                {"type": "reference", "content": f"registry_heaven_variable={{'registry_name': '{project_name}_rules'}}"},
                {"type": "freestyle", "content": "\n\n## Most Recent Session\n\n"},
                {"type": "reference", "content": f"registry_heaven_variable={{'registry_name': '{project_name}_starlog', 'key': 'latest_session'}}"},
                {"type": "freestyle", "content": "\n\n## Current Status (Debug Diary)\n\n"},
                {"type": "reference", "content": f"registry_heaven_variable={{'registry_name': '{project_name}_debug_diary', 'key': 'current_status'}}"}
            ]
        }
```

## Main Starlog Class (`starlog.py`)

```python
import os
import json
from typing import Dict, Any
from pathlib import Path

from .debug_diary import DebugDiaryMixin
from .starlog_sessions import StarlogSessionsMixin
from .rules import RulesMixin
from .hpi_system import HpiSystemMixin

class Starlog(DebugDiaryMixin, StarlogSessionsMixin, RulesMixin, HpiSystemMixin):
    """Main STARLOG singleton class combining all functionality."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Get HEAVEN_DATA_DIR from environment
        self.heaven_data_dir = os.environ.get('HEAVEN_DATA_DIR', '/tmp/heaven_data')
        self.registry_dir = os.path.join(self.heaven_data_dir, 'registry')
        os.makedirs(self.registry_dir, exist_ok=True)
    
    def init_project(self, path: str, name: str) -> str:
        """Create new project with registries and starlog.hpi."""
        # Create empty registries
        for registry_type in ['rules', 'debug_diary', 'starlog']:
            registry_data = {}
            self._save_registry(name, registry_type, registry_data)
        
        # Create default starlog.hpi
        hpi_content = self._create_default_hpi_content(name)
        hpi_path = os.path.join(path, "starlog.hpi")
        
        with open(hpi_path, 'w') as f:
            json.dump(hpi_content, f, indent=2)
        
        return f"Created STARLOG project '{name}' at {path}"
    
    def check(self, path: str) -> Dict[str, Any]:
        """Check if directory is a STARLOG project."""
        hpi_path = os.path.join(path, "starlog.hpi")
        is_project = os.path.exists(hpi_path)
        
        result = {
            "is_project": is_project,
            "path": path
        }
        
        if is_project:
            # Auto-retrieve basic info
            try:
                project_name = self._get_project_name_from_hpi(hpi_path)
                result["project_name"] = project_name
                result["message"] = f"STARLOG project: {project_name}"
            except Exception as e:
                result["message"] = f"STARLOG project found but error reading: {e}"
        else:
            result["message"] = "Not a STARLOG project (no starlog.hpi found)"
        
        return result
    
    # Heaven Registry System Integration (UPDATED)
    # See HEAVEN_REGISTRY_PATTERN.md for full details
    
    def _create_project_registry(self, project_name: str, registry_type: str) -> str:
        """Create registry using Heaven registry system"""
        return registry_util_func("create_registry", registry_name=f"{project_name}_{registry_type}")
    
    def _add_to_registry(self, project_name: str, registry_type: str, key: str, value: Any) -> str:
        """Add item to registry with proper serialization"""
        if isinstance(value, dict):
            return registry_util_func("add", registry_name=f"{project_name}_{registry_type}", 
                                    key=key, value_dict=value)
        else:
            return registry_util_func("add", registry_name=f"{project_name}_{registry_type}", 
                                    key=key, value_str=str(value))
    
    def _get_from_registry(self, project_name: str, registry_type: str, key: str) -> Any:
        """Get specific item from registry"""
        return registry_util_func("get", registry_name=f"{project_name}_{registry_type}", key=key)
    
    def _get_all_from_registry(self, project_name: str, registry_type: str) -> Dict[str, Any]:
        """Get all items from registry"""
        return registry_util_func("get_all", registry_name=f"{project_name}_{registry_type}")
    
    def _get_project_name_from_path(self, path: str) -> str:
        """Extract project name from .hpi file."""
        hpi_path = os.path.join(path, "starlog.hpi")
        return self._get_project_name_from_hpi(hpi_path)
    
    def _get_project_name_from_hpi(self, hpi_path: str) -> str:
        """Extract project name from .hpi file content."""
        with open(hpi_path, 'r') as f:
            hpi_data = json.load(f)
        
        # Extract from first registry reference
        for block in hpi_data.get("blocks", []):
            if block.get("type") == "reference":
                content = block.get("content", "")
                if "registry_name" in content:
                    # Parse registry_name from the reference
                    # registry_heaven_variable={'registry_name': 'project_rules'}
                    import re
                    match = re.search(r"'registry_name':\s*'([^_]+)_", content)
                    if match:
                        return match.group(1)
        
        # Fallback: use directory name
        return Path(hpi_path).parent.name
```

## MCP Server Wrapper (`starlog_mcp.py`)

```python
from mcp import FastMCP
from typing import Dict, Any

from .starlog import Starlog

# Create singleton instance
starlog = Starlog()

# Create FastMCP app
app = FastMCP("STARLOG")

@app.tool()
def init_project(path: str, name: str) -> str:
    """Create new project with registries and starlog.hpi."""
    return starlog.init_project(path, name)

@app.tool()
def check(path: str) -> Dict[str, Any]:
    """Check if directory is a STARLOG project."""
    return starlog.check(path)

@app.tool()
def orient(path: str) -> str:
    """Load project's starlog.hpi and render complete context."""
    return starlog.orient(path)

@app.tool()
def rules(path: str) -> str:
    """Get all project rules."""
    return starlog.rules(path)

@app.tool()
def update_rules(content: str, path: str) -> str:
    """Replace all project rules."""
    return starlog.update_rules(content, path)

@app.tool()
def add_rule(rule: str, path: str, category: str = "general") -> str:
    """Add single rule."""
    return starlog.add_rule(rule, path, category)

@app.tool()
def delete_rule(rule_id: str, path: str) -> str:
    """Remove specific rule."""
    return starlog.delete_rule(rule_id, path)

@app.tool()
def view_debug_diary(path: str) -> str:
    """Get current project status."""
    return starlog.view_debug_diary(path)

@app.tool()
def update_debug_diary(content: str, path: str) -> str:
    """Update current project status."""
    return starlog.update_debug_diary(content, path)

@app.tool()
def view_starlog(path: str) -> str:
    """Get recent session history."""
    return starlog.view_starlog(path)

@app.tool()
def start_starlog(content: str, path: str) -> str:
    """Begin new session with context."""
    return starlog.start_starlog(content, path)

@app.tool()
def end_starlog(content: str, path: str) -> str:
    """End current session with summary."""
    return starlog.end_starlog(content, path)

@app.tool()
def retrieve_starlog(project: str, session_id: str = None, 
                    date_range: str = None, paths: bool = False) -> str:
    """Selective historical retrieval."""
    return starlog.retrieve_starlog(project, session_id, date_range, paths)

if __name__ == "__main__":
    app.run()
```

## Package Setup (`setup.py`)

```python
from setuptools import setup, find_packages

setup(
    name="starlog-mcp",
    version="0.1.0",
    description="STARLOG documentation workflow MCP for Claude Code",
    packages=find_packages(),
    install_requires=[
        "fastmcp",
        "pydantic",
        "heaven-base>=0.1.0",  # Assumes heaven framework is available
    ],
    entry_points={
        "console_scripts": [
            "starlog-server=starlog_mcp.starlog_mcp:main",
        ],
    },
    python_requires=">=3.8",
)
```

## Implementation Complexity

**Total estimated lines:**
- `models.py`: ~50 lines
- `debug_diary.py`: ~80 lines  
- `starlog_sessions.py`: ~150 lines
- `rules.py`: ~100 lines
- `hpi_system.py`: ~120 lines
- `starlog.py`: ~150 lines
- `starlog_mcp.py`: ~80 lines

**Total: ~730 lines**

**Key Implementation Challenges:**
1. **Content Parsing**: Converting free-form text to structured models
2. **PIS Integration**: Properly interfacing with Heaven's PIS system
3. **Date Range Filtering**: Parsing and filtering sessions by date
4. **Error Handling**: Graceful handling of missing files, malformed JSON, etc.

**Simplifications Available:**
- Start with basic text parsing (improve later)
- Use simple date string comparisons (upgrade to proper date parsing later)
- Basic error handling initially

This modular structure makes the codebase maintainable while keeping the MCP interface simple and clean.