#!/usr/bin/env python3
"""
Quick verification script to test all dependencies
"""
import sys

def test_imports():
    """Test that all required packages can be imported"""
    print("🔍 Testing package imports...")
    print("-" * 60)
    
    packages = [
        ("can", "python-can"),
        ("matplotlib.pyplot", "matplotlib"),
        ("websockets", "websockets"),
        ("ocpp.v16", "ocpp"),
    ]
    
    all_ok = True
    for module, package in packages:
        try:
            __import__(module)
            print(f"✅ {package:20s} - OK")
        except ImportError as e:
            print(f"❌ {package:20s} - FAILED: {e}")
            all_ok = False
    
    print("-" * 60)
    
    if all_ok:
        print("✅ All packages installed correctly!")
        return True
    else:
        print("❌ Some packages are missing. Run:")
        print("   pip install -r requirements.txt")
        return False

def test_can_bus():
    """Test virtual CAN bus creation"""
    print("\n🔍 Testing virtual CAN bus...")
    print("-" * 60)
    
    try:
        import can
        bus = can.interface.Bus(interface="virtual", channel=0)
        print(f"✅ Virtual CAN bus created successfully")
        print(f"   Interface: virtual")
        print(f"   Channel: {bus.channel_info}")
        bus.shutdown()
        print("-" * 60)
        return True
    except Exception as e:
        print(f"❌ Failed to create CAN bus: {e}")
        print("-" * 60)
        return False

def test_python_version():
    """Check Python version"""
    print("\n🔍 Checking Python version...")
    print("-" * 60)
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("✅ Python version OK (3.11+)")
    else:
        print("⚠️  Python 3.11+ recommended")
    print("-" * 60)

def main():
    print("=" * 60)
    print("⚡ EV Anomaly Simulator - Environment Test")
    print("=" * 60)
    print()
    
    test_python_version()
    imports_ok = test_imports()
    can_ok = test_can_bus()
    
    print("\n" + "=" * 60)
    if imports_ok and can_ok:
        print("✅ Environment test PASSED")
        print("\nYou can now run the simulation:")
        print("  ./run_all.sh")
    else:
        print("❌ Environment test FAILED")
        print("\nPlease fix the issues above before running.")
    print("=" * 60)

if __name__ == "__main__":
    main()
