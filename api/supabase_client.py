# api/supabase_client.py
import os
from supabase import create_client, Client

# GANTI DENGAN DATA DARI DASHBOARD SUPABASE KAMU
url = "https://xmsffgwcjeequpqjhvqi.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2ZmZ3djamVlcXVwcWpodnFpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA2MTE1OCwiZXhwIjoyMDg1NjM3MTU4fQ.vHQUwzZ83fYSgSnUcYnZ1jRhQFtqMzDGbvw54mUcRwA"

supabase: Client = create_client(url, key)