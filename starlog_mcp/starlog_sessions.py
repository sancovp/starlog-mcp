"""Starlog sessions mixin for session management and history."""

import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import StarlogEntry, DebugDiaryEntry

logger = logging.getLogger(__name__)


class StarlogSessionsMixin:
    """Handles starlog session management and history."""
    
    def _create_start_debug_entry(self, session: StarlogEntry) -> DebugDiaryEntry:
        """Create debug diary entry for session START with stardate."""
        content_parts = [session.session_title, session.start_content]
        if session.session_goals:
            content_parts.append(f"Goals: {', '.join(session.session_goals)}")
        if session.relevant_docs:
            content_parts.append(f"Docs: {', '.join(session.relevant_docs)}")
        captain_log_content = f"Captain's Log, stardate {session.timestamp}: START SESSION {session.id} -- {' | '.join(content_parts)}"
        return DebugDiaryEntry(content=captain_log_content)
    
    def _create_end_debug_entry(self, session: StarlogEntry) -> DebugDiaryEntry:
        """Create debug diary entry for session END with stardate."""  
        content_parts = [session.session_title]
        if session.end_content:
            content_parts.append(session.end_content)
        if session.key_discoveries:
            content_parts.append(f"Discoveries: {', '.join(session.key_discoveries)}")
        if session.files_updated:
            content_parts.append(f"Files: {', '.join(session.files_updated)}")
        if session.challenges_faced:
            content_parts.append(f"Challenges: {', '.join(session.challenges_faced)}")
        captain_log_content = f"Captain's Log, stardate {session.end_timestamp}: END SESSION {session.id} -- {' | '.join(content_parts)}"
        return DebugDiaryEntry(content=captain_log_content)
    
    def _find_active_session(self, project_name: str) -> Optional[StarlogEntry]:
        """Find active session by walking backwards through registry until hitting START or END."""
        try:
            registry_data = self._get_registry_data(project_name, "starlog")
            if not registry_data:
                return None
            
            # Sort entries by timestamp in descending order (newest first)
            sorted_entries = sorted(
                registry_data.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            )
            
            # Walk backwards until we hit START or END
            for session_id, session_data in sorted_entries:
                session = StarlogEntry(**session_data)
                
                # Check if this is START (has start_content but no end_content)
                if session.start_content and not session.end_content:
                    return session  # Found active session
                
                # Check if this is END (has both start_content and end_content)  
                if session.start_content and session.end_content:
                    return None  # No active session (last session was ended)
            
            return None  # No sessions found
            
        except Exception as e:
            logger.error(f"Failed to find active session: {e}")
            return None
    
    def view_starlog(self, path: str) -> str:
        """Get all registry paths where project data is stored."""
        try:
            import os
            project_name = self._get_project_name_from_path(path)
            heaven_data_dir = os.environ.get("HEAVEN_DATA_DIR", "/tmp/heaven_data")
            
            # Check all registry types for this project
            registry_types = ["starlog", "debug_diary", "rules"]
            paths = []
            
            for registry_type in registry_types:
                registry_name = f"{project_name}_{registry_type}"
                registry_path = os.path.join(heaven_data_dir, "registry", f"{registry_name}_registry.json")
                
                # Check if the registry file exists
                if os.path.exists(registry_path):
                    paths.append(f"Registry: {registry_name}\nPath: {registry_path} ✅")
                else:
                    paths.append(f"Registry: {registry_name}\nPath: {registry_path} ❌ (not found)")
            
            return "\n\n".join(paths)
            
        except Exception as e:
            logger.error(f"Failed to get registry paths: {e}")
            return f"❌ Error getting registry paths: {str(e)}"
    
    def start_starlog(self, session_title: str, start_content: str, context_from_docs: str, 
                     session_goals: List[str], path: str) -> str:
        """Begin new session with context."""
        try:
            project_name = self._get_project_name_from_path(path)
            
            # Convert context_from_docs string to relevant_docs list
            relevant_docs = [context_from_docs] if context_from_docs.strip() else []
            
            session = StarlogEntry(
                session_title=session_title,
                start_content=start_content,
                relevant_docs=relevant_docs,
                session_goals=session_goals
            )
            
            self._save_starlog_entry(project_name, session)
            
            # Create START debug diary entry with stardate
            start_entry = self._create_start_debug_entry(session)
            self._save_debug_diary_entry(project_name, start_entry)
            
            logger.info(f"Started starlog session {session.id} in project {project_name}")
            return f"✅ Started session: {session_title} (ID: {session.id})"
            
        except Exception as e:
            logger.error(f"Failed to start starlog session: {e}")
            return f"❌ Error starting session: {str(e)}"
    
    def end_starlog(self, end_content: str, path: str) -> str:
        """End current session with summary."""
        try:
            project_name = self._get_project_name_from_path(path)
            
            # Find active session by walking backwards through registry
            active_session = self._find_active_session(project_name)
            if not active_session:
                return f"❌ No active session found"
            
            # End the session
            active_session.end_session(end_content)
            
            # Save updated session back to registry
            self._update_registry_item(project_name, "starlog", active_session.id, active_session.model_dump(mode='json'))
            
            # Create END debug diary entry with stardate
            end_entry = self._create_end_debug_entry(active_session)
            self._save_debug_diary_entry(project_name, end_entry)
            
            # Check for task completion and update GitHub issues
            github_updates = self._process_completed_tasks_github_update(active_session, end_content, path)
            github_status = ""
            if github_updates:
                github_status = f" | GitHub: {github_updates}"
            
            logger.info(f"Ended starlog session {active_session.id} in project {project_name}")
            return f"✅ Ended session: {active_session.session_title} (Duration: {active_session.duration_minutes} minutes){github_status}"
            
        except Exception as e:
            logger.error(f"Failed to end starlog session: {e}")
            return f"❌ Error ending session: {str(e)}"
    
    def _process_completed_tasks_github_update(self, session, end_content: str, path: str) -> str:
        """Process completed tasks and update GitHub issues to in-review status."""
        try:
            # Get GIINT project data from starlog.hpi metadata
            project_name = self._get_project_name_from_path(path)
            hpi_data = self._load_session_hpi_data(path)
            giint_project_id = hpi_data.get("metadata", {}).get("giint_project_id")
            
            if not giint_project_id:
                return "No GIINT project linked"
            
            # Check if end_content indicates task completion
            completion_indicators = ["completed", "finished", "done", "task complete", "ready for review"]
            if not any(indicator in end_content.lower() for indicator in completion_indicators):
                return "No task completion detected"
            
            # Call GIINT to update GitHub issues for completed tasks
            import requests
            import os
            
            # Get GIINT MCP endpoint
            llm_intelligence_dir = os.getenv('LLM_INTELLIGENCE_DIR', '/tmp/llm_intelligence_responses')
            
            # Direct call to GIINT's GitHub update function
            return self._update_giint_task_to_review(giint_project_id)
            
        except Exception as e:
            logger.error(f"Failed to process GitHub updates: {e}")
            return f"GitHub update failed: {str(e)}"
    
    def _load_session_hpi_data(self, path: str) -> dict:
        """Load HPI data from starlog.hpi file."""
        import json
        import os
        hpi_path = os.path.join(path, "starlog.hpi")
        if os.path.exists(hpi_path):
            with open(hpi_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _update_giint_task_to_review(self, giint_project_id: str) -> str:
        """Update GIINT tasks to in-review status via direct function call."""
        try:
            # Import GIINT projects module
            import sys
            sys.path.insert(0, '/tmp/llm_intelligence_mcp/llm_intelligence_package')
            from llm_intelligence.projects import ProjectRegistry
            
            # Create GIINT project registry instance
            giint_manager = ProjectRegistry()
            
            # Get project data
            project_data = giint_manager.get_project(giint_project_id)
            if not project_data.get("success"):
                return f"GIINT project {giint_project_id} not found"
            
            project = project_data["project"]
            
            # Find in-progress tasks and update to in-review
            updated_count = 0
            for feature_name, feature in project.get("features", {}).items():
                for component_name, component in feature.get("components", {}).items():
                    for deliverable_name, deliverable in component.get("deliverables", {}).items():
                        for task_id, task in deliverable.get("tasks", {}).items():
                            # If task has GitHub issue and is ready/in-progress, move to in-review
                            if (task.get("github_issue_id") and 
                                (task.get("is_ready") or task.get("is_done"))):
                                
                                # Update task status to in-review
                                giint_manager.update_task_status(
                                    giint_project_id, feature_name, component_name, 
                                    deliverable_name, task_id, 
                                    is_done=False, is_blocked=False, is_ready=False,
                                    blocked_description=None
                                )
                                updated_count += 1
            
            return f"Updated {updated_count} tasks to in-review"
            
        except Exception as e:
            logger.error(f"Failed to update GIINT tasks: {e}")
            return f"GIINT update failed: {str(e)}"
    
    def _format_session_history(self, starlog_data: dict) -> str:
        """Format session history for display."""
        if not starlog_data:
            return "📋 **STARLOG Sessions** (Empty)\n\nNo sessions found."
        
        formatted = "📋 **STARLOG Sessions**\n\n"
        
        # Sort sessions by timestamp (newest first)
        sessions = []
        for session_id, session_data in starlog_data.items():
            sessions.append((session_id, session_data))
        
        sessions.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        
        # Format each session
        for session_id, session_data in sessions:
            date = session_data.get("date", "")
            title = session_data.get("session_title", "")
            is_ended = session_data.get("end_content") is not None
            duration = session_data.get("duration_minutes") if is_ended else None
            
            status = "✅ COMPLETE" if is_ended else "🔄 IN PROGRESS"
            duration_str = f" ({duration}min)" if duration else ""
            
            formatted += f"**{date}** - {title} `{session_id}` {status}{duration_str}\n"
            
            # Show goals briefly
            goals = session_data.get("session_goals", [])
            if goals:
                formatted += f"Goals: {', '.join(goals[:2])}{'...' if len(goals) > 2 else ''}\n"
            
            formatted += "\n"
        
        return formatted.strip()