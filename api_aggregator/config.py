import json
from pathlib import Path
from typing import List
from pydantic import ValidationError
from models import SourceConfig, AppConfig

def load_config(conf_path: str) -> List[SourceConfig]:
    conf_file = Path(conf_path)
    if not conf_file.exists():
        raise FileNotFoundError(f"Файл по пути {conf_path} не найден")
    try:
        with open(conf_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f) 
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга json в файле {conf_path}: {e}")
        raise 
    try:
        config = AppConfig(**config_data)
    except ValidationError as e:
        print("Ошибка валидации:")
        for error in e.errors():  
            print(f"  - {error}")
        raise
    return config.sources