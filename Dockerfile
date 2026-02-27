# 1. Kita naikin ke Python 3.12 karena Django 6 wajib pakai ini!
FROM python:3.12-slim

# 2. Biar output error/print dari Django langsung muncul di terminal
ENV PYTHONUNBUFFERED=1

# 3. Bikin folder kerja di dalam container
WORKDIR /app

# 4. Copy file requirements.txt duluan
COPY requirements.txt .

# 5. Upgrade pip dulu, baru install requirements (biar mulus)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy seluruh sisa kodingan Django lu ke dalam container
COPY . .

# 7. Buka port 8000 (Port default Django)
EXPOSE 8000

# 8. Jalankan server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]