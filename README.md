## Step 1: Install the dependency

**What to do:** Add the HiveTrace SDK to your project

**Where:** In `requirements.txt` or via pip

```bash
# Via pip (for quick testing)
pip install hivetrace[crewai]>=1.3.3

# Or add to requirements.txt (recommended)
echo "hivetrace[crewai]>=1.3.3" >> requirements.txt
pip install -r requirements.txt
```

**Why:** The HiveTrace SDK provides decorators and clients for sending agent activity data to the monitoring platform.

---

## Step 2: **ADD** unique IDs for each agent

**Example:** In `src/config.py`

```python
PLANNER_ID = "333e4567-e89b-12d3-a456-426614174001"
WRITER_ID = "444e4567-e89b-12d3-a456-426614174002"
EDITOR_ID = "555e4567-e89b-12d3-a456-426614174003"
```

**Why agents need IDs:** HiveTrace tracks each agent individually. A UUID ensures the agent can be uniquely identified in the monitoring system.

---

## Step 3: Create an agent mapping

**What to do:** Map agent roles to their HiveTrace IDs

**Example:** In `src/agents.py` (where your agents are defined)

```python
from crewai import Agent
# ADD: import agent IDs
from src.config import EDITOR_ID, PLANNER_ID, WRITER_ID

# ADD: mapping for HiveTrace (REQUIRED!)
agent_id_mapping = {
    "Content Planner": {  # ← Exactly the same as Agent(role="Content Planner")
        "id": PLANNER_ID,
        "description": "Creates content plans"
    },
    "Content Writer": {   # ← Exactly the same as Agent(role="Content Writer")
        "id": WRITER_ID,
        "description": "Writes high-quality articles"
    },
    "Editor": {           # ← Exactly the same as Agent(role="Editor")
        "id": EDITOR_ID,
        "description": "Edits and improves articles"
    },
}

# Your existing agents (NO CHANGES)
planner = Agent(
    role="Content Planner",  # ← Must match key in agent_id_mapping
    goal="Create a structured content plan for the given topic",
    backstory="You are an experienced analyst...",
    verbose=True,
)

writer = Agent(
    role="Content Writer",   # ← Must match key in agent_id_mapping
    goal="Write an informative and engaging article",
    backstory="You are a talented writer...",
    verbose=True,
)

editor = Agent(
    role="Editor",           # ← Must match key in agent_id_mapping
    goal="Improve the article",
    backstory="You are an experienced editor...",
    verbose=True,
)
```

**Important:** The keys in `agent_id_mapping` must **exactly** match the `role` of your agents. Otherwise, HiveTrace will not be able to associate activity with the correct agent.

---

## Step 4: Integrate with tools (if used)

**What to do:** Add HiveTrace support to tools

**Example:** In `src/tools.py`

```python
from crewai.tools import BaseTool
from typing import Optional

class WordCountTool(BaseTool):
    name: str = "WordCountTool"
    description: str = "Count words, characters and sentences in text"
    # ADD: HiveTrace field (REQUIRED!)
    agent_id: Optional[str] = None
    
    def _run(self, text: str) -> str:
        word_count = len(text.split())
        return f"Word count: {word_count}"
```

**Example:** In `src/agents.py`

```python
from src.tools import WordCountTool
from src.config import PLANNER_ID, WRITER_ID, EDITOR_ID

# ADD: create tools for each agent
planner_tools = [WordCountTool()]
writer_tools = [WordCountTool()]
editor_tools = [WordCountTool()]

# ADD: assign tools to agents
for tool in planner_tools:
    tool.agent_id = PLANNER_ID

for tool in writer_tools:
    tool.agent_id = WRITER_ID

for tool in editor_tools:
    tool.agent_id = EDITOR_ID

# Use tools in agents
planner = Agent(
    role="Content Planner",
    tools=planner_tools,  # ← Agent-specific tools
    # ... other parameters
)
```

**Why:** HiveTrace tracks tool usage. The `agent_id` field in the tool class and its assignment let HiveTrace know which agent used which tool.

---

## Step 5: Initialize HiveTrace in FastAPI (if used)

**What to do:** Add the HiveTrace client to the application lifecycle

**Example:** In `main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
# ADD: import HiveTrace SDK
from hivetrace import SyncHivetraceSDK
from src.config import HIVETRACE_ACCESS_TOKEN, HIVETRACE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ADD: initialize HiveTrace client
    hivetrace = SyncHivetraceSDK(
        config={
            "HIVETRACE_URL": HIVETRACE_URL,
            "HIVETRACE_ACCESS_TOKEN": HIVETRACE_ACCESS_TOKEN,
        }
    )
    # Store client in app state
    app.state.hivetrace = hivetrace
    try:
        yield
    finally:
        # IMPORTANT: close connection on shutdown
        hivetrace.close()

app = FastAPI(lifespan=lifespan)
```

---

## Step 6: Integrate into business logic

**What to do:** Wrap Crew creation with the HiveTrace decorator

**Example:** In `src/services/topic_service.py`

```python
import uuid
from typing import Optional
from crewai import Crew
# ADD: HiveTrace imports
from hivetrace import SyncHivetraceSDK
from hivetrace import crewai_trace as trace

from src.agents import agent_id_mapping, planner, writer, editor
from src.tasks import plan_task, write_task, edit_task
from src.config import HIVETRACE_APP_ID

def process_topic(
    topic: str,
    hivetrace: SyncHivetraceSDK,  # ← ADD parameter
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    # ADD: generate unique conversation ID
    agent_conversation_id = str(uuid.uuid4())
    
    # ADD: common trace parameters
    common_params = {
        "agent_conversation_id": agent_conversation_id,
        "user_id": user_id,
        "session_id": session_id,
    }

    # ADD: log user request
    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on topic: {topic}",
        additional_parameters={
            **common_params,
            "agents": agent_id_mapping,  # ← pass agent mapping
        },
    )

    # ADD: @trace decorator for monitoring Crew
    @trace(
        hivetrace=hivetrace,
        application_id=HIVETRACE_APP_ID,
        agent_id_mapping=agent_id_mapping,  # ← REQUIRED!
    )
    def create_crew():
        return Crew(
            agents=[planner, writer, editor],
            tasks=[plan_task, write_task, edit_task],
            verbose=True,
        )

    # Execute with monitoring
    crew = create_crew()
    result = crew.kickoff(
        inputs={"topic": topic},
        **common_params  # ← pass common parameters
    )

    return {
        "result": result.raw,
        "execution_details": {**common_params, "status": "completed"},
    }
```

**How it works:**

1. **`agent_conversation_id`** — unique ID for grouping all actions under a single request
2. **`hivetrace.input()`** — sends the user’s request to HiveTrace for inspection
3. **`@trace`**:

   * Intercepts all agent actions inside the Crew
   * Sends data about each step to HiveTrace
   * Associates actions with specific agents via `agent_id_mapping`
4. **`**common_params`** — passes metadata into `crew.kickoff()` so all events are linked

**Critical:** The `@trace` decorator must be applied to the function that creates and returns the `Crew`, **not** the function that calls `kickoff()`.

---

## Step 7: Update FastAPI endpoints (if used)

**What to do:** Pass the HiveTrace client to the business logic

**Example:** In `src/routers/topic_router.py`

```python
from fastapi import APIRouter, Body, Request
# ADD: import HiveTrace type
from hivetrace import SyncHivetraceSDK

from src.services.topic_service import process_topic
from src.config import SESSION_ID, USER_ID

router = APIRouter(prefix="/api")

@router.post("/process-topic")
async def api_process_topic(request: Request, request_body: dict = Body(...)):
    # ADD: get HiveTrace client from app state
    hivetrace: SyncHivetraceSDK = request.app.state.hivetrace
    
    return process_topic(
        topic=request_body["topic"],
        hivetrace=hivetrace,  # ← pass client
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
```

**Why:** The API endpoint must pass the HiveTrace client to the business logic so monitoring data can be sent.

---

## 🚨 Common mistakes

1. **Role mismatch** — make sure keys in `agent_id_mapping` exactly match `role` in agents
2. **Missing `agent_id_mapping`** — the `@trace` decorator must receive the mapping
3. **Decorator on wrong function** — `@trace` must be applied to the Crew creation function, not `kickoff`
4. **Client not closed** — remember to call `hivetrace.close()` in the lifespan
5. **Invalid credentials** — check your HiveTrace environment variables
