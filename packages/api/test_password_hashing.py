#!/usr/bin/env python3
"""
Test script to verify password hashing compatibility.
Tests bcrypt directly (without passlib) for Python 3.13 + Alpine compatibility.
"""
import sys
import bcrypt
from datetime import datetime

def test_bcrypt_hashing():
    """Test bcrypt password hashing and verification."""
    print("=" * 60)
    print("Testing bcrypt password hashing (Python 3.13 compatible)")
    print("=" * 60)
    
    # Test password
    password = "testpass123"
    password_bytes = password.encode('utf-8')
    
    print(f"\n1. Testing password: '{password}'")
    print(f"   Python version: {sys.version}")
    print(f"   bcrypt version: {bcrypt.__version__ if hasattr(bcrypt, '__version__') else 'unknown'}")
    
    # Generate hash
    try:
        print("\n2. Generating hash...")
        salt = bcrypt.gensalt(rounds=12)  # Standard security rounds
        hashed = bcrypt.hashpw(password_bytes, salt)
        hashed_str = hashed.decode('utf-8')
        
        print(f"   ✅ Hash generated successfully")
        print(f"   Hash length: {len(hashed_str)} characters")
        print(f"   Hash preview: {hashed_str[:20]}...")
        
    except Exception as e:
        print(f"   ❌ Error generating hash: {e}")
        return False
    
    # Verify password
    try:
        print("\n3. Verifying password...")
        is_valid = bcrypt.checkpw(password_bytes, hashed)
        
        if is_valid:
            print(f"   ✅ Password verification successful")
        else:
            print(f"   ❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error verifying password: {e}")
        return False
    
    # Test wrong password
    try:
        print("\n4. Testing wrong password...")
        wrong_password = "wrongpass".encode('utf-8')
        is_valid = bcrypt.checkpw(wrong_password, hashed)
        
        if not is_valid:
            print(f"   ✅ Wrong password correctly rejected")
        else:
            print(f"   ❌ Wrong password incorrectly accepted")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing wrong password: {e}")
        return False
    
    # Test hash persistence (simulate database storage)
    try:
        print("\n5. Testing hash persistence...")
        # Simulate storing hash as string and retrieving
        stored_hash = hashed_str
        retrieved_hash = stored_hash.encode('utf-8')
        is_valid = bcrypt.checkpw(password_bytes, retrieved_hash)
        
        if is_valid:
            print(f"   ✅ Hash persistence works correctly")
        else:
            print(f"   ❌ Hash persistence failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing hash persistence: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - bcrypt is compatible!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_bcrypt_hashing()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Please install bcrypt: pip install bcrypt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
































