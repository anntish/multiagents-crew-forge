## Шаг 1: Установка зависимости

**Что делаем:** Добавляем HiveTrace SDK в проект

**Куда:** В `requirements.txt` или через pip

```bash
# Через pip (для быстрого тестирования)
pip install hivetrace[crewai]>=1.3.3

# Или добавляем в requirements.txt (рекомендуется)
echo "hivetrace[crewai]>=1.3.3" >> requirements.txt
pip install -r requirements.txt
```

**Зачем:** HiveTrace SDK предоставляет декораторы и клиенты для отправки данных о работе агентов на платформу мониторинга.


## Шаг 2: ДОБАВЛЯЕМ: Уникальные ID для каждого агента

**Пример:** В файле `src/config.py` 

```
PLANNER_ID = "333e4567-e89b-12d3-a456-426614174001"
WRITER_ID = "444e4567-e89b-12d3-a456-426614174002" 
EDITOR_ID = "555e4567-e89b-12d3-a456-426614174003"
```

**Зачем ID агентов:** HiveTrace отслеживает каждого агента отдельно. UUID позволяет однозначно идентифицировать агента в системе мониторинга.


## Шаг 3: Создание маппинга агентов

**Что делаем:** Связываем роли агентов с их ID для HiveTrace

**Пример:** В файле `src/agents.py` (где определены ваши агенты)

```python
from crewai import Agent
# ДОБАВЛЯЕМ: импорт ID агентов
from src.config import EDITOR_ID, PLANNER_ID, WRITER_ID

# ДОБАВЛЯЕМ: маппинг для HiveTrace (ОБЯЗАТЕЛЬНО!)
agent_id_mapping = {
    "Content Planner": {  # ← Точно такая же роль как в Agent(role="Content Planner")
        "id": PLANNER_ID, 
        "description": "Creates content plans"
    },
    "Content Writer": {   # ← Точно такая же роль как в Agent(role="Content Writer") 
        "id": WRITER_ID,
        "description": "Writes high-quality articles"
    },
    "Editor": {          # ← Точно такая же роль как в Agent(role="Editor")
        "id": EDITOR_ID,
        "description": "Edits and improves articles"  
    },
}

# Ваши существующие агенты (БЕЗ ИЗМЕНЕНИЙ)
planner = Agent(
    role="Content Planner",  # ← Роль должна совпадать с ключом в agent_id_mapping
    goal="Create a structured content plan for the given topic",
    backstory="You are an experienced analyst...",
    verbose=True,
)

writer = Agent(
    role="Content Writer",   # ← Роль должна совпадать с ключом в agent_id_mapping
    goal="Write an informative and engaging article",
    backstory="You are a talented writer...",
    verbose=True,
)

editor = Agent(
    role="Editor",          # ← Роль должна совпадать с ключом в agent_id_mapping
    goal="Improve the article",
    backstory="You are an experienced editor...",
    verbose=True,
)
```

**ВАЖНО:** Ключи в `agent_id_mapping` должны ТОЧНО совпадать с `role` в ваших агентах. Иначе HiveTrace не сможет связать активность с конкретным агентом.



## Шаг 4: Инициализация HiveTrace в FastAPI (если используете)

**Что делаем:** Добавляем HiveTrace клиент в жизненный цикл приложения

**Пример:** В файле `main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
# ДОБАВЛЯЕМ: импорт HiveTrace SDK
from hivetrace import SyncHivetraceSDK
from src.config import HIVETRACE_ACCESS_TOKEN, HIVETRACE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ДОБАВЛЯЕМ: инициализация HiveTrace клиента
    hivetrace = SyncHivetraceSDK(
        config={
            "HIVETRACE_URL": HIVETRACE_URL,
            "HIVETRACE_ACCESS_TOKEN": HIVETRACE_ACCESS_TOKEN,
        }
    )
    # Сохраняем клиент в состоянии приложения
    app.state.hivetrace = hivetrace
    try:
        yield
    finally:
        # ВАЖНО: закрываем соединение при завершении
        hivetrace.close()

app = FastAPI(lifespan=lifespan)
```


## Шаг 5: Интеграция в бизнес-логику

**Что делаем:** Оборачиваем создание Crew декоратором HiveTrace

**Пример:** В файле с бизнес-логикой (`src/services/topic_service.py`)

```python
import uuid
from typing import Optional
from crewai import Crew
# ДОБАВЛЯЕМ: импорты HiveTrace
from hivetrace import SyncHivetraceSDK
from hivetrace import crewai_trace as trace

from src.agents import agent_id_mapping, planner, writer, editor
from src.tasks import plan_task, write_task, edit_task
from src.config import HIVETRACE_APP_ID

def process_topic(
    topic: str,
    hivetrace: SyncHivetraceSDK,  # ← ДОБАВЛЯЕМ параметр
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    # ДОБАВЛЯЕМ: генерируем уникальный ID беседы агентов
    agent_conversation_id = str(uuid.uuid4())
    
    # ДОБАВЛЯЕМ: общие параметры для трейсинга
    common_params = {
        "agent_conversation_id": agent_conversation_id,
        "user_id": user_id,
        "session_id": session_id,
    }

    # ДОБАВЛЯЕМ: логируем пользовательский запрос
    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on topic: {topic}",
        additional_parameters={
            **common_params,
            "agents": agent_id_mapping,  # ← передаем маппинг агентов
        },
    )

    # ДОБАВЛЯЕМ: декоратор @trace для мониторинга Crew
    @trace(
        hivetrace=hivetrace,
        application_id=HIVETRACE_APP_ID,
        agent_id_mapping=agent_id_mapping,  # ← ОБЯЗАТЕЛЬНО!
    )
    def create_crew():
        return Crew(
            agents=[planner, writer, editor], 
            tasks=[plan_task, write_task, edit_task],
            verbose=True,
        )

    # Выполняем с мониторингом
    crew = create_crew()
    result = crew.kickoff(
        inputs={"topic": topic}, 
        **common_params  # ← ДОБАВЛЯЕМ общие параметры
    )

    return {
        "result": result.raw,
        "execution_details": {**common_params, "status": "completed"},
    }
```

**Что происходит:**

1. **`agent_conversation_id`** - уникальный ID для группировки всех действий в рамках одного запроса
2. **`hivetrace.input()`** - отправляет в HiveTrace на проверку запрос пользователя
3. **`@trace`**:
   - Перехватывает все действия агентов внутри Crew
   - Отправляет данные о каждом шаге в HiveTrace
   - Связывает действия с конкретными агентами через `agent_id_mapping`
4. **`**common_params`** - передает метаданные в `crew.kickoff()` для связывания всех событий

**КРИТИЧЕСКИ ВАЖНО:** Декоратор `@trace` должен быть применен к функции, которая создает и возвращает `Crew`. НЕ к функции, которая вызывает `kickoff()`!

## Шаг 6: Обновление API эндпоинтов FastAPI (если используете)

**Что делаем:** Передаем HiveTrace клиент в бизнес-логику

**Пример:** В файле (`src/routers/topic_router.py`)

```python
from fastapi import APIRouter, Body, Request
# ДОБАВЛЯЕМ: импорт типа HiveTrace
from hivetrace import SyncHivetraceSDK

from src.services.topic_service import process_topic
from src.config import SESSION_ID, USER_ID

router = APIRouter(prefix="/api")

@router.post("/process-topic")
async def api_process_topic(request: Request, request_body: dict = Body(...)):
    # ДОБАВЛЯЕМ: получаем HiveTrace клиент из состояния приложения
    hivetrace: SyncHivetraceSDK = request.app.state.hivetrace
    
    return process_topic(
        topic=request_body["topic"],
        hivetrace=hivetrace,  # ← ДОБАВЛЯЕМ передачу клиента
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
```

**Зачем:** API эндпоинт должен передать HiveTrace клиент в бизнес-логику для отправки данных мониторинга.

## Шаг 7: Интеграция с инструментами (если используете)

**Что делаем:** Добавляем поддержку HiveTrace в инструменты

**Пример:** В файле с инструментами (`src/tools.py`)

```python
from crewai.tools import BaseTool
from typing import Optional

class WordCountTool(BaseTool):
    name: str = "WordCountTool"
    description: str = "Count words, characters and sentences in text"
    # ДОБАВЛЯЕМ: поле для HiveTrace (ОБЯЗАТЕЛЬНО!)
    agent_id: Optional[str] = None
    
    def _run(self, text: str) -> str:
        word_count = len(text.split())
        return f"Word count: {word_count}"
```

**Пример:** В файле с агентами (`src/agents.py`)

```python
from src.tools import WordCountTool
from src.config import PLANNER_ID, WRITER_ID, EDITOR_ID

# ДОБАВЛЯЕМ: создаем инструменты для каждого агента
planner_tools = [WordCountTool()]
writer_tools = [WordCountTool()]
editor_tools = [WordCountTool()]

# ДОБАВЛЯЕМ: привязываем инструменты к агентам
for tool in planner_tools:
    tool.agent_id = PLANNER_ID

for tool in writer_tools:
    tool.agent_id = WRITER_ID

for tool in editor_tools:
    tool.agent_id = EDITOR_ID

# Используем инструменты в агентах
planner = Agent(
    role="Content Planner",
    tools=planner_tools,  # ← Привязанные к агенту инструменты
    # ... остальные параметры
)
```

**Зачем:** HiveTrace отслеживает использование инструментов. Поле `agent_id` в классе инструмента и его установка позволяет понять, какой агент использовал какой инструмент.

## 🚨 Частые ошибки

1. **Роли не совпадают** - убедитесь что ключи в `agent_id_mapping` точно совпадают с `role` в агентах
2. **Не передан agent_id_mapping** - декоратор `@trace` должен получить маппинг агентов
3. **Декоратор на неправильной функции** - `@trace` должен быть на функции создания Crew, не на kickoff
4. **Не закрыт клиент** - не забудьте `hivetrace.close()` в lifespan
5. **Неправильные credentials** - проверьте переменные окружения HiveTrace

