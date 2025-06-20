import logging
import random
import httpx

from typing import Tuple, TypeVar, Generic, Type, List, Dict, Any, Union, cast
from typing_extensions import get_type_hints
from app.models import GenerationResponse
from app.settings import settings

logger = logging.getLogger(__name__)

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')

class ServiceRouter(Generic[InputT, OutputT]):
    def __init__(self):
        self.services = settings.services
        self.mode = settings.mode
        self.timeout = settings.timeout
        self.fallback_enabled = settings.fallback_enabled
        self._check_config()
        
    def _check_config(self):
        """Проверка корректности конфигурации"""
        if self.mode == "single" and len(self.services) < 1:
            raise ValueError("Для режима 'single' требуется минимум один сервис")
        elif self.mode == "dual" and len(self.services) < 2:
            raise ValueError("Для режима 'dual' требуется минимум два сервиса")
        elif self.mode == "triple" and len(self.services) < 3:
            raise ValueError("Для режима 'triple' требуется минимум два сервиса")
            
        total_weight = sum(service.weight for service in self.services.values())
        if total_weight <= 0:
            raise ValueError("Общий вес сервисов должен быть положительным числом")
    
    def _select_service(self) -> Tuple[str, str]:
        """Выбор сервиса с учетом весов"""
        if self.mode == "single":
            # В режиме одного сервиса берем первый
            service_name = next(iter(self.services.keys()))
            return service_name, self.services[service_name].url
        
        # Выбор сервиса по весовой системе
        weights = [service.weight for service in self.services.values()]
        service_names = list(self.services.keys())
        
        # Случайный выбор с учетом весов
        selected_service = random.choices(service_names, weights=weights, k=1)[0]
        return selected_service, self.services[selected_service].url
    
    def _prepare_request_data(self, data: Any) -> Any:
        """
        Подготовка данных запроса к отправке
        
        Args:
            data: Данные запроса
            
        Returns:
            Подготовленные данные для отправки
        """
        if isinstance(data, list):
            # Если это список, преобразуем каждый элемент
            return [self._prepare_single_item(item) for item in data]
        else:
            # Если одиночный элемент
            return self._prepare_single_item(data)
    
    def _prepare_single_item(self, item: Any) -> Dict[str, Any]:
        """
        Преобразует одиночный элемент в словарь
        
        Args:
            item: Элемент для преобразования
            
        Returns:
            Словарь с данными элемента
        """
        if hasattr(item, 'model_dump'):
            return item.model_dump()
        elif hasattr(item, 'dict'):
            return item.dict()
        else:
            return dict(item)
    
    def _create_output_model(self, output_model: Type[OutputT], data: Dict[str, Any]) -> OutputT:
        """
        Создает экземпляр модели ответа с учетом типа (TypedDict или Pydantic)
        
        Args:
            output_model: Тип модели
            data: Данные для модели
            
        Returns:
            Экземпляр модели с данными
        """

        logger.info(f"Input data: {data}")
        logger.info(f"Input data type: {type(data)}")

        if isinstance(data, dict):
            return output_model(**data)
        elif isinstance(data, list):
            return [output_model(**item) for item in data]
        else:
            raise ValueError(f"Expected dict or list, got {type(data)}")
    
    async def route_request(self, request_data: Union[InputT, List[InputT]], output_model: Type[OutputT]) -> List[OutputT]:
        """
        Универсальная маршрутизация запроса на выбранный сервис
        
        Args:
            request_data: Данные запроса (одиночный элемент или список)
            output_model: Класс модели для ответа
            
        Returns:
            Список ответов от сервиса в формате модели output_model
        """
        service_name, service_url = self._select_service()
        logger.info(f"Выбран сервис: {service_name}")
        
        # Подготовка данных запроса
        prepared_data = self._prepare_request_data(request_data)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    service_url,
                    json=prepared_data,
                )
                response.raise_for_status()
                
                # Преобразуем ответ в модель
                json_response = response.json()

                if isinstance(json_response, dict):
                    # Берём значение по ключу "generations"
                    generations = json_response.get("generations")
                    if isinstance(generations, list):
                        return [GenerationResponse(**item) for item in generations]
                    
                    if isinstance(generations, list):
                        # Если это список — обрабатываем каждый элемент
                        return [self._create_output_model(output_model, item) for item in generations]
                    elif generations is not None:
                        # Если не список, но не None — оборачиваем в список
                        return [self._create_output_model(output_model, generations)]
                    else:
                        raise ValueError("Field 'generations' is missing in the response")

                elif isinstance(json_response, list):
                    # Если уже список — обрабатываем напрямую
                    return [self._create_output_model(output_model, item) for item in json_response]

                # Если ничего не подошло
                raise ValueError(f"Unexpected response format: {json_response}")     
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к сервису {service_name}: {str(e)}")
            
            # Если включен режим резервирования и есть другие сервисы
            if self.fallback_enabled and self.mode == "dual" and len(self.services) > 1:
                fallback_services = {k: v for k, v in self.services.items() if k != service_name}
                
                if fallback_services:
                    fallback_name = next(iter(fallback_services.keys()))
                    fallback_url = fallback_services[fallback_name].url
                    
                    logger.info(f"Используем резервный сервис: {fallback_name}")
                    
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout) as client:
                            response = await client.post(
                                fallback_url,
                                json=prepared_data,
                            )
                            response.raise_for_status()
                            
                            # Преобразуем ответ в модель
                            json_response = response.json()
                            if isinstance(json_response, list):
                                return [self._create_output_model(output_model, item) for item in json_response]
                            return [self._create_output_model(output_model, json_response)]
                    except Exception as fallback_error:
                        logger.error(f"Ошибка при обращении к резервному сервису: {str(fallback_error)}")
            
            # Если все сервисы недоступны, просто выбрасываем исключение
            raise

service_router = ServiceRouter()