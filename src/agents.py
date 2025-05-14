from crewai import Agent

from src.config import EDITOR_ID, PLANNER_ID, WRITER_ID
from src.tools import WebSearchTool

planner_tools = [WebSearchTool()]
writer_tools = [WebSearchTool()]
editor_tools = [WebSearchTool()]

for tool in planner_tools:
    tool.agent_id = PLANNER_ID

for tool in writer_tools:
    tool.agent_id = WRITER_ID

for tool in editor_tools:
    tool.agent_id = EDITOR_ID

agent_id_mapping = {
    "Content Planner": {"id": PLANNER_ID, "description": "Creates content plans"},
    "Content Writer": {"id": WRITER_ID, "description": "Writes high-quality articles"},
    "Editor": {"id": EDITOR_ID, "description": "Edits and improves articles"},
}

planner = Agent(
    role="Content Planner",
    goal="Create a structured content plan for the given topic",
    backstory="You are an experienced analyst and researcher. Your task is to collect and structure information on a given topic, "
    "using various sources and evaluation criteria. You must create a clear plan that will help the writer create "
    "an informative and interesting article. You can analyze any topic and find key aspects in it.",
    allow_delegation=False,
    verbose=True,
    tools=planner_tools,
)

writer = Agent(
    role="Content Writer",
    goal="Write an informative and engaging article on the given topic",
    backstory="You are a talented writer capable of creating interesting articles on any topic. Your task is to write an article "
    "based on the plan created by Content Planner that will be interesting to readers and provide them with valuable information. "
    "You can adapt your style to any topic and structure information logically and engagingly.",
    allow_delegation=False,
    verbose=True,
    tools=writer_tools,
)

editor = Agent(
    role="Editor",
    goal="Improve the article by making it more structured and readable",
    backstory="You are an experienced editor with broad knowledge. Your task is to check the article for "
    "factual accuracy, improve structure and writing style, ensure that information is presented "
    "logically and consistently. You can work with texts on any topic.",
    allow_delegation=False,
    verbose=True,
    tools=editor_tools,
)
