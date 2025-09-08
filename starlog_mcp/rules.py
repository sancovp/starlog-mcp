"""Rules mixin for project rules and guidelines management."""

import logging
from typing import List
from .models import RulesEntry

logger = logging.getLogger(__name__)


class RulesMixin:
    """Handles project rules and guidelines management."""
    
    def rules(self, path: str) -> str:
        """Get all project rules."""
        try:
            project_name = self._get_project_name_from_path(path)
            rules_data = self._get_registry_data(project_name, "rules")
            
            if not rules_data:
                return "No project rules found. Use add_rule to create rules."
            
            return self._format_rules_list(rules_data)
            
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return f"❌ Error getting rules: {str(e)}"
    
    def add_rule(self, rule: str, path: str, category: str = "general") -> str:
        """Add single rule."""
        try:
            project_name = self._get_project_name_from_path(path)
            
            # Create new rule entry
            rule_entry = RulesEntry(rule=rule, category=category)
            
            # Save to registry
            self._save_rules_entry(project_name, rule_entry)
            
            logger.info(f"Added rule {rule_entry.id} to project {project_name}")
            return f"✅ Added rule: {rule} (ID: {rule_entry.id})"
            
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return f"❌ Error adding rule: {str(e)}"
    
    def delete_rule(self, rule_id: str, path: str) -> str:
        """Remove specific rule."""
        try:
            project_name = self._get_project_name_from_path(path)
            registry_name = f"{project_name}_rules"
            
            # Try to delete from registry (using Heaven registry delete functionality)
            from heaven_base.tools.registry_tool import registry_util_func
            result = registry_util_func("delete", registry_name=registry_name, key=rule_id)
            
            logger.info(f"Deleted rule {rule_id} from project {project_name}")
            return f"✅ Deleted rule: {rule_id}"
            
        except Exception as e:
            logger.error(f"Failed to delete rule: {e}")
            return f"❌ Error deleting rule: {str(e)}"
    
    def _format_rules_list(self, rules_data: dict) -> str:
        """Format rules list for display."""
        if not rules_data:
            return "No rules found."
        
        formatted = "📏 **Project Rules**\n\n"
        
        # Group by category
        by_category = {}
        for rule_id, rule_data in rules_data.items():
            category = rule_data.get("category", "general")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((rule_id, rule_data))
        
        # Format each category
        for category, category_rules in by_category.items():
            formatted += f"**{category.title()}**\n"
            for rule_id, rule_data in category_rules:
                priority = rule_data.get("priority", 5)
                rule_text = rule_data.get("rule", "")
                formatted += f"- [{priority}] {rule_text} `({rule_id})`\n"
            formatted += "\n"
        
        return formatted.strip()