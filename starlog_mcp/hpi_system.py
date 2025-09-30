"""HPI system mixin for context rendering and injection."""

import os
import json
import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import PIS system components
try:
    from heaven_base.tool_utils.prompt_injection_system_vX1 import (
        PromptInjectionSystemVX1,
        PromptInjectionSystemConfigVX1,
        PromptStepDefinitionVX1,
        PromptBlockDefinitionVX1,
        BlockTypeVX1
    )
    from heaven_base.baseheavenagent import HeavenAgentConfig, ProviderEnum
    PIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PIS system not available: {traceback.format_exc()}")
    PIS_AVAILABLE = False


class HpiSystemMixin:
    """Handles HPI integration and context rendering."""
    
    def orient(self, path: str) -> str:
        """Load project's starlog.hpi and render complete context."""
        try:
            hpi_path = os.path.join(path, "starlog.hpi")
            if not os.path.exists(hpi_path):
                return f"❌ No starlog.hpi found at {path}. Use init_project first."
            
            # Get latest session context only (START + DEBUG ENTRIES + END)
            project_name = self._get_project_name_from_path(path)
            context = self._get_latest_session_context(project_name)
            
            # Render HPI file with context
            hpi_content = self._render_hpi_file(hpi_path, context)
            
            return hpi_content
            
        except Exception as e:
            logger.error(f"Failed to orient: {e}")
            return f"❌ Error getting orientation: {str(e)}"
    
    def _get_latest_session_context(self, project_name: str) -> str:
        """Get latest session context: START + DEBUG ENTRIES + END."""
        starlog_data = self._get_registry_data(project_name, "starlog")
        if not starlog_data:
            return "*No sessions found*"
        
        latest_session = self._find_latest_session(starlog_data)
        if not latest_session:
            return "*No sessions found*"
        
        # Extract session details
        session_title = latest_session.get('session_title', 'Untitled')
        start_content = latest_session.get('start_content', 'No start content')
        end_content = latest_session.get('end_content')
        session_timestamp = latest_session.get('timestamp')
        
        # Build context with START + DEBUG ENTRIES + END
        context = f"**{session_title}**\n\n"
        context += f"**START**: {start_content}\n\n"
        
        # Add debug entries from session start until session end (or until now if no end)
        if session_timestamp:
            end_timestamp = latest_session.get('end_timestamp') if end_content else None
            debug_entries = self._get_debug_entries_in_range(project_name, session_timestamp, end_timestamp)
            if debug_entries:
                context += "**DEBUG ENTRIES**:\n"
                for entry in debug_entries:
                    entry_content = entry.get('content', 'No content')
                    entry_time = entry.get('timestamp', '')[:16]  # YYYY-MM-DDTHH:MM
                    context += f"- {entry_time}: {entry_content}\n"
                context += "\n"
        
        # Add session end if it exists
        if end_content:
            context += f"**END**: {end_content}\n"
        
        return context
    
    def _find_latest_session(self, starlog_data: dict) -> dict:
        """Find the most recent session from starlog data."""
        latest_session = None
        latest_timestamp = ""
        
        for session_id, session_data in starlog_data.items():
            timestamp = session_data.get("timestamp", "")
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_session = session_data
        
        return latest_session
    
    def _format_session_context(self, latest_session: dict) -> str:
        """Format latest session for context display."""
        context = "## Last STARLOG Session\n\n"
        context += f"**{latest_session.get('date', '')}** - {latest_session.get('session_title', '')}\n\n"
        context += f"**START**: {latest_session.get('start_content', '')}\n\n"
        
        if latest_session.get('end_content'):
            context += f"**END**: {latest_session.get('end_content', '')}\n\n"
        else:
            context += "**Status**: Session in progress\n\n"
        
        return context
    
    def _format_diary_context(self, diary_data: dict) -> str:
        """Format debug diary entries for context display."""
        context = "## Current Debug Diary\n\n"
        
        # Sort by timestamp and get recent entries
        entries = list(diary_data.items())
        entries.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        
        for entry_id, entry_data in entries[:5]:  # Last 5 entries
            timestamp = entry_data.get("timestamp", "").split("T")[0]
            content = entry_data.get("content", "")
            context += f"**{timestamp}**: {content}\n"
        
        context += "\n"
        return context
    
    def _get_last_session_and_diary(self, project_name: str) -> str:
        """Get the most recent session and current debug diary context."""
        context = "# STARLOG Project Context\n\n"
        
        # Get latest starlog session
        starlog_data = self._get_registry_data(project_name, "starlog")
        if starlog_data:
            latest_session = self._find_latest_session(starlog_data)
            if latest_session:
                context += self._format_session_context(latest_session)
        
        # Get debug diary (recent entries)
        diary_data = self._get_registry_data(project_name, "debug_diary")
        if diary_data:
            context += self._format_diary_context(diary_data)
        
        return context
    
    def _render_hpi_file(self, hpi_path: str, context: str) -> str:
        """Load and render .hpi file using PIS."""
        try:
            hpi_data = self._load_hpi_data(hpi_path)
            project_name = self._get_project_name_from_hpi(hpi_path)
            
            if not PIS_AVAILABLE:
                logger.warning("PIS not available, using fallback rendering")
                return self._fallback_hpi_render(hpi_data, context)
            
            return self._render_with_pis(hpi_data, project_name)
            
        except Exception as e:
            logger.error(f"Failed to render HPI file: {traceback.format_exc()}")
            return f"❌ Error rendering HPI file: {str(e)}"
    
    def _load_hpi_data(self, hpi_path: str) -> dict:
        """Load JSON data from .hpi file."""
        with open(hpi_path, 'r') as f:
            return json.load(f)
    
    def _render_with_pis(self, hpi_data: dict, project_name: str) -> str:
        """Render HPI data using PIS system with template variables for session data."""
        project_description = self._extract_project_description(hpi_data)
        step = self._create_pis_step(hpi_data)
        
        # Create template variables for session content (keeping working approach)
        session_parts = self._get_session_parts(project_name)
        template_vars = {
            "project_name": project_name,
            "project_description": project_description,
            "session_start_content": session_parts["start"],
            "debug_logs_content": session_parts["debug_logs"], 
            "session_end_content": session_parts["end"]
        }
        
        pis_config = self._create_pis_config(step, template_vars)
        pis = PromptInjectionSystemVX1(pis_config)
        
        return pis.get_next_prompt() or "No context generated"
    
    def _extract_project_description(self, hpi_data: dict) -> str:
        """Extract project description from HPI metadata."""
        metadata = hpi_data.get("metadata", {})
        return metadata.get("project_description", "")
    
    def _create_pis_step(self, hpi_data: dict) -> PromptStepDefinitionVX1:
        """Create PIS step from HPI data."""
        step_data = {"name": hpi_data.get("name"), "blocks": hpi_data.get("blocks")}
        return PromptStepDefinitionVX1(**step_data)
    
    def _create_pis_config(self, step: PromptStepDefinitionVX1, template_vars: dict) -> PromptInjectionSystemConfigVX1:
        """Create PIS configuration."""
        agent_config = HeavenAgentConfig(
            name="starlog_context_agent",
            system_prompt="",
            tools=[],
            provider=ProviderEnum.ANTHROPIC
        )
        
        return PromptInjectionSystemConfigVX1(
            steps=[step],
            template_vars=template_vars,
            agent_config=agent_config
        )
    
    def _fallback_hpi_render(self, hpi_data: dict, context: str) -> str:
        """Fallback rendering when PIS is not available."""
        project_name = hpi_data.get('name', 'Unknown')
        
        rendered = f"# {project_name}\n\n"
        rendered += "⚠️  PIS system not available - using fallback rendering\n\n"
        rendered += context
        
        return rendered
    
    
    def _get_session_parts(self, project_name: str) -> dict:
        """Get session parts broken down into start, debug logs, and end."""
        starlog_data = self._get_registry_data(project_name, "starlog")
        if not starlog_data:
            return self._get_empty_session_parts()
        
        latest_session = self._find_latest_session(starlog_data)
        if not latest_session:
            return self._get_empty_session_parts()
        
        return self._format_session_parts(project_name, latest_session)
    
    def _get_empty_session_parts(self) -> dict:
        """Return empty session parts structure."""
        return {
            "start": "*No sessions found*",
            "debug_logs": "*No debug logs*", 
            "end": "*No session end*"
        }
    
    def _format_session_parts(self, project_name: str, session: dict) -> dict:
        """Format session data into structured parts."""
        fields = self._extract_session_fields(session)
        
        start = f"**{fields['session_title']}**\n{fields['start_content']}"
        debug_logs = self._format_session_debug_logs(project_name, fields['session_timestamp'])
        end = fields['end_content']
        
        return {
            "start": start,
            "debug_logs": debug_logs,
            "end": end
        }
    
    def _format_session_debug_logs(self, project_name: str, session_timestamp: str) -> str:
        """Format debug logs for session parts."""
        if not session_timestamp:
            return "*No debug entries*"
        
        debug_entries = self._get_debug_entries_after(project_name, session_timestamp)
        if not debug_entries:
            return "*No debug entries*"
        
        return self._format_debug_entries_list(debug_entries)
    
    def _extract_session_fields(self, session: dict) -> dict:
        """Extract common session fields."""
        return {
            'session_title': session.get('session_title', 'Untitled'),
            'start_content': session.get('start_content', 'No start content'),
            'end_content': session.get('end_content'),
            'session_timestamp': session.get('timestamp')
        }
    
    def _format_debug_entries_list(self, debug_entries: list) -> str:
        """Format list of debug entries into markdown."""
        content = ""
        for entry in debug_entries:
            entry_content = entry.get('content', 'No content')
            entry_time = entry.get('timestamp', '')[:16]  # YYYY-MM-DDTHH:MM
            content += f"- {entry_time}: {entry_content}\n"
        return content
    
    def _assemble_rules_content(self, project_name: str) -> str:
        """Get all rules formatted as markdown."""
        rules_data = self._get_registry_data(project_name, "rules")
        if not rules_data:
            return "*No rules defined*"
        
        content = ""
        for rule_id, rule_data in rules_data.items():
            rule_text = rule_data.get('rule', 'No rule text')
            category = rule_data.get('category', 'general')
            content += f"**{category.title()}**: {rule_text}\n"
        
        return content
    
    def _assemble_latest_session_content(self, project_name: str) -> str:
        """Find latest session and assemble START + DEBUG entries + END."""
        starlog_data = self._get_registry_data(project_name, "starlog")
        if not starlog_data:
            return "*No sessions found*"
        
        latest_session = self._find_latest_session(starlog_data)
        if not latest_session:
            return "*No sessions found*"
        
        return self._format_session_content(project_name, latest_session)
    
    def _format_session_content(self, project_name: str, session: dict) -> str:
        """Format session data into markdown content."""
        session_title = session.get('session_title', 'Untitled')
        start_content = session.get('start_content', 'No start content')
        end_content = session.get('end_content')
        session_timestamp = session.get('timestamp')
        
        content = f"**{session_title}**\n\n"
        content += f"**START**: {start_content}\n\n"
        
        if session_timestamp:
            content += self._format_debug_entries_section(project_name, session_timestamp)
        
        content += self._format_end_section(end_content)
        return content
    
    def _format_debug_entries_section(self, project_name: str, session_timestamp: str) -> str:
        """Format debug entries section for session."""
        debug_entries = self._get_debug_entries_after(project_name, session_timestamp)
        if not debug_entries:
            return ""
        
        content = "**DEBUG ENTRIES**:\n"
        content += self._format_debug_entries_list(debug_entries)
        content += "\n"
        return content
    
    def _format_end_section(self, end_content: str) -> str:
        """Format the end section of session content."""
        if end_content:
            return f"**END**: {end_content}\n"
        else:
            return "*Session in progress*\n"
    
    def _assemble_current_status_content(self, project_name: str) -> str:
        """Get recent debug diary entries."""
        diary_data = self._get_registry_data(project_name, "debug_diary")
        if not diary_data:
            return "*No debug diary entries*"
        
        # Get recent entries (last 3)
        entries = list(diary_data.values())
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent_entries = entries[:3]
        
        content = ""
        for entry in recent_entries:
            entry_content = entry.get('content', 'No content')
            entry_time = entry.get('timestamp', '')[:16]  # YYYY-MM-DDTHH:MM
            content += f"**{entry_time}**: {entry_content}\n"
        
        return content
    
    def _get_debug_entries_in_range(self, project_name: str, start_timestamp: str, end_timestamp: str = None) -> list:
        """Get debug diary entries between start and end timestamps (or until now if no end)."""
        diary_data = self._get_registry_data(project_name, "debug_diary")
        if not diary_data:
            return []
        
        entries = []
        for entry_data in diary_data.values():
            entry_timestamp = entry_data.get('timestamp', '')
            if entry_timestamp and entry_timestamp > start_timestamp:
                # If no end_timestamp, include all entries after start
                # If end_timestamp exists, only include entries before it
                if end_timestamp is None or entry_timestamp <= end_timestamp:
                    entries.append(entry_data)
        
        # Sort by timestamp
        entries.sort(key=lambda x: x.get('timestamp', ''))
        return entries
    
    def _get_debug_entries_after(self, project_name: str, after_timestamp: str) -> list:
        """Get all debug diary entries after the given timestamp."""
        diary_data = self._get_registry_data(project_name, "debug_diary")
        if not diary_data:
            return []
        
        entries = []
        for entry_data in diary_data.values():
            entry_timestamp = entry_data.get('timestamp', '')
            if entry_timestamp and entry_timestamp > after_timestamp:
                entries.append(entry_data)
        
        # Sort by timestamp
        entries.sort(key=lambda x: x.get('timestamp', ''))
        return entries
    
    def _create_default_hpi_content(self, project_name: str, project_description: str = "", giint_project_id: str = None) -> Dict[str, Any]:
        """Create default starlog.hpi content with real values (no templating)."""
        metadata = {
            "project_name": project_name,
            "project_description": project_description
        }
        
        # Add GIINT project mapping if provided
        if giint_project_id:
            metadata["giint_project_id"] = giint_project_id
        
        # Get GIINT data FIRST to get real values
        if giint_project_id:
            giint_data = self._get_giint_project_data(giint_project_id)
            mode_info = self._detect_project_mode(giint_data)
            features_text = self._format_giint_features(giint_data)
            tasks_text = self._format_giint_tasks(giint_data)
        else:
            mode_info = {
                "mode": "standalone", 
                "instructions": "*No GIINT project linked - operating in standalone STARLOG mode*"
            }
            features_text = "*No GIINT project linked*"
            tasks_text = "*No GIINT project linked*"
        
        
        # Build blocks with REAL VALUES (no template variables)
        blocks = [
            {"type": "freestyle", "content": "<STARLOG>"},
            {"type": "freestyle", "content": "<CaptainsLog>"},
            {"type": "freestyle", "content": "<ProjectMetadata>"},
            {"type": "freestyle", "content": f"Project Name: {project_name}"},
            {"type": "freestyle", "content": f"Description: {project_description}"},
            {"type": "freestyle", "content": f"Mode: {mode_info['mode']}"},
            {"type": "freestyle", "content": "</ProjectMetadata>"},
            {"type": "freestyle", "content": "<ModeInstructions>"},
            {"type": "freestyle", "content": mode_info['instructions']},
            {"type": "freestyle", "content": "</ModeInstructions>"}
        ]
        
        # Add GIINT project structure if linked
        if giint_project_id:
            blocks.extend([
                {"type": "freestyle", "content": "<ProjectStructure>"},
                {"type": "freestyle", "content": features_text},
                {"type": "freestyle", "content": "</ProjectStructure>"},
                {"type": "freestyle", "content": "<CurrentTasks>"},
                {"type": "freestyle", "content": tasks_text},
                {"type": "freestyle", "content": "</CurrentTasks>"}
            ])
        
        # Add standard STARLOG session blocks with TEMPLATE VARIABLES (keep working approach)
        blocks.extend([
            {"type": "freestyle", "content": "<Started>{session_start_content}</Started>"},
            {"type": "freestyle", "content": "<DebugDiaries>{debug_logs_content}</DebugDiaries>"},
            {"type": "freestyle", "content": "<Ended>{session_end_content}</Ended>"},
            {"type": "freestyle", "content": "</CaptainsLog>"},
            {"type": "freestyle", "content": "</STARLOG>"}
        ])
        
        return {
            "name": "starlog_context",
            "metadata": metadata,
            "blocks": blocks
        }
    
    def _get_giint_project_data(self, giint_project_id: str) -> dict:
        """Load GIINT project data from projects.json file."""
        try:
            # Get LLM_INTELLIGENCE_DIR from environment, fall back to default
            llm_intelligence_dir = os.getenv('LLM_INTELLIGENCE_DIR', '/tmp/llm_intelligence_responses')
            projects_file = os.path.join(llm_intelligence_dir, 'projects.json')
            
            if not os.path.exists(projects_file):
                logger.warning(f"GIINT projects file not found at {projects_file}")
                return {}
            
            with open(projects_file, 'r') as f:
                projects_data = json.load(f)
            
            project_data = projects_data.get(giint_project_id, {})
            if not project_data:
                logger.warning(f"GIINT project '{giint_project_id}' not found in projects.json")
            
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to load GIINT project data for '{giint_project_id}': {e}")
            return {}
    
    def _format_giint_features(self, giint_data: dict) -> str:
        """Format GIINT project features into XML structure."""
        if not giint_data or 'features' not in giint_data:
            return "*No features defined*"
        
        features = giint_data['features']
        if not features:
            return "*No features defined*"
        
        result = ""
        for feature_name, feature_data in features.items():
            result += f"**{feature_name}**\n"
            
            # Add components
            components = feature_data.get('components', {})
            for component_name, component_data in components.items():
                result += f"  - {component_name}\n"
                
                # Add deliverables
                deliverables = component_data.get('deliverables', {})
                for deliverable_name, deliverable_data in deliverables.items():
                    result += f"    * {deliverable_name}\n"
                    
                    # Add tasks count
                    tasks = deliverable_data.get('tasks', {})
                    if tasks:
                        result += f"      ({len(tasks)} tasks)\n"
            result += "\n"
        
        return result.strip()
    
    def _format_giint_tasks(self, giint_data: dict) -> str:
        """Format current GIINT tasks with status information."""
        if not giint_data or 'features' not in giint_data:
            return "*No tasks defined*"
        
        result = ""
        task_count = 0
        
        features = giint_data['features']
        for feature_name, feature_data in features.items():
            components = feature_data.get('components', {})
            for component_name, component_data in components.items():
                deliverables = component_data.get('deliverables', {})
                for deliverable_name, deliverable_data in deliverables.items():
                    tasks = deliverable_data.get('tasks', {})
                    for task_id, task_data in tasks.items():
                        task_count += 1
                        status = "📋 " if task_data.get('is_ready', False) else "⏳ "
                        result += f"{status}{feature_name}.{component_name}.{deliverable_name}: {task_id}\n"
        
        if task_count == 0:
            return "*No tasks defined*"
        
        return f"Total Tasks: {task_count}\n\n{result.strip()}"
    
    def _detect_project_mode(self, giint_data: dict) -> dict:
        """Detect project mode (planning/execution) based on GIINT task states."""
        if not giint_data or 'features' not in giint_data:
            return {
                "mode": "planning",
                "instructions": "🎯 You are in PLANNING mode. Call giint.get_mode_instructions(planning) for workflow guidance.\n\nCurrent Context: No project structure found. Start by creating features and components."
            }
        
        # Check for ready tasks
        ready_tasks = []
        total_tasks = 0
        
        features = giint_data['features']
        for feature_name, feature_data in features.items():
            components = feature_data.get('components', {})
            for component_name, component_data in components.items():
                deliverables = component_data.get('deliverables', {})
                for deliverable_name, deliverable_data in deliverables.items():
                    tasks = deliverable_data.get('tasks', {})
                    for task_id, task_data in tasks.items():
                        total_tasks += 1
                        if task_data.get('is_ready', False):
                            ready_tasks.append(f"{feature_name}.{component_name}.{deliverable_name}: {task_id}")
        
        if ready_tasks:
            return {
                "mode": "execution",
                "instructions": f"🚀 You are in EXECUTION mode. Call giint.get_mode_instructions(execution) for workflow guidance.\n\nCurrent Context: {len(ready_tasks)} ready task(s) found. Execute the next ready task:\n" + "\n".join(f"- {task}" for task in ready_tasks[:3])
            }
        else:
            return {
                "mode": "planning", 
                "instructions": f"🎯 You are in PLANNING mode. Call giint.get_mode_instructions(planning) for workflow guidance.\n\nCurrent Context: {total_tasks} task(s) exist but none are ready. Time to spec out and prepare tasks for execution."
            }