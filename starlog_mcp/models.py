"""Final STARLOG Pydantic models with GitHub integration.

Designed for Heaven Registry System + GitHub Issues workflow.
Use model_dump(mode='json') for proper datetime serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from payload_discovery.core import PayloadDiscovery

logger = logging.getLogger(__name__)


class RulesEntry(BaseModel):
    """Model for project rules/guidelines with intelligent brain-agent enforcement.
    
    Registry pattern: {project_name}_rules with individual rule entries.
    Used by brain-agent system to analyze changes and provide compliance guidance.
    
    TODO: Rules hierarchy system needed:
    - Global rules: Apply to all work across entire project
    - Project rules (global for project): Apply to all modules within this project  
    - Module rules: Apply only to specific modules/contexts within project
    Need scope field and brain-agent logic to determine which rules apply to current work context.
    
    TODO: Language-specific rules system:
    - Global rules should have language enum (python, javascript, rust, etc.)
    - Project config should specify primary language
    - Brain-agent should filter rules by language relevance for current work context
    """
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str = Field(..., description="The actual rule text")
    category: str = Field(default="general", description="Rule category (coding, process, security, etc.)")
    created_at: datetime = Field(default_factory=datetime.now, description="When rule was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When rule was last updated")
    
    # Brain-agent enforcement fields
    priority: int = Field(default=5, description="Rule priority 1-10 (10=critical)", ge=1, le=10)
    applies_to: List[str] = Field(default_factory=list, description="File patterns this rule applies to (*.py, api/*, etc.)")
    violation_examples: List[str] = Field(default_factory=list, description="Examples of rule violations")
    enforcement_level: str = Field(default="warning", description="How strictly to enforce: error|warning|suggestion")
    related_rules: List[str] = Field(default_factory=list, description="Related rule IDs")
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        logger.debug(f"Updating timestamp for rule {self.id}")
        self.updated_at = datetime.now()
    
    def to_brain_knowledge(self) -> dict:
        """Convert rule to brain-agent knowledge format.
        
        Returns structured knowledge that brain-agent can reason about.
        """
        return {
            "type": "rule",
            "rule_text": self.rule,
            "category": self.category,
            "priority": self.priority,
            "enforcement_level": self.enforcement_level,
            "applies_to": self.applies_to,
            "violation_examples": self.violation_examples,
            "related_rules": self.related_rules,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": {
                "source": "starlog_rules",
                "project_rule_id": self.id
            }
        }
    
    @classmethod
    def from_violation_pattern(cls, violation_description: str, rule_text: str, 
                              category: str = "general", priority: int = 5) -> "RulesEntry":
        """Create rule from discovered violation pattern.
        
        Args:
            violation_description: Description of the violation that led to this rule
            rule_text: The actual rule text
            category: Rule category
            priority: Rule priority (1-10)
            
        Returns:
            New RulesEntry with violation example included
        """
        logger.info(f"Creating rule from violation pattern: {category}")
        
        return cls(
            rule=rule_text,
            category=category,
            priority=priority,
            violation_examples=[violation_description]
        )


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
    
    # TODO: Rules context strategy - add applicable_rules field
    # applicable_rules: List[str] = Field(default_factory=list, description="Rule names that apply to this work")
    # Validate rule names exist, provide helpful error: "Rule 'x' invalid. Check rules(path) for valid names."
    # Alternative: brain-agent selects applicable rules, or carry rules from session END
    
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
    relevant_docs: List[str] = Field(default_factory=list, description="File paths, URLs, or search queries relevant to this session")
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
        if self.relevant_docs:
            md += f"**Relevant docs**: {', '.join(self.relevant_docs)}\n\n"
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


class StarlogPayloadDiscoveryConfig(PayloadDiscovery):
    """PayloadDiscovery that contains the unchanging base STARLOG session management."""
    
    def __init__(self, **data):
        # Set the base STARLOG session management workflow
        base_data = {
            "domain": "starlog_session",
            "version": "v1", 
            "entry_point": "01_check.md",
            "root_files": [
                {
                    "filename": "01_check.md",
                    "title": "Check STARLOG Project",
                    "content": "STARLOG System - Development Session Tracking Flow\n\nStep 1: Check if directory is a STARLOG project\nUse: check(path)\n\nThis verifies if the current directory is already set up as a STARLOG project.",
                    "sequence_number": 1
                },
                {
                    "filename": "02_init_or_orient.md", 
                    "title": "Initialize or Orient",
                    "content": "Step 2: Setup project context\n\nIf NOT a STARLOG project:\n→ Use: init_project(path, name, description) - Creates project structure with registries and HPI template\n\nIf IS a STARLOG project:\n→ Use: orient(path) - Returns full Captain's Log XML context for existing projects",
                    "sequence_number": 2
                },
                {
                    "filename": "03_start_session.md",
                    "title": "Start STARLOG Session", 
                    "content": "Step 3: Begin tracked development session\nUse: start_starlog(session_data, path)\n\nBegin tracked development session with goals and context. This starts the formal logging process.",
                    "sequence_number": 3
                },
                {
                    "filename": "04_work_loop.md",
                    "title": "Work Loop - Development Activities",
                    "content": "Step 4: Work Loop - Choose tools as needed during development:\n\n• update_debug_diary(entry, path) - Log real-time discoveries, bugs, insights during work\n• view_debug_diary(path) - Check current project status and recent entries  \n• view_starlog(path) - Review session history and past work\n• rules(path) - View project guidelines and standards\n• add_rule(rule, path) - Create new project guideline or standard\n\nUse these tools throughout your development work to track progress and maintain documentation.",
                    "sequence_number": 4
                },
                {
                    "filename": "05_end_session.md",
                    "title": "End STARLOG Session",
                    "content": "Step 5: Complete session with summary\nUse: end_starlog(session_id, summary, path)\n\nComplete session with summary and outcomes. This formally closes the development session and saves all context.\n\nSTARLOG creates Captain's Log style XML output for AI context injection.",
                    "sequence_number": 5
                }
            ],
            "directories": {}
        }
        # Merge with any provided data
        base_data.update(data)
        super().__init__(**base_data)


class FlightConfig(BaseModel):
    """Flight configs extend the work_loop with a waypoint subchain.
    
    Registry pattern: starlog_flight_configs with global entries that can be scoped to projects.
    Flight configs can only add one thing: a waypoint subchain that executes as part of the work_loop phase.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique flight config ID")
    name: str = Field(..., description="Flight config name (must end with '_flight_config')")
    original_project_path: str = Field(..., description="Path where this flight config was created")
    category: str = Field(default="general", description="Flight config category (research, development, analysis, etc.)")
    description: str = Field(..., description="What this flight pattern adds")
    
    # The only extension point: optional waypoint subchain
    work_loop_subchain: Optional[str] = Field(
        default=None, 
        description="Path to PayloadDiscovery JSON config for subchain execution"
    )
    
    created_at: datetime = Field(default_factory=datetime.now, description="When flight config was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When flight config was last updated")
    
    class Config:
        # Allow datetime serialization and PayloadDiscovery objects
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True