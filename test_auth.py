import auth
import os

print("Testing auth configuration...")
try:
    configured = auth.is_configured()
    print(f"Is configured: {configured}")
except Exception as e:
    print(f"Error checking configuration: {e}")

print("Testing Supabase initialization...")
try:
    client = auth.init_supabase()
    if client:
        print("Supabase initialized successfully")
    else:
        print("Supabase initialization returned None")
except Exception as e:
    print(f"Error initializing Supabase: {e}")
