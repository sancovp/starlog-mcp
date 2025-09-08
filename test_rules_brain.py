#!/usr/bin/env python3
"""
Test STARLOG rules brain integration
"""

import asyncio
import os
from starlog_mcp.rules_brain_integration import StarlogRulesBrainIntegration

async def test_rules_brain():
    """Test the rules brain integration."""
    print("🧠 Testing STARLOG Rules Brain Integration")
    print("=" * 50)
    
    # Set required environment variable
    os.environ['HEAVEN_DATA_DIR'] = '/tmp/heaven_data'
    
    # Create integration
    integration = StarlogRulesBrainIntegration()
    
    # Test with hello world project path
    project_path = "/tmp/hello_world_project"
    
    print(f"\n📁 Project path: {project_path}")
    
    # Create rules brain
    try:
        brain_id = integration.create_rules_brain(project_path)
        print(f"✅ Created brain: {brain_id}")
    except Exception as e:
        print(f"❌ Brain creation failed: {e}")
        return
    
    # Test query
    try:
        context = "I'm writing a Python validation function"
        print(f"\n🔍 Query context: {context}")
        
        guidance = await integration.query_rules_brain(project_path, context)
        print(f"\n📝 Guidance received:")
        print(guidance)
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rules_brain())