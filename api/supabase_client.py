# api/supabase_client.py
import os
from supabase import create_client, Client

# GANTI DENGAN DATA DARI DASHBOARD SUPABASE KAMU
url = "https://xmsffgwcjeequpqjhvqi.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2ZmZ3djamVlcXVwcWpodnFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwNjExNTgsImV4cCI6MjA4NTYzNzE1OH0.e2l6Xp-GI2E-u8kA5vesHK-rXZL_BM-WgWKDV5fUdGA"

supabase: Client = create_client(url, key)