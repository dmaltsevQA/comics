"""
API/fooocus_api.py
──────────────────
Обертка для Fooocus API для генерации изображений.

Fooocus API обычно доступен по адресу http://localhost:7865
Документация: https://github.com/lllyasviel/Fooocus/blob/main/api.md
"""

from __future__ import annotations

import base64
import os
import time
from typing import Optional, Dict, Any, List
import requests
from PIL import Image
import io


class FooocusAPI:
    """Клиент для Fooocus API."""

    def __init__(self, base_url: str = "http://localhost:7865"):
        """
        Инициализация клиента.

        Args:
            base_url: URL Fooocus API
        """
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def is_available(self) -> bool:
        """Проверить доступность API."""
        try:
            response = self._session.get(f"{self.base_url}/ping", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Получить статус очереди."""
        try:
            response = self._session.get(f"{self.base_url}/queue", timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "Fooocus V2",
        aspect_ratio: str = "1024*1024",
        image_number: int = 1,
        seed: int = -1,
        guidance_scale: float = 4.0,
        steps: int = 30,
        model_name: str = "",
        lora_name: str = "",
        lora_weight: float = 1.0,
        progress_callback: Optional[callable] = None,
    ) -> Optional[List[Image.Image]]:
        """
        Генерация изображения через Fooocus API.

        Args:
            prompt: Основной промпт
            negative_prompt: Негативный промпт
            style: Стиль Fooocus (например "Fooocus V2", "Fooocus Enhance")
            aspect_ratio: Соотношение сторон (например "1024*1024")
            image_number: Количество изображений
            seed: Seed для воспроизводимости (-1 = случайный)
            guidance_scale: CFG scale
            steps: Количество шагов
            model_name: Имя checkpoint модели
            lora_name: Имя LoRA модели
            lora_weight: Вес LoRA (0.0 - 2.0)
            progress_callback: Callback для отслеживания прогресса

        Returns:
            Список PIL Image или None при ошибке
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "image_number": image_number,
            "seed": seed,
            "guidance_scale": guidance_scale,
            "steps": steps,
        }

        # Добавляем модель если указана
        if model_name and model_name != "default":
            payload["base_model_name"] = model_name

        # Добавляем LoRA если указана
        if lora_name and lora_weight != 0:
            payload["lora_name"] = lora_name
            payload["lora_weight"] = lora_weight

        try:
            # Отправляем запрос на генерацию
            response = self._session.post(
                f"{self.base_url}/v2/generation/image-simple",
                json=payload,
                timeout=300,
            )

            if response.status_code != 200:
                print(f"[FOOOCUS] Ошибка: {response.status_code} - {response.text}")
                return None

            result = response.json()

            # Извлекаем изображения из ответа
            images = []
            if "improvements" in result:
                for img_data in result["improvements"]:
                    if "base64" in img_data:
                        img_bytes = base64.b64decode(img_data["base64"])
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)

            return images if images else None

        except requests.exceptions.Timeout:
            print("[FOOOCUS] Таймаут генерации")
            return None
        except Exception as e:
            print(f"[FOOOCUS] Ошибка генерации: {e}")
            return None

    def generate_image_async(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "general",
        aspect_ratio: str = "1024*1024",
        image_number: int = 1,
        seed: int = -1,
        guidance_scale: float = 4.0,
        steps: int = 30,
    ) -> Optional[str]:
        """
        Асинхронная генерация изображения (возвращает task_id).

        Returns:
            task_id или None при ошибке
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "image_number": image_number,
            "seed": seed,
            "guidance_scale": guidance_scale,
            "steps": steps,
        }

        try:
            response = self._session.post(
                f"{self.base_url}/v2/generation/image",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("task_id")
            return None

        except Exception as e:
            print(f"[FOOOCUS] Ошибка асинхронной генерации: {e}")
            return None

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получить статус задачи."""
        try:
            response = self._session.get(
                f"{self.base_url}/v2/generation/query-job?task_id={task_id}",
                timeout=10,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_task_result(self, task_id: str) -> Optional[List[Image.Image]]:
        """Получить результат задачи."""
        try:
            response = self._session.get(
                f"{self.base_url}/v2/generation/query-job?task_id={task_id}&require_base64=true",
                timeout=10,
            )
            result = response.json()

            if result.get("status") == "SUCCESS":
                images = []
                for img_data in result.get("results", []):
                    if "base64" in img_data:
                        img_bytes = base64.b64decode(img_data["base64"])
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)
                return images
            return None

        except Exception as e:
            print(f"[FOOOCUS] Ошибка получения результата: {e}")
            return None

    def wait_for_task(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: float = 2.0,
        progress_callback: Optional[callable] = None,
    ) -> Optional[List[Image.Image]]:
        """
        Ожидание завершения задачи.

        Args:
            task_id: ID задачи
            timeout: Максимальное время ожидания (сек)
            poll_interval: Интервал опроса (сек)
            progress_callback: Callback для прогресса

        Returns:
            Список изображений или None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)

            if status.get("status") == "SUCCESS":
                return self.get_task_result(task_id)
            elif status.get("status") in ("FAILED", "ERROR"):
                print(f"[FOOOCUS] Задача {task_id} завершилась ошибкой")
                return None

            if progress_callback:
                progress_callback(status)

            time.sleep(poll_interval)

        print(f"[FOOOCUS] Таймаут ожидания задачи {task_id}")
        return None

    def get_styles(self) -> List[str]:
        """Получить доступные стили Fooocus."""
        try:
            response = self._session.get(f"{self.base_url}/v2/generation/styles", timeout=10)
            return response.json().get("styles", [])
        except Exception:
            return ["Fooocus V2", "Fooocus Enhance", "Fooocus Sharp", "Fooocus Masterpiece"]

    def get_models(self) -> List[str]:
        """Получить доступные модели (checkpoints)."""
        try:
            response = self._session.get(f"{self.base_url}/v2/generation/checkpoints", timeout=10)
            return response.json().get("checkpoints", [])
        except Exception:
            return []

    def get_loras(self) -> List[str]:
        """Получить доступные LoRA."""
        try:
            response = self._session.get(f"{self.base_url}/v2/generation/loras", timeout=10)
            return response.json().get("loras", [])
        except Exception:
            return []

    def upscale_image(
        self,
        image: Image.Image,
        upscale_factor: float = 2.0,
    ) -> Optional[Image.Image]:
        """
        Апскейл изображения через Fooocus API.

        Args:
            image: PIL Image для апскейла
            upscale_factor: Коэффициент увеличения

        Returns:
            Увеличенное изображение или None
        """
        # Конвертируем в base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "input_image": img_base64,
            "upscale_factor": upscale_factor,
        }

        try:
            response = self._session.post(
                f"{self.base_url}/v2/upscale",
                json=payload,
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                if "base64" in result:
                    img_bytes = base64.b64decode(result["base64"])
                    return Image.open(io.BytesIO(img_bytes))
            return None

        except Exception as e:
            print(f"[FOOOCUS] Ошибка апскейла: {e}")
            return None