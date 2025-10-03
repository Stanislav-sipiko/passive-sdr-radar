FROM python:3.10-slim

# Установим системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential git wget \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Скопировать requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Установить зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

# Скопировать код
COPY passive_radar/ passive_radar/
COPY examples/ examples/
COPY tests/ tests/

# Запуск по умолчанию
CMD ["pytest", "-v"]
