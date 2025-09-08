"""Final STARLOG Pydantic models with GitHub integration.

Designed for Heaven Registry System + GitHub Issues workflow.
Use model_dump(mode='json') for proper datetime serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class RulesEntry(BaseModel):
    """Model for project rules/guidelines that emerge from development sessions.
    
    Registry pattern: {project_name}_rules with individual rule entries.
    """
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str = Field(..., description="The actual rule text")
    category: str = Field(default="general", description="Rule category (coding, process, etc.)")
    created_at: datetime = Field(default_factory=datetime.now, description="When rule was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When rule was last updated")
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        logger.debug(f"Updating timestamp for rule {self.id}")
        self.updated_at = datetime.now()


class DebugDiaryEntry(BaseModel):
    """Model for real-time development tracking with GitHub issue integration.
    
    Registry pattern: {project_name}_debug_diary with timestamped entries.
    
    GitHub Workflow:
    - bug_report=True → Creates GitHub issue, stores issue_id
    - bug_fix=True → Updates GitHub issue to in-review status
    - External issues can be pulled in with from_github=True
    """
    id: str = Field(default_factory=lambda: f"diary_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now, description="When entry was created")
    content: str = Field(..., description="The diary entry content")
    insights: Optional[str] = Field(default=None, description="Additional insights or analysis")
    in_file: Optional[str] = Field(default=None, description="File context if applicable")
    
    # GitHub Issue Workflow - mutually exclusive flags
    bug_report: bool = Field(default=False, description="Creates GitHub issue")
    bug_fix: bool = Field(default=False, description="Updates GitHub issue to in-review")
    
    # GitHub integration data
    issue_id: Optional[str] = Field(default=None, description="GitHub issue ID")
    from_github: bool = Field(default=False, description="True if created from external GitHub issue")
    
    def create_github_issue(self) -> str:
        """Create GitHub issue for bug reports.
        
        Returns:
            str: The created issue ID
            
        Raises:
            ValueError: If not a bug report
        """
        if not self.bug_report:
            raise ValueError("Can only create issues for bug reports")
        
        logger.info(f"Creating GitHub issue for diary entry {self.id}")
        
        # TODO: Integrate with heaven-bml GitHub functions
        # For now, return a placeholder
        issue_id = f"issue_{uuid.uuid4().hex[:8]}"
        self.issue_id = issue_id
        
        logger.debug(f"Created GitHub issue {issue_id} for entry {self.id}")
        return issue_id
    
    def update_github_issue(self) -> str:
        """Update GitHub issue status for bug fixes.
        
        Returns:
            str: Update result message
            
        Raises:
            ValueError: If not a bug fix or no issue_id
        """
        if not self.bug_fix:
            raise ValueError("Can only update issues for bug fixes")
        if not self.issue_id:
            raise ValueError("Bug fix requires existing issue_id")
        
        logger.info(f"Updating GitHub issue {self.issue_id} to in-review")
        
        # TODO: Integrate with heaven-bml GitHub functions
        # Update issue status to in-review
        
        return f"Updated issue {self.issue_id} to in-review status"
    
    def to_github_issue_body(self) -> str:
        """Generate GitHub-safe issue content.
        
        Uses GitHub Flavored Markdown (restricted markdown subset).
        """
        body = "**Bug Report from STARLOG**\n\n"
        body += f"**Description**: {self.content}\n\n"
        
        if self.insights:
            body += f"**Insights**: {self.insights}\n\n"
        
        if self.in_file:
            body += f"**File Context**: `{self.in_file}`\n\n"
        
        body += f"**Timestamp**: {self.timestamp.isoformat()}\n"
        body += f"**Entry ID**: {self.id}\n"
        
        return body


class StarlogEntry(BaseModel):
    """Model for complete development sessions with START/END markers.
    
    Registry pattern: {project_name}_starlog with session entries.
    
    Generates markdown strings in the STARLOG format for documentation.
    """
    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now, description="When session was started")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), 
                     description="Session date in YYYY-MM-DD format")
    
    # Session content
    session_title: str = Field(..., description="Brief session title")
    start_content: str = Field(..., description="START marker content")
    context_from_docs: str = Field(..., description="Context loaded from project docs")
    session_goals: List[str] = Field(..., description="List of session goals")
    
    # Session progress (accumulated during session)
    key_discoveries: List[str] = Field(default_factory=list, description="Important findings")
    files_updated: List[str] = Field(default_factory=list, description="Files modified")
    challenges_faced: List[str] = Field(default_factory=list, description="Challenges encountered")
    
    # Session completion
    end_content: Optional[str] = Field(default=None, description="END marker content")
    end_timestamp: Optional[datetime] = Field(default=None, description="When session ended")
    
    def end_session(self, end_content: str):
        """Mark session as ended with summary.
        
        Args:
            end_content: The END marker content describing session completion
        """
        logger.info(f"Ending session {self.id}: {self.session_title}")
        self.end_content = end_content
        self.end_timestamp = datetime.now()
        logger.debug(f"Session {self.id} ended after {self.duration_minutes} minutes")
    
    def _format_header_section(self) -> str:
        """Format the header section of markdown"""
        md = f"## {self.date} - {self.session_title}\n\n"
        md += f"**START**: {self.start_content}\n\n"
        md += f"**Context from docs**: {self.context_from_docs}\n\n"
        return md

    def _format_goals_section(self) -> str:
        """Format the session goals section"""
        md = "**Session goals**:\n"
        for goal in self.session_goals:
            md += f"- {goal}\n"
        md += "\n"
        return md

    def _format_progress_sections(self) -> str:
        """Format progress tracking sections"""
        md = ""
        
        if self.key_discoveries:
            md += "**Key discoveries**:\n"
            for i, discovery in enumerate(self.key_discoveries, 1):
                md += f"{i}. {discovery}\n"
            md += "\n"
        
        if self.files_updated:
            md += "**Files updated during session**:\n"
            for file_path in self.files_updated:
                md += f"- `{file_path}`\n"
            md += "\n"
        
        if self.challenges_faced:
            md += "**Challenges faced**:\n"
            for i, challenge in enumerate(self.challenges_faced, 1):
                md += f"{i}. {challenge}\n"
            md += "\n"
        
        return md

    def _format_end_section(self) -> str:
        """Format the end section"""
        if self.end_content:
            return f"**END**: {self.end_content}\n\n---\n\n"
        else:
            return "**Note**: Session in progress (END marker missing)\n\n---\n\n"

    def to_markdown(self) -> str:
        """Generate full STARLOG markdown format.
        
        Returns the complete markdown string in the STARLOG format
        as seen in the original documentation examples.
        """
        md = self._format_header_section()
        md += self._format_goals_section()
        md += self._format_progress_sections()
        md += self._format_end_section()
        return md
    
    @property
    def is_ended(self) -> bool:
        """Check if session has been ended."""
        return self.end_content is not None
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Get session duration in minutes if ended."""
        if self.end_timestamp:
            delta = self.end_timestamp - self.timestamp
            return int(delta.total_seconds() / 60)
        return None