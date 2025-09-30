"""STARLOG MCP server wrapper using FastMCP."""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Set up logging for debugging
logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("FastMCP not available - install mcp package")
    raise

from .starlog import Starlog
from .models import RulesEntry, DebugDiaryEntry, StarlogEntry, FlightConfig, StarlogPayloadDiscoveryConfig
from heaven_base.tools.registry_tool import registry_util_func

# Create singleton instance
logger.info("Initializing STARLOG instance")
starlog = Starlog()

# Create FastMCP app
app = FastMCP("STARLOG")
logger.info("STARLOG initialized")

@app.tool()
def init_project(path: str, name: str, description: str = "", giint_project_id: str = None) -> str:
    """Creates project structure with registries and HPI template. Use this when check() shows directory is not a STARLOG project.
    
    Args:
        path: Directory path for the STARLOG project
        name: Project name
        description: Project description
        giint_project_id: Optional GIINT project ID to link this STARLOG project to GIINT intelligence data
    """
    logger.debug(f"init_project called with path={path}, name={name}, description={description}, giint_project_id={giint_project_id}")
    return starlog.init_project(path, name, description, giint_project_id)

@app.tool()
def check(path: str) -> Dict[str, Any]:
    """Verifies if directory is a STARLOG project. Always use this first to determine if you need to init_project or can proceed with orient."""
    logger.debug(f"check called with path={path}")
    return starlog.check(path)

@app.tool()
def orient(path: str) -> str:
    """Returns full Captain's Log XML context for existing projects. Use this after check() confirms project exists to get complete project history and context."""
    logger.debug(f"orient called with path={path}")
    return starlog.orient(path)

@app.tool()
def rules(path: str) -> str:
    """View project guidelines and standards. Use this to check what coding standards and project rules have been established."""
    logger.debug(f"rules called with path={path}")
    return starlog.rules(path)

@app.tool()
def update_rules(rules_data: list[RulesEntry], path: str) -> str:
    """Replace all project rules with RulesEntry models."""
    logger.debug(f"update_rules called with path={path}, count={len(rules_data)}")
    project_name = starlog._get_project_name_from_path(path)
    
    # Clear existing rules and add new ones
    for rule in rules_data:
        starlog._save_rules_entry(project_name, rule)
    
    return f"✅ Updated {len(rules_data)} rules for {project_name}"

@app.tool()
def add_rule(rule: str, path: str, category: str = "general") -> str:
    """Create new project guideline or standard. Use this to establish coding standards, project conventions, or other guidelines during development."""
    logger.debug(f"add_rule called with path={path}, category={category}")
    return starlog.add_rule(rule, path, category)

@app.tool()
def delete_rule(rule_id: str, path: str) -> str:
    """Remove specific rule."""
    logger.debug(f"delete_rule called with path={path}, rule_id={rule_id}")
    return starlog.delete_rule(rule_id, path)

def _has_active_session(project_name: str) -> bool:
    """Check if project has an active (non-ended) session."""
    try:
        starlog_data = starlog._get_registry_data(project_name, "starlog")
        if not starlog_data:
            return False
        
        # Check for any session without end_timestamp
        for session_id, session_data in starlog_data.items():
            if session_data.get("end_timestamp") is None:
                return True
        
        return False
    except Exception as e:
        logger.error(f"Failed to check active sessions: {e}", exc_info=True)
        return False

def _log_warpcore_work_phase(project_name: str) -> None:
    """Log WARPCORE phase 2 (work phase) if not already logged for current session."""
    try:
        # Check if work phase already logged for current session
        diary_data = starlog._get_registry_data(project_name, "debug_diary")
        if diary_data:
            # Get current session start time
            starlog_data = starlog._get_registry_data(project_name, "starlog")
            session_start = None
            for session_id, session_data in starlog_data.items():
                if session_data.get("end_timestamp") is None:
                    session_start = session_data.get("timestamp")
                    break
            
            if session_start:
                # Check if WARPCORE work phase already logged since session start
                for entry_id, entry_data in diary_data.items():
                    entry_timestamp = entry_data.get("timestamp", "")
                    entry_content = entry_data.get("content", "")
                    if (entry_timestamp >= session_start and 
                        "[WARPCORE]: Jumping. Warp phase (2/3): 🌌" in entry_content):
                        return  # Already logged
        
        # Log work phase
        from .models import DebugDiaryEntry
        work_entry = DebugDiaryEntry(
            content="[WARPCORE]: Jumping. Warp phase (2/3): 🌌"
        )
        starlog._save_debug_diary_entry(project_name, work_entry)
        
    except Exception as e:
        logger.error(f"Failed to log WARPCORE work phase: {e}", exc_info=True)

def _has_warpcore_work_phase(project_name: str) -> bool:
    """Check if current session has WARPCORE work phase logged."""
    try:
        diary_data = starlog._get_registry_data(project_name, "debug_diary")
        if not diary_data:
            return False
            
        # Get current session start time
        starlog_data = starlog._get_registry_data(project_name, "starlog")
        session_start = None
        for session_id, session_data in starlog_data.items():
            if session_data.get("end_timestamp") is None:
                session_start = session_data.get("timestamp")
                break
        
        if not session_start:
            return False
            
        # Check if WARPCORE work phase logged since session start
        for entry_id, entry_data in diary_data.items():
            entry_timestamp = entry_data.get("timestamp", "")
            entry_content = entry_data.get("content", "")
            if (entry_timestamp >= session_start and 
                "[WARPCORE]: Jumping. Warp phase (2/3): 🌌" in entry_content):
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Failed to check WARPCORE work phase: {e}", exc_info=True)
        return False

@app.tool()
def view_debug_diary(path: str) -> str:
    """Check current project status and recent entries. Use this to review what's been discovered and logged during the current session."""
    logger.debug(f"view_debug_diary called with path={path}")
    return starlog.view_debug_diary(path)

@app.tool()
def update_debug_diary(diary_entry: DebugDiaryEntry, path: str) -> str:
    """Log real-time discoveries, bugs, insights during work. Use this frequently during your work session to track progress and issues."""
    logger.debug(f"update_debug_diary called with path={path}")
    project_name = starlog._get_project_name_from_path(path)
    
    # Check if there's an active session
    if not _has_active_session(project_name):
        return f"❌ Debug diary entries can only be added during active sessions. Use start_starlog() first."
    
    # Log WARPCORE work phase
    _log_warpcore_work_phase(project_name)
    
    result = starlog._save_debug_diary_entry(project_name, diary_entry)
    return f"✅ Updated debug diary: {diary_entry.content[:50]}{'...' if len(diary_entry.content) > 50 else ''}"

@app.tool()
def view_starlog(path: str) -> str:
    """Get registry paths where starlog data is stored. Returns the actual file paths to access the raw session data."""
    logger.debug(f"view_starlog called with path={path}")
    return starlog.view_starlog(path)

def _update_recent_projects(project_path: str) -> None:
    """Update recent projects list, moving project to front and deduping."""
    try:
        from heaven_base.tools.registry_tool import registry_util_func
        
        # Get current recent projects
        recent_data = {}
        try:
            recent_result = registry_util_func("get_all", registry_name="starlog_recent_projects")
            if "Items in registry" in recent_result:
                # Extract the dictionary part from the result string
                start_idx = recent_result.find("{") 
                if start_idx != -1:
                    dict_str = recent_result[start_idx:]
                    # Handle Python literals (None, True, False) in the registry data
                    dict_str = dict_str.replace("None", "null").replace("True", "true").replace("False", "false")
                    recent_data = json.loads(dict_str.replace("'", '"'))
        except Exception:
            # Registry doesn't exist yet, start fresh
            pass
        
        # Remove project if it already exists (for deduplication)
        keys_to_remove = []
        for key, value in recent_data.items():
            if value.get("project") == project_path:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            registry_util_func("delete", registry_name="starlog_recent_projects", key=key)
        
        # Add project to front with current timestamp as key
        from datetime import datetime
        timestamp_key = datetime.now().isoformat()
        registry_util_func("add", 
                          registry_name="starlog_recent_projects", 
                          key=timestamp_key,
                          value_dict={"project": project_path})
        
        # Prune to keep only 100 most recent
        updated_result = registry_util_func("get_all", registry_name="starlog_recent_projects")
        if "Items in registry" in updated_result:
            start_idx = updated_result.find("{") 
            if start_idx != -1:
                dict_str = updated_result[start_idx:]
                dict_str = dict_str.replace("None", "null").replace("True", "true").replace("False", "false")
                updated_data = json.loads(dict_str.replace("'", '"'))
            if len(updated_data) > 100:
                # Sort by timestamp (key) and keep only newest 100
                sorted_keys = sorted(updated_data.keys(), reverse=True)
                keys_to_prune = sorted_keys[100:]
                for key in keys_to_prune:
                    registry_util_func("delete", registry_name="starlog_recent_projects", key=key)
        
        logger.debug(f"Updated recent projects with {project_path}")
        
    except Exception as e:
        logger.error(f"Failed to update recent projects: {e}", exc_info=True)

@app.tool()
def start_starlog(session_title: str, start_content: str, session_goals: List[str], path: str, relevant_docs: List[str] = None) -> str:
    """Begin tracked development session with goals and context. Use this to start a new work session after orient() provides project context."""
    logger.debug(f"start_starlog called with path={path}, title={session_title}")
    
    # Update recent projects list
    _update_recent_projects(path)
    
    # Call the actual starlog method that includes debug diary creation
    context_from_docs = ', '.join(relevant_docs or [])
    return starlog.start_starlog(session_title, start_content, context_from_docs, session_goals, path)

@app.tool()
def end_starlog(end_content: str, path: str, 
                key_discoveries: List[str] = None, files_updated: List[str] = None, 
                challenges_faced: List[str] = None) -> str:
    """Complete session with summary and outcomes. Use this to properly close your work session with a summary of what was accomplished."""
    logger.debug(f"end_starlog called with path={path}")
    project_name = starlog._get_project_name_from_path(path)
    
    # Check WARPCORE sequence - must have work phase before ending
    if not _has_warpcore_work_phase(project_name):
        return f"❌ WARPCORE sequence violation: No jumping detected. Use fly() or update_debug_diary() first."
    
    # If additional fields provided, update session before ending
    if key_discoveries or files_updated or challenges_faced:
        active_session = starlog._find_active_session(project_name)
        if not active_session:
            return f"❌ No active session found"
        
        # Update session with provided fields
        if key_discoveries:
            active_session.key_discoveries = key_discoveries
        if files_updated:
            active_session.files_updated = files_updated
        if challenges_faced:
            active_session.challenges_faced = challenges_faced
        
        # Save updated session back to registry
        starlog._update_registry_item(project_name, "starlog", active_session.id, active_session.model_dump(mode='json'))
    
    # Delegate to the working StarlogSessionsMixin method
    return starlog.end_starlog(end_content, path)

@app.tool()
def retrieve_starlog(project: str, session_id: str = None, 
                    date_range: str = None, paths: bool = False) -> str:
    """Selective historical retrieval."""
    logger.debug(f"retrieve_starlog called with project={project}, session_id={session_id}, date_range={date_range}, paths={paths}")
    return starlog.retrieve_starlog(project, session_id, date_range, paths)

@app.tool()
def starlog_guide() -> str:
    """Returns STARLOG system workflow and tool usage guide."""
    
    return f"""
<STARLOG_GUIDE>
🌌📖 STARLOG System - Development Session Tracking Flow

check(path) [¹]
    ↓
    Is STARLOG project?
    ├─ NO → init_project(path, name, description) [²]
    └─ YES → orient(path) [³]
    ↓
start_starlog(session_data, path) [⁴]
    ↓
[Work Loop - choose as needed:]
├─ update_debug_diary(entry, path) [⁵]
├─ view_debug_diary(path) [⁶]
├─ view_starlog(path) [⁷]
├─ rules(path) [⁸]
└─ add_rule(rule, path) [⁹]
    ↓
end_starlog(session_id, summary, path) [¹⁰]

[¹] Check: Verifies if directory is a STARLOG project
[²] Init: Creates project structure with registries and HPI template  
[³] Orient: Returns full Captain's Log XML context for existing projects
[⁴] Start: Begin tracked development session with goals and context
[⁵] Update Diary: Log real-time discoveries, bugs, insights during work
[⁶] View Diary: Check current project status and recent entries
[⁷] View Sessions: Review session history and past work
[⁸] Rules: View project guidelines and standards
[⁹] Add Rule: Create new project guideline or standard
[¹⁰] End: Complete session with summary and outcomes

STARLOG creates Captain's Log style XML output for AI context injection.
</STARLOG_GUIDE>
"""

@app.tool()
async def query_project_rules(
    path: str, 
    context: str, 
    persona_id: str = None, 
    persona_str: str = None, 
    mode_id: str = None, 
    mode_str: str = None
) -> str:
    """Query project rules brain for development guidance based on context.
    
    Args:
        path: Project path containing STARLOG rules
        context: Development context/question to query
        persona_id: Predefined persona ID. Available personas:
            - 'logical_philosopher': Rigorous logical analysis with explicit premises
            - 'senior_scientist': Methodical, evidence-driven, cautious with claims
            - 'senior_engineer': Pragmatic implementation guidance with trade-offs
        persona_str: Custom persona description (e.g., 'experienced backend developer')
        mode_id: Predefined mode ID. Available modes:
            - 'summarize': Comprehensive summary relating neuron content to query
            - 'imagine': Creative connections between content and imaginary scenarios
            - 'reify': Actionable steps to make concrete ideas reality
        mode_str: Custom mode description (e.g., 'provide step-by-step instructions')
    """
    logger.debug(f"query_project_rules called with path={path}, context={context}, persona_id={persona_id}, persona_str={persona_str}, mode_id={mode_id}, mode_str={mode_str}")
    
    try:
        from .rules_brain_integration import query_project_rules as async_query
        
        # Pass persona/mode parameters to the async function
        result = await async_query(path, context, persona_id, persona_str, mode_id, mode_str)
        return result
        
    except ImportError:
        return "❌ brain-agent not available - cannot query rules brain"
    except Exception as e:
        logger.error(f"Error in query_project_rules: {e}", exc_info=True)
        return f"❌ Error querying rules brain: {str(e)}"


def _find_flight_config_by_name(flight_data: dict, name: str, path: str) -> Optional[Tuple[str, dict]]:
    """Find flight config by name and path. Returns (config_id, config_data) or None."""
    for config_id, config in flight_data.items():
        if config.get("name") == name and config.get("original_project_path") == path:
            return config_id, config
    return None

def _validate_flight_config_name(name: str) -> Optional[str]:
    """Validate flight config name convention. Returns error message or None."""
    if not name.endswith("_flight_config"):
        return "❌ Flight config names must end with '_flight_config'"
    return None

def _validate_payload_discovery_path(path: Optional[str]) -> Optional[str]:
    """Validate PayloadDiscovery file exists. Returns error message or None."""
    if path and not os.path.exists(path):
        return f"❌ PayloadDiscovery file not found: {path}"
    return None

def _filter_flight_data(flight_data: dict, path: str, this_project_only: bool, category: str = None) -> dict:
    """Filter flight data by project and category."""
    if this_project_only:
        flight_data = {k: v for k, v in flight_data.items() 
                      if v.get("original_project_path") == path}
    
    if category:
        flight_data = {k: v for k, v in flight_data.items() 
                      if v.get("category") == category}
    
    return flight_data


def _create_default_flight(path: str) -> str:
    """Create default flight if none exist."""
    flight_path = os.path.join(path, "starlog_flight.json")
    if not os.path.exists(flight_path):
        flight_pd = StarlogPayloadDiscoveryConfig()
        with open(flight_path, 'w') as f:
            json.dump(flight_pd.model_dump(), f, indent=2)
        logger.info(f"Created default Flight PayloadDiscovery for Waypoint at {flight_path}")
    
    return f"""📋 No custom flight configs found

✅ Created default STARLOG flight configuration at:
   {flight_path}

🚀 To start a STARLOG session, use:
   start_waypoint_journey('{flight_path}', '{path}')

🌐 Global flight configs ARE available! You're seeing all available configs by default.
💡 Set this_project_only=true to view flight configs from a specific STARLOG project only.

💡 To create custom flight configs for your project:
   - Use add_flight_config() to create domain-specific workflows
   - Flight configs extend the base STARLOG session with custom subchains that are Waypoint journeys (`PayloadDiscovery`s)
   - Subchains work best when they are configured as infinitely repeatable processes
   - For example a 'write_documentation' subchain is best formatted as 'detect if there is documentation in this code and add or refine it as necessary' instead of 'detect code that needs documentation and add it'
   - Or a 'write_5_paragraph_essay' subchain is best formatted as 'create or edit a 5 paragraph essay at path' instead of 'write a 5 paragraph essay xyz'
   - Examples: research_flight_config, debugging_flight_config, analysis_flight_config"""


def _show_categories_page(flight_data: dict) -> str:
    """Show main categories page."""
    categories = list(set(v.get("category", "general") for v in flight_data.values()))
    total_configs = len(flight_data)
    
    configs_per_category = {}
    for cat in categories:
        configs_per_category[cat] = len([v for v in flight_data.values() 
                                       if v.get("category") == cat])
    
    result = f"Available Flight Categories ({total_configs} total configs):\\n"
    for cat, count in configs_per_category.items():
        result += f"- {cat} ({count} configs)\\n"
    result += f"\\nUse fly(path, category='name') to browse categories"
    return result


def _show_paginated_configs(flight_data: dict, page: int, category: str, path: str) -> str:
    """Show paginated list of configs."""
    configs_list = list(flight_data.items())
    page_size = 5
    total_pages = (len(configs_list) + page_size - 1) // page_size
    total_configs = len(flight_data)
    
    if page is None:
        page = 1
        
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_configs = configs_list[start_idx:end_idx]
    
    if category:
        result = f"{category.title()} Flight Configs ({total_configs} configs, page {page}/{total_pages}):\\n"
    else:
        result = f"All Flight Configs (page {page}/{total_pages}):\\n"
        
    for i, (config_id, config_data) in enumerate(page_configs, start_idx + 1):
        name = config_data.get("name", "Unnamed")
        desc = config_data.get("description", "No description")
        result += f"{i}. {name} - {desc}\\n"
    
    if total_pages > 1:
        result += f"\\nUse fly('{path}', page={page+1}" 
        if category:
            result += f", category='{category}'"
        result += ") for more"
        
    return result


def internal_add_flight_config(path: str, name: str, config_data: dict, category: str = "general") -> str:
    """Create new flight config with validation."""
    logger.debug(f"add_flight_config called with path={path}, name={name}, category={category}")
    
    try:
        # Validate flight config name convention
        if not name.endswith("_flight_config"):
            return "❌ Flight config names must end with '_flight_config'"
        
        # Validate that user is providing a subchain (required for custom flight configs)
        subchain_path = config_data.get("work_loop_subchain")
        if not subchain_path:
            return "❌ Custom flight configs must specify a work_loop_subchain"
        
        # Validate the PayloadDiscovery file exists
        if not os.path.exists(subchain_path):
            return f"❌ PayloadDiscovery file not found: {subchain_path}"
        
        # Now create FlightConfig instance
        flight_config = FlightConfig(
            name=name,
            original_project_path=path,
            category=category,
            description=config_data.get("description", ""),
            work_loop_subchain=subchain_path
        )
        
        # Save to registry
        result = starlog._save_flight_config(flight_config)
        
        if "added to registry" in result:
            return f"✅ Created flight config '{name}' in category '{category}'"
        else:
            return f"❌ Failed to create flight config: {result}"
            
    except Exception as e:
        logger.error(f"Error creating flight config: {e}", exc_info=True)
        return f"❌ Error creating flight config: {str(e)}"


def internal_delete_flight_config(path: str, name: str) -> str:
    """Remove flight config."""
    logger.debug(f"delete_flight_config called with path={path}, name={name}")
    
    try:
        # Find the flight config by name and path
        flight_data = starlog._get_flight_configs_registry_data()
        flight_id = None
        
        for config_id, config in flight_data.items():
            if config.get("name") == name and config.get("original_project_path") == path:
                flight_id = config_id
                break
        
        if not flight_id:
            return f"❌ Flight config '{name}' not found for project at {path}"
        
        # Delete from registry
        result = registry_util_func("delete", registry_name="starlog_flight_configs", key=flight_id)
        
        if "deleted from registry" in result:
            return f"✅ Deleted flight config '{name}'"
        else:
            return f"❌ Failed to delete flight config: {result}"
            
    except Exception as e:
        logger.error(f"Error deleting flight config: {e}", exc_info=True)
        return f"❌ Error deleting flight config: {str(e)}"


def internal_update_flight_config(path: str, name: str, config_data: dict) -> str:
    """Modify existing flight config."""
    logger.debug(f"update_flight_config called with path={path}, name={name}")
    
    try:
        # Find the flight config
        flight_data = starlog._get_flight_configs_registry_data()
        flight_id = None
        current_config = None
        
        for config_id, config in flight_data.items():
            if config.get("name") == name and config.get("original_project_path") == path:
                flight_id = config_id
                current_config = config
                break
        
        if not flight_id:
            return f"❌ Flight config '{name}' not found for project at {path}"
        
        # Update the config
        updated_config = FlightConfig(**current_config)
        
        if "description" in config_data:
            updated_config.description = config_data["description"]
        if "work_loop_subchain" in config_data:
            updated_config.work_loop_subchain = config_data["work_loop_subchain"]
        if "category" in config_data:
            updated_config.category = config_data["category"]
        
        updated_config.updated_at = datetime.now()
        
        # Validate PayloadDiscovery path if provided
        if updated_config.work_loop_subchain:
            import os
            if not os.path.exists(updated_config.work_loop_subchain):
                return f"❌ PayloadDiscovery file not found: {updated_config.work_loop_subchain}"
        
        # Save updated config
        result = registry_util_func("update", 
                                  registry_name="starlog_flight_configs", 
                                  key=flight_id, 
                                  value_dict=updated_config.model_dump(mode='json'))
        
        if "updated in registry" in result:
            return f"✅ Updated flight config '{name}'"
        else:
            return f"❌ Failed to update flight config: {result}"
            
    except Exception as e:
        logger.error(f"Error updating flight config: {e}", exc_info=True)
        return f"❌ Error updating flight config: {str(e)}"


def internal_read_starlog_flight_config_instruction_manual() -> str:
    """Show flight config schema, examples, and usage guide."""
    
    return """
🧭 STARSHIP Flight Config Instruction Manual

## Overview
Flight configs extend the base STARLOG session workflow with domain-specific subchains.
They provide a way to customize STARLOG sessions for different project types while 
maintaining the immutable base STARLOG structure.

## Schema
```json
{
  "name": "research_methodology_flight_config",
  "category": "research", 
  "description": "Systematic literature review and analysis workflow",
  "work_loop_subchain": "/configs/research_methodology_waypoint.json"
}
```

## Naming Convention
✅ REQUIRED: Flight config names MUST end with '_flight_config'
- research_methodology_flight_config ✅
- debugging_analysis_flight_config ✅ 
- giint_integration_flight_config ✅
- research_waypoint ❌ (this is a regular waypoint)

## Subchain Requirements
- work_loop_subchain: Path to PayloadDiscovery JSON config (required for custom flight configs)
- Subchains should be amplificatory (repeatable processes)
- Example: "detect and improve documentation" vs "write documentation"

## PayloadDiscovery Help
For creating PayloadDiscovery configs, use:
python -c 'import payload_discovery; help(payload_discovery)'

## Usage Examples

### Create Flight Config:
add_flight_config(
    path="/my/project",
    name="research_flight_config",
    config_data={
        "description": "Systematic research methodology",
        "work_loop_subchain": "/configs/research_waypoint.json"
    },
    category="research"
)

### Use Flight Config:
start_waypoint_journey(config_path="/configs/research_waypoint.json", starlog_path="/my/project")

### Management:
- fly(path) - Browse existing configs
- update_flight_config(path, name, new_data)
- delete_flight_config(path, name)

## Architecture
Base STARLOG: check → orient → start → work_loop → end
With Flight Config: check → orient → start → work_loop + subchain → end

The subchain executes as part of work_loop, then returns control to STARLOG for proper session closure.
"""


@app.tool()
def list_most_recent_projects(page: Optional[int] = None) -> str:
    """List most recently used STARLOG projects with pagination."""
    logger.debug(f"list_most_recent_projects called with page={page}")
    
    try:
        from heaven_base.tools.registry_tool import registry_util_func
        
        # Get recent projects registry
        recent_data = {}
        try:
            recent_result = registry_util_func("get_all", registry_name="starlog_recent_projects")
            if "Items in registry" in recent_result:
                start_idx = recent_result.find("{") 
                if start_idx != -1:
                    dict_str = recent_result[start_idx:]
                    dict_str = dict_str.replace("None", "null").replace("True", "true").replace("False", "false")
                    recent_data = json.loads(dict_str.replace("'", '"'))
        except Exception:
            return "📁 No recent projects found. Start a STARLOG session to track projects."
        
        if not recent_data:
            return "📁 No recent projects found. Start a STARLOG session to track projects."
        
        # Sort by timestamp (key) to get most recent first
        sorted_items = sorted(recent_data.items(), key=lambda x: x[0], reverse=True)
        projects = [item[1]["project"] for item in sorted_items]
        
        # Pagination
        page_size = 10
        total_projects = len(projects)
        total_pages = (total_projects + page_size - 1) // page_size
        
        if page is None:
            page = 1
        
        if page < 1 or page > total_pages:
            return f"❌ Page {page} out of range. Available pages: 1-{total_pages}"
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_projects = projects[start_idx:end_idx]
        
        result = f"📁 Most Recent STARLOG Projects (page {page}/{total_pages}, {total_projects} total):\n\n"
        for i, project_path in enumerate(page_projects, start_idx + 1):
            result += f"{i}. {project_path}\n"
        
        if total_pages > 1:
            result += f"\n💡 Use list_most_recent_projects(page={page+1}) for more"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing recent projects: {e}", exc_info=True)
        return f"❌ Error listing recent projects: {str(e)}"

def internal_fly(path: str, page: int = None, category: str = None, this_project_only: bool = False) -> str:
    """Browse and search flight configurations with pagination and categories."""
    logger.debug(f"fly called with path={path}, page={page}, category={category}, this_project_only={this_project_only}")
    
    try:
        project_name = starlog._get_project_name_from_path(path)
        
        # Log WARPCORE work phase only if we have an active session
        if _has_active_session(project_name):
            _log_warpcore_work_phase(project_name)
        
        flight_data = starlog._get_flight_configs_registry_data()
        flight_data = _filter_flight_data(flight_data, path, this_project_only, category)
        
        if category is None:
            # If local flight config doesn't exist, create default
            local_flight_path = os.path.join(path, "starlog_flight.json")
            if not os.path.exists(local_flight_path):
                return _create_default_flight(path)
            
            # Show default string with metadata
            categories = list(set(v.get("category", "general") for v in flight_data.values()))
            num_categories = len(categories)
            
            flight_path = os.path.join(path, "starlog_flight.json")
            return f"""🚀 Default STARLOG Flight Configuration:
   {flight_path}

Default Flight Sequence:
  1. Check STARLOG project
  2. Init or Orient
  3. Start session
  4. Work loop (debug diary, rules, etc.)
  5. End session

🚀 To start a STARLOG session, use:
   start_waypoint_journey('{flight_path}', '{path}')

Available Flight Categories: {num_categories} categories available

Use fly(path, category='name') to browse categories"""
        
        # Category specified - show that category with optional pagination
        return _show_paginated_configs(flight_data, page, category, path)
        
    except Exception as e:
        logger.error(f"Error in fly: {e}", exc_info=True)
        return f"❌ Error browsing flight configs: {str(e)}"


def main():
    """Main entry point for console script."""
    logger.info("Starting STARLOG MCP server")
    app.run()

if __name__ == "__main__":
    main()