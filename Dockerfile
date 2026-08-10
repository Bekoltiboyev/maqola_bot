FROM python:3.11-slim

WORKDIR /app

# Xavfsizlik: root bo'lmagan foydalanuvchi yaratamiz
RUN groupadd -r botgroup && useradd -r -g botgroup botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage/articles media \
    && chown -R botuser:botgroup /app

USER botuser

CMD ["python", "bot.py"]
