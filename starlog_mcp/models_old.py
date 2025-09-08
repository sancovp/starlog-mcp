"""Pydantic models for STARLOG system.

Designed for use with Heaven Registry System via registry_util_func.
Use model_dump(mode='json') for proper datetime serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class RulesEntry(BaseModel):
    """Model for project rules/guidelines.
    
    Use with registry pattern:
    rule_entry = RulesEntry(rule="Use descriptive variable names", category="coding")
    registry_util_func("add", registry_name=f"{project}_rules", 
                      key=rule_entry.id, value_dict=rule_entry.model_dump(mode='json'))
    """
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str = Field(..., description="The actual rule text")
    category: str = Field(default="general", description="Rule category (general, coding, testing, etc.)")
    created_at: datetime = Field(default_factory=datetime.now, description="When rule was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When rule was last updated")
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        logger.debug(f"Updating timestamp for rule {self.id}")
        self.updated_at = datetime.now()


class DebugDiaryEntry(BaseModel):
    """Model for debug diary status entries.
    
    Represents the current project status. Only one per project (key="current_status").
    
    Use with registry pattern:
    diary_entry = DebugDiaryEntry(status="Working on feature X", 
                                 current_state="Implemented core logic",
                                 next_steps=["Add tests", "Update docs"])
    registry_util_func("update", registry_name=f"{project}_debug_diary",
                      key="current_status", value_dict=diary_entry.model_dump(mode='json'))
    """
    timestamp: datetime = Field(default_factory=datetime.now, description="When status was last updated")
    status: str = Field(..., description="Brief status summary")
    current_state: str = Field(..., description="Detailed description of current state")
    next_steps: List[str] = Field(..., description="List of next steps to take")
    blockers: List[str] = Field(default_factory=list, description="Current blockers or issues")
    recent_changes: List[str] = Field(default_factory=list, description="Recent changes made")


class StarlogEntry(BaseModel):
    """Model for starlog session entries.
    
    Represents a complete development session with START and END.
    
    Use with registry pattern:
    session = StarlogEntry(session_title="Implement user auth",
                          start="Starting work on authentication system",
                          context_from_docs="Previous session left off at...",
                          session_goals=["Add login", "Add logout"])
    registry_util_func("add", registry_name=f"{project}_starlog",
                      key=session.id, value_dict=session.model_dump(mode='json'))
    """
    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now, description="When session was started")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), 
                     description="Session date in YYYY-MM-DD format")
    session_title: str = Field(..., description="Brief session title")
    start: str = Field(..., description="Session start context and goals")
    context_from_docs: str = Field(..., description="Context loaded from project docs")
    session_goals: List[str] = Field(..., description="List of session goals")
    
    # Session progress tracking
    key_discoveries: List[str] = Field(default_factory=list, description="Key insights discovered")
    files_updated: List[str] = Field(default_factory=list, description="Files modified during session")
    testing_results: List[str] = Field(default_factory=list, description="Test outcomes")
    challenges_faced: List[str] = Field(default_factory=list, description="Challenges encountered")
    
    # Session completion
    end: Optional[str] = Field(default=None, description="Session end summary")
    session_summary: Optional[str] = Field(default=None, description="Overall session summary")
    end_timestamp: Optional[datetime] = Field(default=None, description="When session ended")
    
    def end_session(self, end_content: str, session_summary: str):
        """Mark session as ended with summary"""
        logger.info(f"Ending session {self.id}: {self.session_title}")
        self.end = end_content
        self.session_summary = session_summary
        self.end_timestamp = datetime.now()
        logger.debug(f"Session {self.id} ended after {self.duration_minutes} minutes")
    
    @property
    def is_ended(self) -> bool:
        """Check if session has been ended"""
        return self.end is not None
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Get session duration in minutes if ended"""
        if self.end_timestamp:
            delta = self.end_timestamp - self.timestamp
            return int(delta.total_seconds() / 60)
        return None