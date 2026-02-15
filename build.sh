#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Library
pip install -r requirements.txt

# 2. Kumpulin Static Files (CSS/JS Admin)
python manage.py collectstatic --no-input

# 3. Update Database (Migrate ke Supabase)
python manage.py migrate