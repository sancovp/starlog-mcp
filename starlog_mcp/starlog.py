"""Main STARLOG singleton class combining all functionality."""

import os
import json
import logging
import traceback
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import Heaven registry system
try:
    from heaven_base.tools.registry_tool import registry_util_func
except ImportError:
    # Fallback for development
    logger.warning(f"Heaven registry not available, using fallback: {traceback.format_exc()}")
    def registry_util_func(*args, **kwargs):
        return "Heaven registry not available - using fallback"

from .debug_diary import DebugDiaryMixin
from .starlog_sessions import StarlogSessionsMixin
from .rules import RulesMixin
from .hpi_system import HpiSystemMixin
from .models import RulesEntry, DebugDiaryEntry, StarlogEntry, FlightConfig

logger = logging.getLogger(__name__)


class Starlog(DebugDiaryMixin, StarlogSessionsMixin, RulesMixin, HpiSystemMixin):
    """Main STARLOG singleton class combining all functionality."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        logger.info("Initialized STARLOG singleton with HEAVEN registry system")
    
    def init_project(self, path: str, name: str, description: str = "") -> str:
        """Create new project with registries and starlog.hpi."""
        try:
            # Create project directory if it doesn't exist
            os.makedirs(path, exist_ok=True)
            
            # Create project registries
            self._create_project_registry(name, "rules")
            self._create_project_registry(name, "debug_diary") 
            self._create_project_registry(name, "starlog")
            
            # Create starlog.hpi file
            hpi_path = os.path.join(path, "starlog.hpi")
            hpi_content = self._create_default_hpi_content(name, description)
            
            with open(hpi_path, 'w') as f:
                json.dump(hpi_content, f, indent=2)
            
            logger.info(f"Initialized STARLOG project '{name}' at {path}")
            return f"✅ Initialized STARLOG project '{name}' with registries and starlog.hpi"
            
        except Exception as e:
            logger.error(f"Failed to initialize project: {traceback.format_exc()}")
            return f"❌ Failed to initialize project: {str(e)}"
    
    def _get_registry_status(self, project_name: str) -> Dict[str, int]:
        """Get registry status for all project registries."""
        rules_data = self._get_registry_data(project_name, "rules")
        diary_data = self._get_registry_data(project_name, "debug_diary") 
        starlog_data = self._get_registry_data(project_name, "starlog")
        
        return {
            "rules": len(rules_data),
            "debug_diary": len(diary_data),
            "starlog": len(starlog_data)
        }
    
    def _build_project_status(self, project_name: str) -> Dict[str, Any]:
        """Build project status info for valid STARLOG projects."""
        registry_status = self._get_registry_status(project_name)
        
        return {
            "is_starlog_project": True,
            "project_name": project_name,
            "hpi_file_exists": True,
            "registries": registry_status
        }
    
    def check(self, path: str) -> Dict[str, Any]:
        """Check if directory is a STARLOG project."""
        try:
            hpi_path = os.path.join(path, "starlog.hpi")
            is_starlog_project = os.path.exists(hpi_path)
            
            if is_starlog_project:
                project_name = self._get_project_name_from_path(path)
                return self._build_project_status(project_name)
            else:
                return {
                    "is_starlog_project": False,
                    "hpi_file_exists": False
                }
                
        except Exception as e:
            logger.error(f"Error checking project: {traceback.format_exc()}")
            return {
                "is_starlog_project": False,
                "error": str(e)
            }
    
    # Heaven registry utilities for all mixins
    def _create_project_registry(self, project_name: str, registry_type: str) -> str:
        """Create registry for project using Heaven registry system."""
        registry_name = f"{project_name}_{registry_type}"
        result = registry_util_func("create_registry", registry_name=registry_name)
        logger.debug(f"Created registry {registry_name}: {result}")
        return result
    
    def _get_registry_data(self, project_name: str, registry_type: str) -> Dict[str, Any]:
        """Get all data from registry using Heaven registry system."""
        registry_name = f"{project_name}_{registry_type}"
        result = registry_util_func("get_all", registry_name=registry_name)
        
        # Parse the result string to extract the actual data
        if "Items in registry" in result:
            # Extract the dictionary part from the result string
            try:
                start_idx = result.find("{") 
                if start_idx != -1:
                    dict_str = result[start_idx:]
                    # Handle Python literals (None, True, False) in the registry data
                    dict_str = dict_str.replace("None", "null").replace("True", "true").replace("False", "false")
                    return json.loads(dict_str.replace("'", '"'))
            except Exception:
                logger.warning(f"Failed to parse registry result: {traceback.format_exc()}")
        
        return {}
    
    def _add_to_registry(self, project_name: str, registry_type: str, key: str, value: Any) -> str:
        """Add item to registry using Heaven registry system."""
        registry_name = f"{project_name}_{registry_type}"
        
        # Check if this is the first item being added to a rules registry
        is_first_rule = (registry_type == "rules" and 
                        self._is_registry_empty(registry_name))
        
        if isinstance(value, dict):
            result = registry_util_func("add", registry_name=registry_name, key=key, value_dict=value)
        else:
            result = registry_util_func("add", registry_name=registry_name, key=key, value_str=str(value))
        
        # Auto-create brain when first rule is added
        if is_first_rule and "added to registry" in result:
            self._auto_create_rules_brain(project_name, registry_name)
        
        logger.debug(f"Added {key} to {registry_name}: {result}")
        return result
    
    def _is_registry_empty(self, registry_name: str) -> bool:
        """Check if registry is empty or doesn't exist."""
        try:
            result = registry_util_func("get_all", registry_name=registry_name)
            return "{}" in result or "not found" in result or not result.strip()
        except:
            return True
    
    def _auto_create_rules_brain(self, project_name: str, registry_name: str) -> None:
        """Auto-create brain-agent brain when rules registry is created."""
        try:
            from brain_agent.manager_tools import brain_manager_func
            
            brain_id = f"{project_name}_rules_brain"
            result = brain_manager_func(
                operation="add",
                brain_id=brain_id,
                name=f"{project_name} Rules Brain",
                neuron_source_type="registry_keys",
                neuron_source=registry_name,
                chunk_max=30000
            )
            
            if "added to registry" in result:
                logger.info(f"✅ Auto-created rules brain '{brain_id}' for project '{project_name}'")
            else:
                logger.warning(f"Failed to auto-create rules brain: {result}")
                
        except ImportError:
            logger.info("brain-agent not available - skipping auto brain creation")
        except Exception as e:
            logger.warning(f"Failed to auto-create rules brain: {e}")
    
    def _update_registry_item(self, project_name: str, registry_type: str, key: str, value: Any) -> str:
        """Update item in registry using Heaven registry system."""
        registry_name = f"{project_name}_{registry_type}"
        
        if isinstance(value, dict):
            result = registry_util_func("update", registry_name=registry_name, key=key, value_dict=value)
        else:
            result = registry_util_func("update", registry_name=registry_name, key=key, value_str=str(value))
        
        logger.debug(f"Updated {key} in {registry_name}: {result}")
        return result
    
    def _get_from_registry(self, project_name: str, registry_type: str, key: str) -> Any:
        """Get specific item from registry using Heaven registry system."""
        registry_name = f"{project_name}_{registry_type}"
        result = registry_util_func("get", registry_name=registry_name, key=key)
        
        # Parse the result string to extract the actual data
        if f"Item '{key}' in registry" in result:
            try:
                start_idx = result.find(": ") + 2
                if start_idx > 1:
                    data_str = result[start_idx:]
                    if data_str.startswith(('{', '[')):
                        # Handle Python literals (None, True, False) in the registry data
                        data_str = data_str.replace("None", "null").replace("True", "true").replace("False", "false")
                        return json.loads(data_str.replace("'", '"'))
                    else:
                        return data_str
            except Exception:
                logger.warning(f"Failed to parse registry item: {traceback.format_exc()}")
        
        return None
    
    def _get_project_name_from_path(self, path: str) -> str:
        """Extract project name from path - checks for starlog.hpi file."""
        hpi_path = os.path.join(path, "starlog.hpi")
        if os.path.exists(hpi_path):
            return self._get_project_name_from_hpi(hpi_path)
        else:
            # Default to directory name
            return os.path.basename(os.path.abspath(path))
    
    def _get_project_name_from_hpi(self, hpi_path: str) -> str:
        """Extract project name from .hpi file content."""
        try:
            with open(hpi_path, 'r') as f:
                hpi_data = json.load(f)
                return hpi_data.get('project_name', os.path.basename(os.path.dirname(hpi_path)))
        except:
            return os.path.basename(os.path.dirname(hpi_path))
    
    # Model-registry operations
    def _save_rules_entry(self, project_name: str, rule: RulesEntry) -> str:
        """Save RulesEntry to registry."""
        try:
            result = self._add_to_registry(project_name, "rules", rule.id, rule.model_dump(mode='json'))
            logger.debug(f"Saved rule {rule.id} to {project_name}_rules")
            return result
        except Exception as e:
            logger.error(f"Failed to save rule: {traceback.format_exc()}")
            raise e
    
    def _load_rules_entry(self, project_name: str, rule_id: str) -> Optional[RulesEntry]:
        """Load RulesEntry from registry."""
        try:
            rule_data = self._get_from_registry(project_name, "rules", rule_id)
            if rule_data:
                return RulesEntry(**rule_data)
            return None
        except Exception as e:
            logger.error(f"Failed to load rule {rule_id}: {traceback.format_exc()}")
            return None
    
    def _save_debug_diary_entry(self, project_name: str, entry: DebugDiaryEntry) -> str:
        """Save DebugDiaryEntry to registry."""
        try:
            result = self._add_to_registry(project_name, "debug_diary", entry.id, entry.model_dump(mode='json'))
            logger.debug(f"Saved debug diary entry {entry.id} to {project_name}_debug_diary")
            return result
        except Exception as e:
            logger.error(f"Failed to save debug diary entry: {traceback.format_exc()}")
            raise e
    
    def _load_debug_diary_entry(self, project_name: str, entry_id: str) -> Optional[DebugDiaryEntry]:
        """Load DebugDiaryEntry from registry."""
        try:
            entry_data = self._get_from_registry(project_name, "debug_diary", entry_id)
            if entry_data:
                return DebugDiaryEntry(**entry_data)
            return None
        except Exception as e:
            logger.error(f"Failed to load debug diary entry {entry_id}: {traceback.format_exc()}")
            return None
    
    def _save_starlog_entry(self, project_name: str, session: StarlogEntry) -> str:
        """Save StarlogEntry to registry."""
        try:
            result = self._add_to_registry(project_name, "starlog", session.id, session.model_dump(mode='json'))
            logger.debug(f"Saved starlog session {session.id} to {project_name}_starlog")
            return result
        except Exception as e:
            logger.error(f"Failed to save starlog session: {traceback.format_exc()}")
            raise e
    
    def _load_starlog_entry(self, project_name: str, session_id: str) -> Optional[StarlogEntry]:
        """Load StarlogEntry from registry."""
        try:
            session_data = self._get_from_registry(project_name, "starlog", session_id)
            if session_data:
                return StarlogEntry(**session_data)
            return None
        except Exception as e:
            logger.error(f"Failed to load starlog session {session_id}: {traceback.format_exc()}")
            return None
    
    def _save_flight_config(self, flight_config: FlightConfig) -> str:
        """Save FlightConfig to global registry."""
        try:
            result = registry_util_func("add", "starlog_flight_configs", flight_config.id, flight_config.model_dump(mode='json'))
            logger.debug(f"Saved flight config {flight_config.id} to starlog_flight_configs")
            return result
        except Exception as e:
            logger.error(f"Failed to save flight config: {traceback.format_exc()}")
            raise e
    
    def _load_flight_config(self, flight_id: str) -> Optional[FlightConfig]:
        """Load FlightConfig from global registry."""
        try:
            flight_data = registry_util_func("get", "starlog_flight_configs", flight_id)
            if flight_data:
                return FlightConfig(**flight_data)
            return None
        except Exception as e:
            logger.error(f"Failed to load flight config {flight_id}: {traceback.format_exc()}")
            return None
    
    def _get_flight_configs_registry_data(self) -> Dict[str, Any]:
        """Get all flight configs from registry."""
        try:
            result = registry_util_func("list", "starlog_flight_configs")
            if isinstance(result, dict):
                return result
            return {}
        except Exception as e:
            logger.error(f"Failed to get flight configs: {traceback.format_exc()}")
            return {}