import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import io
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from pdd_app.db.database import SessionLocal
from pdd_app.db.models import PddModel
from enum import Enum as PyEnum



class CheckImage(nn.Module):
  def __init__(self):
     super().__init__()
     self.first = nn.Sequential(
        nn.Conv2d(3, 16, kernel_size=3, padding=1),
        nn.BatchNorm2d(16),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(16, 32, kernel_size=3, padding=1),
        nn.BatchNorm2d(32),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(32, 64, kernel_size=3, padding=1),
        nn.BatchNorm2d(64),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(64, 128, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.AdaptiveAvgPool2d((8, 8))
      )
     self.second = nn.Sequential(
        nn.Flatten(),
        nn.Linear(128 * 8 * 8, 256), # Corrected input size
        nn.ReLU(),
        nn.Linear(256, 15)
     )

  def forward(self, image):
    image = self.first(image)
    image = self.second(image)
    return image




transform_data = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])


#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#MODEL_PATH = BASE_DIR / "pdd_app" / "model.pth"


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CheckImage()
model.load_state_dict(torch.load('model_PDD (3).pth', map_location=device))
model.to(device)
model.eval()




pdd_router = APIRouter(prefix='/pdd', tags=['ПДД'])


pdd_info = {
    0:  {"name": "Speed limit 30 km/h", "category": "Запрещающий знак", "description": "Ограничение скорости до 30 км/ч"},
    1:  {"name": "Speed limit 50 km/h", "category": "Запрещающий знак", "description": "Ограничение скорости до 50 км/ч"},
    2:  {"name": "Speed limit 70 km/h", "category": "Запрещающий знак", "description": "Ограничение скорости до 70 км/ч"},
    3:  {"name": "Access Denied", "category": "Запрещающий знак", "description": "Доступ запрещён для всех транспортных средств или определённых типов"},
    4:  {"name": "Bumper", "category": "Предупреждающий знак", "description": "Лежачий полицейский — препятствие для снижения скорости"},
    5:  {"name": "Close Road", "category": "Запрещающий знак", "description": "Дорога закрыта"},
    6:  {"name": "Left Turn", "category": "Предписывающий знак", "description": "Разрешён или обязателен поворот налево"},
    7:  {"name": "One Way Road", "category": "Предписывающий знак", "description": "Дорога с односторонним движением"},
    8:  {"name": "Parking", "category": "Информационный знак", "description": "Место для парковки транспортных средств"},
    9:  {"name": "Pedestrian Crosswalk", "category": "Предупреждающий знак", "description": "Пешеходный переход, уступить дорогу пешеходам"},
    10: {"name": "Right Turn", "category": "Предписывающий знак", "description": "Разрешён или обязателен поворот направо"},
    11: {"name": "Roundabout", "category": "Предписывающий знак", "description": "Круговое движение, соблюдать правила кольца"},
    12: {"name": "Stop", "category": "Запрещающий знак", "description": "Полная остановка перед пересечением обязательна"},
    13: {"name": "Uneven Road", "category": "Предупреждающий знак", "description": "Неровная дорога, кочки, выбоины, снижайте скорость"},
    14: {"name": "Yield", "category": "Знаки приоритета", "description": "Уступите дорогу другим участникам движения"}
}



@pdd_router.post('/predict/')
async def check_image(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail='Файл не получен')

        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        img_tensor = transform_data(img).unsqueeze(0).to(device)

        with torch.no_grad():
            y_pred = model(img_tensor)
            pred = y_pred.argmax(dim=1).item()

        record_info = pdd_info.get(pred, {"name": "Unknown", "category": "Неизвестно", "description": ""})

        db = SessionLocal()
        try:
            record = PddModel(
                name=record_info["name"],
                category=record_info["category"],
                description=record_info["description"],
                images="uploaded_image.png"
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        finally:
            db.close()

        return {
            "class_id": pred,
            "class_name": record_info["name"],
            "category": record_info["category"],
            "description": record_info["description"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))