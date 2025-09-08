# STARLOG System Specification

## Overview

STARLOG is a documentation workflow management system that enables structured project documentation through a single MCP. The system provides automatic context injection for development sessions through registry-backed documentation and intelligent prompt assembly using the Heaven framework's PIS (Prompt Injection System).

## Architecture

### Single-MCP System

STARLOG MCP manages three types of project documentation:
1. **RULES** - Project guidelines, constraints, and orientation
2. **DEBUG_DIARY** - Current project status and next steps  
3. **STARLOG** - Session history with START/END markers

## Core Concepts

### Project Definition
- **Project**: Any directory containing a `starlog.hpi` file
- **Arbitrary Nesting**: Projects can be nested infinitely (project within project within project)
- **Project Boundaries**: Defined by the presence of `starlog.hpi` files

### Registry-Based Storage
- Each project stores documentation in three Heaven registries (JSON files)
- Registry naming convention: `{project_name}_{doc_type}_registry.json`
  - `{project_name}_rules_registry.json` - Project guidelines and orientation
  - `{project_name}_debug_diary_registry.json` - Current status tracking
  - `{project_name}_starlog_registry.json` - Session history logs
- Arbitrary schema - each registry stores whatever structure fits the documentation type

## Documentation Models

### Three Core Models
The system uses simple Pydantic models to ensure consistent data structure:

```python
class RulesEntry(BaseModel):
    id: str
    rule: str
    category: str
    created_at: str
    updated_at: str

class DebugDiaryEntry(BaseModel):
    timestamp: str  # Generated automatically, maps to starlog sessions
    status: str
    current_state: str
    next_steps: List[str]
    
class StarlogEntry(BaseModel):
    timestamp: str  # Generated automatically
    date: str
    session_title: str
    start: str
    context_from_docs: str
    session_goals: List[str]
    key_discoveries: List[str] = []
    files_updated: List[str] = []
    testing_results: List[str] = []
    end: Optional[str] = None  # Missing indicates incomplete session
```

### The `.hpi` File Format

`.hpi` files contain JSON that deserializes to a `PromptStepDefinitionVX1` - essentially a recipe for assembling context from multiple sources.

**Default Structure (same for all projects unless customized):**
```json
{
  "name": "starlog_context",
  "blocks": [
    {"type": "freestyle", "content": "## Project Rules\n\n"},
    {"type": "reference", "content": "registry_heaven_variable={'registry_name': '{project_name}_rules'}"},
    {"type": "freestyle", "content": "\n\n## Most Recent Session\n\n"},
    {"type": "reference", "content": "registry_heaven_variable={'registry_name': '{project_name}_starlog', 'key': 'latest_session'}"},
    {"type": "freestyle", "content": "\n\n## Current Status (Debug Diary)\n\n"},
    {"type": "reference", "content": "registry_heaven_variable={'registry_name': '{project_name}_debug_diary', 'key': 'current_status'}"}
  ]
}
```

**Block Types:**
- **FREESTYLE**: Static text with optional template variable substitution
- **REFERENCE**: Dynamic content resolved through HeavenAgentConfig patterns

**Resolution Process:**
1. Load `.hpi` file into `PromptStepDefinitionVX1`
2. Create `PromptInjectionSystemVX1` with this step
3. Call `get_next_prompt()` to render and concatenate all blocks
4. Return assembled prompt string

## STARLOG MCP API

### Complete API (all functions are path-based)

#### Project Management
- `init_project(path: str, name: str)` - Create new project with registries and default `starlog.hpi`
- `check(path: str)` - Check if directory is a STARLOG project
- `orient(path: str)` - Load project's `starlog.hpi` and render complete context

#### RULES Management (Project guidelines/orientation)
- `rules(path: str)` - Get all project rules
- `update_rules(content: str, path: str)` - Replace all project rules
- `add_rule(rule: str, path: str, category?: str)` - Add single rule
- `delete_rule(rule_id: str, path: str)` - Remove specific rule

#### DEBUG_DIARY Management (Current status)
- `view_debug_diary(path: str)` - Get current project status
- `update_debug_diary(content: str, path: str)` - Update current status

#### STARLOG Management (Session history)
- `view_starlog(path: str)` - Get recent session history
- `start_starlog(content: str, path: str)` - Begin new session with context
- `end_starlog(content: str, path: str)` - End current session with summary
- `retrieve_starlog(project: str, session_id?: str, date_range?: str, paths?: bool)` - Selective historical retrieval

### STARLOG Session Format

Sessions follow a structured format with schema-defined fields:

```json
{
  "date": "2025-01-15",
  "session_title": "Initial setup",
  "start": "Session begin marker with context from docs",
  "context_from_docs": "What we learned from reading DIARY, TODOS, etc.",
  "session_goals": ["Goal 1", "Goal 2"],
  "key_discoveries": ["Discovery 1", "Discovery 2"],
  "files_updated": ["file1.py", "file2.md"],
  "testing_results": ["✅ Test 1 passed", "❌ Test 2 failed"],
  "end": "Session completion marker with final status"
}
```

**Missing END marker**: Indicates session ran out of context before completion.

### Historical Data Retrieval

The `retrieve_starlog()` function allows selective access to historical data:

**Parameters:**
- `project: str` - Project name (required)
- `session_id?: str` - Specific session ID to retrieve (optional)
- `date_range?: str` - Date range like "2025-01-01:2025-01-15" (optional)  
- `paths?: bool` - Return file paths to registry data instead of content (optional)

**Constraints:**
- Either `session_id` OR `date_range` must be provided
- Both cannot be None
- `paths=true` returns registry file paths for direct access

**Examples:**
```python
# Get specific session
retrieve_starlog("my_project", session_id="session_123")

# Get sessions from date range  
retrieve_starlog("my_project", date_range="2025-01-01:2025-01-15")

# Get file paths for external processing
retrieve_starlog("my_project", date_range="2025-01-01:2025-01-15", paths=true)
```

## Integration Workflow

### Complete Usage Flow

1. **Initialize Project**:
   ```python
   init_project("/my/project/path", "my_project")  # Creates registries + starlog.hpi
   ```

2. **Setup Project Guidelines**:
   ```python
   add_rule("Always write tests for new features", "/my/project/path", "testing")
   add_rule("Use TypeScript for all new code", "/my/project/path", "coding")
   ```

3. **Start Development Session**:
   ```python
   check("/my/project/path")  # Verify it's a STARLOG project
   rules("/my/project/path")   # Get project guidelines (Claude should call this first)
   start_starlog("Working on feature X with goals: implement API, add tests", "/my/project/path")
   ```

4. **During Development**:
   ```python
   update_debug_diary("Feature X in progress. API implemented, now adding tests.", "/my/project/path")
   ```

5. **Session Context Injection**:
   ```python
   orient("/my/project/path")  # Renders focused project context via PIS
   # Returns: Rules + Most Recent Session + Current Status (mapped by timestamp)
   ```

6. **End Session**:
   ```python
   end_starlog("Completed API and tests. Ready for review. Files: api.py, test_api.py", "/my/project/path")
   ```

### Nested Projects

Projects can be arbitrarily nested:
```
/company/
├── starlog.hpi           # Company-level project
├── backend/
│   ├── starlog.hpi       # Backend team project
│   └── auth-service/
│       └── starlog.hpi   # Microservice project
```

Each level maintains independent documentation while `check()` can navigate the hierarchy.

## Resolution Patterns

### Registry Resolution (within registry data)
Handled by `SimpleRegistryService`:
- `registry_key_ref=<registry>:<key>` → Returns locator string `@<registry>/<key>`
- `registry_object_ref=<registry>:<key>` → Fetches and recursively resolves value
- `registry_all_ref=<registry>` → Fetches entire registry with resolution

### HeavenAgentConfig Resolution (in prompt_suffix_blocks)
Available in REFERENCE blocks:
- `path=/path/to/file` → Read file directly
- `registry_heaven_variable={'registry_name': '...', 'key': '...'}` → Use RegistryHeavenVariable
- `heaven_variable={'path': '/module.py', 'variable_name': 'VAR'}` → Import and extract variable
- `dynamic_call={'path': '/module.py', 'func': 'function'}` → Call function, use return value
- Plain names → Look up in PromptBlockRegistry

## Technical Implementation

### Core Components
STARLOG MCP is built from existing Heaven framework components:

1. **Registry System** - JSON file storage with pointer resolution
2. **PIS (Prompt Injection System)** - Context assembly and rendering 
3. **Pydantic Models** - Data validation for RulesEntry, DebugDiaryEntry, StarlogEntry
4. **CRUD Operations** - Simple JSON file read/write operations

### Data vs Prompts Distinction

**Important**: STARLOG content is **documentation data**, not prompt blocks:

- **STARLOG Data**: Project documentation stored in registries as structured JSON
- **`.hpi` files**: Instructions for assembling context via PIS
- **No prompt creation**: STARLOG never uses `write_prompt_block()` or manages prompt templates

The system creates structured documentation data that gets assembled into context through the injection system.

### Default Behavior
- Every `starlog.hpi` file is identical unless manually customized
- All projects work the same way by default
- Power users can customize their `.hpi` files for advanced workflows
- `orient()` always calls the same PIS pattern: Rules → Latest Session → Current Status
- Timestamps automatically generated for session/diary mapping

## Benefits

1. **Automatic Context**: Never lose track of what you were working on
2. **Structured Documentation**: Consistent format across all projects  
3. **Nested Organization**: Supports complex project hierarchies
4. **Reliable Injection**: Context always available through `orient()`
5. **Path-Based API**: No global state, explicit project targeting
6. **Focused Context**: Rules + Latest Session + Current Status = Relevant context only
7. **Timestamp Mapping**: Debug diary entries automatically linked to sessions by timestamp
8. **Standardization**: Same `.hpi` template works for all projects
9. **Extensibility**: Advanced users can customize context assembly

## Implementation Notes

- Registries are just directories with JSON files - no complex schemas required
- `.hpi` files serve as both project markers and context assembly recipes
- The system leverages existing Heaven infrastructure (registries, PIS, HeavenAgentConfig)
- No accidental project creation - `check()` only retrieves, never creates
- Append-mostly workflow - sessions and status get added/updated, rarely edited
- No TODO management - use GitHub Issues instead

This specification defines a complete documentation workflow system that integrates seamlessly with Claude Code through MCP interfaces, providing automatic project context injection for development sessions.