"""
API/google_imagen_api.py
──────────────────────────
Обертка для Google Imagen 3 (Nano Banana 2) через RouterAI API.
Поддерживает мультимодальный ввод для консистентности персонажей.

Документация: https://routerai.ru/docs/guides/overview/multimodal/images
"""

from __future__ import annotations

import base64
import os
import time
from typing import Optional, Dict, Any, List
import requests
from PIL import Image
import io


class GoogleImagenAPI:
    """Клиент для Google Imagen 3 через RouterAI."""

    def __init__(self, api_key: str = "", base_url: str = "https://api.routerai.ru"):
        """
        Инициализация клиента.

        Args:
            api_key: API ключ RouterAI
            base_url: URL API RouterAI
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("ROUTERAI_API_KEY", "")
        self._session = requests.Session()
        
        if self.api_key:
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })

    def is_available(self) -> bool:
        """Проверить доступность API."""
        if not self.api_key:
            return False
        try:
            # Простой запрос для проверки
            response = self._session.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "1:1",
        image_number: int = 1,
        seed: int = -1,
        model_name: str = "google/imagen-3",
        character_references: Optional[List[str]] = None,
        scene_references: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[callable] = None,
    ) -> Optional[List[Image.Image]]:
        """
        Генерация изображения через Google Imagen 3 API.

        Args:
            prompt: Основной промпт
            negative_prompt: Негативный промпт (для Imagen 3 используется как guidance)
            aspect_ratio: Соотношение сторон ("1:1", "16:9", "9:16", "4:3", "3:4")
            image_number: Количество изображений
            seed: Seed для воспроизводимости (-1 = случайный)
            model_name: Имя модели (по умолчанию google/imagen-3)
            character_references: Список путей к изображениям персонажей для консистентности
            scene_references: Список словарей с референсами сцены
            progress_callback: Callback для отслеживания прогресса

        Returns:
            Список PIL Image или None при ошибке
        """
        # Формируем мультимодальный запрос
        # Для Imagen 3 через RouterAI используем формат с изображениями-референсами
        
        content_parts = []
        
        # Добавляем текстовый промпт
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f". Avoid: {negative_prompt}"
        
        content_parts.append({"type": "text", "text": full_prompt})
        
        # Добавляем референсы персонажей
        if character_references:
            for ref_path in character_references:
                if os.path.exists(ref_path):
                    img_base64 = self._image_to_base64(ref_path)
                    if img_base64:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                        })
        
        # Добавляем референсы сцены
        if scene_references:
            for ref in scene_references:
                if "path" in ref and os.path.exists(ref["path"]):
                    img_base64 = self._image_to_base64(ref["path"])
                    if img_base64:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                        })
                elif "url" in ref:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": ref["url"]}
                    })

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            "n": image_number,
        }
        
        # Добавляем seed если указан
        if seed != -1:
            payload["seed"] = seed
        
        # Параметры генерации для Imagen 3
        payload["size"] = self._aspect_ratio_to_size(aspect_ratio)
        
        try:
            # Отправляем запрос
            response = self._session.post(
                f"{self.base_url}/v1/images/generations",
                json=payload,
                timeout=300,
            )

            if response.status_code != 200:
                print(f"[IMAGEN] Ошибка: {response.status_code} - {response.text}")
                return None

            result = response.json()

            # Извлекаем изображения из ответа
            images = []
            if "data" in result:
                for img_data in result["data"]:
                    if "url" in img_data:
                        # Загружаем изображение по URL
                        img_response = requests.get(img_data["url"], timeout=30)
                        if img_response.status_code == 200:
                            img = Image.open(io.BytesIO(img_response.content))
                            images.append(img)
                    elif "b64_json" in img_data:
                        img_bytes = base64.b64decode(img_data["b64_json"])
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)

            return images if images else None

        except requests.exceptions.Timeout:
            print("[IMAGEN] Таймаут генерации")
            return None
        except Exception as e:
            print(f"[IMAGEN] Ошибка генерации: {e}")
            return None

    def _image_to_base64(self, image_path: str) -> Optional[str]:
        """Конвертирует изображение в base64."""
        try:
            with open(image_path, "rb") as f:
                img = Image.open(f)
                # Конвертируем в JPEG для уменьшения размера
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            print(f"[IMAGEN] Ошибка конвертации изображения: {e}")
            return None

    def _aspect_ratio_to_size(self, aspect_ratio: str) -> str:
        """Конвертирует соотношение сторон в размер для Imagen 3."""
        mapping = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "4:3": "1408x1024",
            "3:4": "1024x1408",
            "1024*1024": "1024x1024",
            "1792*1024": "1792x1024",
            "1024*1792": "1024x1792",
        }
        return mapping.get(aspect_ratio, "1024x1024")

    def generate_character_consistent(
        self,
        prompt: str,
        character_images: List[str],
        character_names: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        image_number: int = 1,
    ) -> Optional[List[Image.Image]]:
        """
        Генерация с сохранением консистентности персонажей.

        Args:
            prompt: Промпт сцены
            character_images: Пути к изображениям персонажей
            character_names: Имена персонажей для идентификации в промпте
            aspect_ratio: Соотношение сторон
            image_number: Количество изображений

        Returns:
            Список изображений
        """
        # Формируем специальный промпт с указанием персонажей
        if character_names:
            char_refs = ", ".join(character_names)
            enhanced_prompt = f"{prompt}. Characters: {char_refs}"
        else:
            enhanced_prompt = prompt
        
        return self.generate_image(
            prompt=enhanced_prompt,
            character_references=character_images,
            aspect_ratio=aspect_ratio,
            image_number=image_number,
        )

    def generate_multi_character_scene(
        self,
        prompt: str,
        characters: Dict[str, str],  # {name: image_path}
        locations: Optional[Dict[str, str]] = None,  # {name: image_path}
        aspect_ratio: str = "1:1",
        image_number: int = 1,
    ) -> Optional[List[Image.Image]]:
        """
        Генерация сцены с несколькими персонажами и локациями.

        Args:
            prompt: Промпт сцены
            characters: Словарь {имя_персонажа: путь_к_изображению}
            locations: Словарь {название_локации: путь_к_изображению}
            aspect_ratio: Соотношение сторон
            image_number: Количество изображений

        Returns:
            Список изображений
        """
        content_parts = []
        
        # Формируем уточненный промпт с именами
        char_names = list(characters.keys())
        loc_names = list(locations.keys()) if locations else []
        
        entities = []
        if char_names:
            entities.append(f"Characters: {', '.join(char_names)}")
        if loc_names:
            entities.append(f"Location: {', '.join(loc_names)}")
        
        enhanced_prompt = prompt
        if entities:
            enhanced_prompt = f"{prompt}. Scene includes: {'; '.join(entities)}"
        
        content_parts.append({"type": "text", "text": enhanced_prompt})
        
        # Добавляем референсы персонажей
        for name, img_path in characters.items():
            if os.path.exists(img_path):
                img_base64 = self._image_to_base64(img_path)
                if img_base64:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                    })
        
        # Добавляем референсы локаций
        if locations:
            for name, img_path in locations.items():
                if os.path.exists(img_path):
                    img_base64 = self._image_to_base64(img_path)
                    if img_base64:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                        })
        
        payload = {
            "model": "google/imagen-3",
            "messages": [
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            "n": image_number,
            "size": self._aspect_ratio_to_size(aspect_ratio),
        }
        
        try:
            response = self._session.post(
                f"{self.base_url}/v1/images/generations",
                json=payload,
                timeout=300,
            )

            if response.status_code != 200:
                print(f"[IMAGEN] Ошибка: {response.status_code} - {response.text}")
                return None

            result = response.json()
            images = []
            
            if "data" in result:
                for img_data in result["data"]:
                    if "url" in img_data:
                        img_response = requests.get(img_data["url"], timeout=30)
                        if img_response.status_code == 200:
                            img = Image.open(io.BytesIO(img_response.content))
                            images.append(img)
                    elif "b64_json" in img_data:
                        img_bytes = base64.b64decode(img_data["b64_json"])
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)

            return images if images else None

        except requests.exceptions.Timeout:
            print("[IMAGEN] Таймаут генерации")
            return None
        except Exception as e:
            print(f"[IMAGEN] Ошибка генерации: {e}")
            return None
