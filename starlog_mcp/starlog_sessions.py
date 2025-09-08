"""Starlog sessions mixin for session management and history."""

import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import StarlogEntry

logger = logging.getLogger(__name__)


class StarlogSessionsMixin:
    """Handles starlog session management and history."""
    
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
            
            session = StarlogEntry(
                session_title=session_title,
                start_content=start_content,
                context_from_docs=context_from_docs,
                session_goals=session_goals
            )
            
            self._save_starlog_entry(project_name, session)
            
            logger.info(f"Started starlog session {session.id} in project {project_name}")
            return f"✅ Started session: {session_title} (ID: {session.id})"
            
        except Exception as e:
            logger.error(f"Failed to start starlog session: {e}")
            return f"❌ Error starting session: {str(e)}"
    
    def end_starlog(self, session_id: str, end_content: str, path: str) -> str:
        """End current session with summary."""
        try:
            project_name = self._get_project_name_from_path(path)
            
            # Load existing session
            session = self._load_starlog_entry(project_name, session_id)
            if not session:
                return f"❌ Session {session_id} not found"
            
            # End the session
            session.end_session(end_content)
            
            # Save updated session back to registry
            self._update_registry_item(project_name, "starlog", session_id, session.model_dump(mode='json'))
            
            logger.info(f"Ended starlog session {session_id} in project {project_name}")
            return f"✅ Ended session: {session.session_title} (Duration: {session.duration_minutes} minutes)"
            
        except Exception as e:
            logger.error(f"Failed to end starlog session: {e}")
            return f"❌ Error ending session: {str(e)}"
    
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