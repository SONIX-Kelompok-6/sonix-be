import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Kasih pengecekan biar gak error kalau variable-nya kosong
if url and key:
    supabase: Client = create_client(url, key)
else:
    supabase = None