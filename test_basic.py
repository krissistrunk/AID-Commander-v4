#!/usr/bin/env python3
"""
Basic validation test for AID Commander v4.0 structure
"""

import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required directories and files exist"""
    print("Testing project structure...")
    
    required_dirs = [
        'config',
        'utils', 
        'tests',
        'memory_bank',
        'quality',
        'patterns'
    ]
    
    required_files = [
        'aid_commander.py',
        'memory_service.py',
        'context_engine.py',
        'quality_gates.py',
        'conversation_manager.py',
        'pyproject.toml',
        '.env.template',
        'README.md'
    ]
    
    missing_dirs = []
    missing_files = []
    
    # Check directories
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
    
    # Check files
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_dirs:
        print(f"✗ Missing directories: {missing_dirs}")
    else:
        print("✓ All required directories present")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
    else:
        print("✓ All required files present")
    
    return len(missing_dirs) == 0 and len(missing_files) == 0

def test_basic_syntax():
    """Test that Python files have valid syntax"""
    print("\nTesting Python file syntax...")
    
    python_files = [
        'aid_commander.py',
        'memory_service.py', 
        'context_engine.py',
        'quality_gates.py',
        'conversation_manager.py',
        'config/settings.py',
        'utils/performance.py',
        'utils/validation.py',
        'utils/encryption.py'
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"✓ {file_path}")
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
                print(f"✗ {file_path}: {e}")
        else:
            print(f"? {file_path} (not found)")
    
    return len(syntax_errors) == 0

def test_config_loading():
    """Test configuration loading without external dependencies"""
    print("\nTesting configuration loading...")
    
    try:
        # Test loading settings without pydantic dependencies
        import config.settings as settings
        
        # Mock environment variables
        os.environ['SECRET_KEY'] = 'test_key'
        os.environ['AID_COMMANDER_VERSION'] = '4.0.0'
        
        config = settings.get_settings()
        
        if config.get('AID_COMMANDER_VERSION') == '4.0.0':
            print("✓ Configuration loading works")
            return True
        else:
            print("✗ Configuration values not loaded correctly")
            return False
            
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_memory_bank_structure():
    """Test memory bank file structure"""
    print("\nTesting memory bank structure...")
    
    try:
        # Test creating memory bank directory structure
        test_dir = Path("test_memory_bank")
        test_dir.mkdir(exist_ok=True)
        
        # Create basic memory files
        memory_files = [
            "project_essence.md",
            "active_context.md",
            "decision_history.md"
        ]
        
        for file_name in memory_files:
            (test_dir / file_name).write_text(f"# {file_name}\n\nTest content")
        
        # Verify files exist
        all_exist = all((test_dir / f).exists() for f in memory_files)
        
        if all_exist:
            print("✓ Memory bank structure can be created")
            
            # Cleanup
            import shutil
            shutil.rmtree(test_dir)
            return True
        else:
            print("✗ Memory bank file creation failed")
            return False
            
    except Exception as e:
        print(f"✗ Memory bank structure test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("AID Commander v4.0 - Basic Validation Tests")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_basic_syntax,
        test_config_loading,
        test_memory_bank_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("AID Commander v4.0 structure is valid!")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)