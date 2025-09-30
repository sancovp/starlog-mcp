"""Debug diary mixin for current project status management."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from .models import DebugDiaryEntry

logger = logging.getLogger(__name__)


class DebugDiaryMixin:
    """Handles debug diary operations for current project status."""
    
    def _generate_stardate(self) -> str:
        """Generate stardate in format YYYYMMDD.HHMM (e.g., 20250906.0940)."""
        now = datetime.now()
        return f"{now.strftime('%Y%m%d.%H%M')}"
    
    def view_debug_diary(self, path: str) -> str:
        """Get current project status from debug diary."""
        try:
            project_name = self._get_project_name_from_path(path)
            diary_data = self._get_registry_data(project_name, "debug_diary")
            
            if not diary_data:
                return "📓 **Debug Diary** (Empty)\n\nNo debug entries yet. Use add_debug_entry to start tracking."
            
            return self._format_debug_diary_entries(diary_data)
            
        except Exception as e:
            logger.error(f"Failed to get debug diary: {e}")
            return f"❌ Error getting debug diary: {str(e)}"
    
    def _handle_github_integration(self, entry: DebugDiaryEntry, result_msg: str) -> str:
        """Handle GitHub issue creation and updates."""
        if entry.bug_report and not entry.issue_id:
            try:
                issue_id = entry.create_github_issue()
                result_msg += f" (Created issue: {issue_id})"
            except Exception as e:
                result_msg += f" (Issue creation failed: {str(e)})"
        
        if entry.bug_fix and entry.issue_id:
            try:
                update_result = entry.update_github_issue()
                result_msg += f" ({update_result})"
            except Exception as e:
                result_msg += f" (Issue update failed: {str(e)})"
        
        return result_msg
    
    def _create_debug_entry(self, content: str, insights: Optional[str], in_file: Optional[str],
                           bug_report: bool, bug_fix: bool, issue_id: Optional[str]) -> DebugDiaryEntry:
        """Create a new debug diary entry."""
        return DebugDiaryEntry(
            content=content,
            insights=insights,
            in_file=in_file,
            bug_report=bug_report,
            bug_fix=bug_fix,
            issue_id=issue_id
        )
    
    def add_debug_entry(self, content: str, path: str, insights: Optional[str] = None, 
                       in_file: Optional[str] = None, bug_report: bool = False, 
                       bug_fix: bool = False, issue_id: Optional[str] = None) -> str:
        """Add new debug diary entry."""
        try:
            project_name = self._get_project_name_from_path(path)
            entry = self._create_debug_entry(content, insights, in_file, bug_report, bug_fix, issue_id)
            
            self._save_debug_diary_entry(project_name, entry)
            
            result_msg = "✅ Added debug entry"
            result_msg = self._handle_github_integration(entry, result_msg)
            
            logger.info(f"Added debug entry {entry.id} to project {project_name}")
            return result_msg
            
        except Exception as e:
            logger.error(f"Failed to add debug entry: {e}")
            return f"❌ Error adding debug entry: {str(e)}"
    
    def _format_debug_diary_entries(self, diary_data: dict) -> str:
        """Format debug diary entries for display."""
        if not diary_data:
            return "📓 **Debug Diary** (Empty)\n\nNo debug entries found."
        
        formatted = "📓 **Debug Diary**\n\n"
        
        # Sort entries by timestamp (newest first)
        entries = []
        for entry_id, entry_data in diary_data.items():
            entries.append((entry_id, entry_data))
        
        entries.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        
        # Format each entry
        for entry_id, entry_data in entries:
            timestamp = entry_data.get("timestamp", "").split("T")[0]  # Just the date
            content = entry_data.get("content", "")
            insights = entry_data.get("insights")
            in_file = entry_data.get("in_file")
            bug_report = entry_data.get("bug_report", False)
            bug_fix = entry_data.get("bug_fix", False)
            issue_id = entry_data.get("issue_id")
            
            formatted += f"**{timestamp}** `{entry_id}`\n"
            formatted += f"{content}\n"
            
            if insights:
                formatted += f"💡 *Insights*: {insights}\n"
            
            if in_file:
                formatted += f"📁 *File*: `{in_file}`\n"
            
            if bug_report and issue_id:
                formatted += f"🐛 *Issue*: {issue_id}\n"
            elif bug_fix and issue_id:
                formatted += f"✅ *Fixed Issue*: {issue_id}\n"
            
            formatted += "\n---\n\n"
        
        return formatted.strip()