#!/usr/bin/env python3
"""
Verification script for Vertex AI Memory Bank integration.

This script checks that the integration is properly configured and can
initialize both in-memory and Vertex AI services.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment():
    """Check environment configuration."""
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 60)
    
    # Check required variables
    api_key = os.environ.get("GOOGLE_API_KEY")
    print(f"\n✓ GOOGLE_API_KEY: {'✓ Set' if api_key else '✗ Not Set (REQUIRED)'}")
    
    # Check optional Vertex AI variables
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    engine_id = os.environ.get("VERTEX_AGENT_ENGINE_ID")
    
    print(f"\nVertex AI Configuration (Optional):")
    print(f"  GOOGLE_CLOUD_PROJECT: {'✓ ' + project_id if project_id else '✗ Not Set'}")
    print(f"  GOOGLE_CLOUD_LOCATION: {'✓ ' + location if location else '✗ Not Set (defaults to us-central1)'}")
    print(f"  VERTEX_AGENT_ENGINE_ID: {'✓ ' + engine_id if engine_id else '✗ Not Set'}")
    
    vertex_configured = bool(project_id and engine_id)
    
    print(f"\nExpected Mode: {'🌩️  VERTEX AI' if vertex_configured else '💾 IN-MEMORY'}")
    
    return vertex_configured, bool(api_key)


def test_service_initialization():
    """Test that services can be initialized."""
    print("\n" + "=" * 60)
    print("SERVICE INITIALIZATION TEST")
    print("=" * 60)
    
    try:
        # Mock streamlit's cache_resource decorator
        import unittest.mock as mock
        
        with mock.patch('streamlit.cache_resource', lambda f: f):
            # Import after patching
            from services.memory import get_memory_service, get_session_service
            
            print("\n🔄 Initializing Memory Service...")
            memory_service = get_memory_service()
            memory_type = memory_service.__class__.__name__
            print(f"  ✓ Memory Service: {memory_type}")
            
            print("\n🔄 Initializing Session Service...")
            session_service = get_session_service()
            session_type = session_service.__class__.__name__
            print(f"  ✓ Session Service: {session_type}")
            
            print("\n🔄 Initializing Story Engine...")
            from services.story_engine import StoryEngine
            engine = StoryEngine(session_service=session_service)
            print(f"  ✓ Story Engine initialized with {session_type}")
            
            return True, memory_type, session_type
            
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def verify_files():
    """Verify that all required files exist."""
    print("\n" + "=" * 60)
    print("FILE VERIFICATION")
    print("=" * 60)
    
    required_files = [
        ("services/memory.py", "Memory service module"),
        ("services/story_engine.py", "Story engine module"),
        ("app.py", "Main application"),
        (".env.example", "Environment template"),
        ("README.md", "Documentation"),
        ("VERTEX_AI_SETUP.md", "Vertex AI setup guide"),
        ("INTEGRATION_SUMMARY.md", "Integration summary"),
        ("tests/test_vertex_integration.py", "Integration tests"),
    ]
    
    all_exist = True
    for file_path, description in required_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}: {description}")
        if not exists:
            all_exist = False
    
    return all_exist


def print_summary(vertex_configured, api_key_set, init_success, memory_type, session_type, files_ok):
    """Print verification summary."""
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Required Files", files_ok),
        ("API Key Configured", api_key_set),
        ("Service Initialization", init_success),
    ]
    
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    if init_success:
        print(f"\n📊 Service Types:")
        print(f"  Memory: {memory_type}")
        print(f"  Session: {session_type}")
    
    print(f"\n🎯 Current Configuration:")
    if vertex_configured:
        print("  Mode: VERTEX AI (Persistent Cloud Storage)")
        print("  ✓ Sessions will persist across restarts")
        print("  ✓ Long-term memory enabled")
        print("  ⚠️  GCP charges may apply")
    else:
        print("  Mode: IN-MEMORY (Default)")
        print("  ⚠️  Sessions will be lost on restart")
        print("  ℹ️  To enable Vertex AI, set:")
        print("     - GOOGLE_CLOUD_PROJECT")
        print("     - VERTEX_AGENT_ENGINE_ID")
    
    all_passed = all([files_ok, api_key_set, init_success])
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ VERIFICATION COMPLETE - ALL CHECKS PASSED")
    else:
        print("⚠️  VERIFICATION COMPLETE - SOME CHECKS FAILED")
    print("=" * 60)
    
    return all_passed


def main():
    """Main verification routine."""
    print("\n🔍 Story Crafter - Vertex AI Integration Verification")
    print("=" * 60)
    
    # Check environment
    vertex_configured, api_key_set = check_environment()
    
    # Verify files
    files_ok = verify_files()
    
    # Test initialization
    init_success, memory_type, session_type = test_service_initialization()
    
    # Print summary
    success = print_summary(
        vertex_configured, 
        api_key_set, 
        init_success, 
        memory_type, 
        session_type,
        files_ok
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

