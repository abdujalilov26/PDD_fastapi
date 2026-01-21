FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# Установка PyTorch CPU
RUN pip install --no-cache-dir \
    torch==2.8.0+cpu \
    torchvision==0.23.0+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html

COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY main.py .
COPY model_mc.pth .

EXPOSE 8011

CMD ["uvicorn", "main:cifar_app", "--host", "0.0.0.0", "--port", "8011", "--workers", "1"]