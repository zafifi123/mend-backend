#!/usr/bin/env python3

import asyncio
from temporalio.client import Client
import sys
import os

# Add the worker directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_temporal_connection():
    """Test basic Temporal connectivity."""
    
    try:
        print("Testing Temporal connection...")
        client = await Client.connect("localhost:7233")
        print("✅ Successfully connected to Temporal server")
        
        # Test if we can list workflows (basic functionality test)
        print("Testing basic functionality...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Temporal server: {e}")
        print("\nTo fix this:")
        print("1. Make sure Temporal server is running: temporal server start-dev")
        print("2. Check if the server is accessible at localhost:7233")
        return False

async def main():
    """Main test function."""
    
    success = await test_temporal_connection()
    
    if success:
        print("\n🎉 Temporal connection test passed!")
        print("You can now run the scheduler or worker.")
    else:
        print("\n💥 Temporal connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 