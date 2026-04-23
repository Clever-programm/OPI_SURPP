import asyncio
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

# Мокаем зависимости, чтобы не импортировать всё приложение
import sys
from types import ModuleType

# Создаем фейковые модули для импортов
m = ModuleType("app.models.order")
sys.modules["app.models.order"] = m
m.Order = MagicMock

m = ModuleType("app.models.order_item")
sys.modules["app.models.order_item"] = m
m.OrderItem = MagicMock

# ... и так далее, но это слишком сложно.
# Проще будет просто запустить тест через docker, когда он поднимется.
