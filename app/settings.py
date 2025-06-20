import logging
from dataclasses import dataclass
from typing import Dict

from omegaconf import OmegaConf

from app.constants import CONFIG_PATH, DEFAULT_MODE, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    url: str
    weight: float = 1.0

@dataclass
class ABTestingConfig:
    mode: str = DEFAULT_MODE
    services: Dict[str, ServiceConfig] = None
    timeout: int = DEFAULT_TIMEOUT
    fallback_enabled: bool = True

    def __post_init__(self):
        # Создаем пустой словарь, если не был передан
        if self.services is None:
            self.services = {}

def load_config() -> ABTestingConfig:
    """Загрузка конфигурации из YAML файла"""
    try:
        # Проверяем существование файла
        if not CONFIG_PATH.exists():
            logger.warning(f"Файл конфигурации не найден: {CONFIG_PATH}. Используются значения по умолчанию.")
            return ABTestingConfig()
        
        # Загружаем конфигурацию из YAML
        cfg = OmegaConf.load(CONFIG_PATH)
        
        # Создаем словарь сервисов
        services_dict = {}
        if "services" in cfg:
            for service_name, service_cfg in cfg.services.items():
                services_dict[service_name] = ServiceConfig(
                    url=service_cfg.get("url"),
                    weight=service_cfg.get("weight", 1.0)
                )
        
        # Создаем и возвращаем конфигурацию
        return ABTestingConfig(
            mode=cfg.get("mode", DEFAULT_MODE),
            services=services_dict,
            timeout=cfg.get("timeout", DEFAULT_TIMEOUT),
            fallback_enabled=cfg.get("fallback_enabled", True)
        )
    
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {str(e)}. Используются значения по умолчанию.")
        return ABTestingConfig()

# Загрузка конфигурации при импорте модуля
settings = load_config()