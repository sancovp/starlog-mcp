"""STARLOG MCP server wrapper using FastMCP."""

import logging
import os
import json
from typing import Dict, Any, List

# Set up logging for debugging
logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("FastMCP not available - install mcp package")
    raise

from .starlog import Starlog
from .models import RulesEntry, DebugDiaryEntry, StarlogEntry, FlightConfig, StarlogPayloadDiscoveryConfig

# Create singleton instance
logger.info("Initializing STARLOG instance")
starlog = Starlog()

# Create FastMCP app
app = FastMCP("STARLOG")
logger.info("STARLOG initialized")

@app.tool()
def init_project(path: str, name: str, description: str = "") -> str:
    """Creates project structure with registries and HPI template. Use this when check() shows directory is not a STARLOG project."""
    logger.debug(f"init_project called with path={path}, name={name}, description={description}")
    return starlog.init_project(path, name, description)

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
    result = starlog._save_debug_diary_entry(project_name, diary_entry)
    return f"✅ Updated debug diary: {diary_entry.content[:50]}{'...' if len(diary_entry.content) > 50 else ''}"

@app.tool()
def view_starlog(path: str) -> str:
    """Get registry paths where starlog data is stored. Returns the actual file paths to access the raw session data."""
    logger.debug(f"view_starlog called with path={path}")
    return starlog.view_starlog(path)

@app.tool()
def start_starlog(session_title: str, start_content: str, session_goals: List[str], path: str, relevant_docs: List[str] = None) -> str:
    """Begin tracked development session with goals and context. Use this to start a new work session after orient() provides project context."""
    logger.debug(f"start_starlog called with path={path}, title={session_title}")
    project_name = starlog._get_project_name_from_path(path)
    
    # Create the session object internally
    session_data = StarlogEntry(
        session_title=session_title,
        start_content=start_content, 
        session_goals=session_goals,
        relevant_docs=relevant_docs or []
    )
    
    result = starlog._save_starlog_entry(project_name, session_data)
    return f"🚀 Started session: {session_title} (ID: {session_data.id})"

@app.tool()
def end_starlog(session_id: str, end_content: str, path: str) -> str:
    """Complete session with summary and outcomes. Use this to properly close your work session with a summary of what was accomplished."""
    logger.debug(f"end_starlog called with path={path}, session_id={session_id}")
    return starlog.end_starlog(session_id, end_content, path)

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
    return f"No custom flight configs found. Using default: start_waypoint_journey('{flight_path}', '{path}')"


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


@app.tool()
def fly(path: str, page: int = None, category: str = None, this_project_only: bool = True) -> str:
    """Browse and search flight configurations with pagination and categories."""
    logger.debug(f"fly called with path={path}, page={page}, category={category}, this_project_only={this_project_only}")
    
    try:
        flight_data = starlog._get_flight_configs_registry_data()
        flight_data = _filter_flight_data(flight_data, path, this_project_only, category)
        
        if not flight_data:
            return _create_default_flight(path)
        
        if page is None and category is None:
            return _show_categories_page(flight_data)
        
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