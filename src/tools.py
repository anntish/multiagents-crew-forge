import time
from datetime import datetime

from crewai.tools import BaseTool
from openai import OpenAI

from src.config import OPENAI_API_KEY


class WebSearchTool(BaseTool):
    name: str = "WebSearchTool"
    description: str = "Search the web for information. Input should be a string query."
    last_request_time: datetime = None
    min_delay: int = 2
    agent_id: str = None

    def _run(self, query: str) -> str:
        try:
            if self.last_request_time:
                time_since_last = (
                    datetime.now() - self.last_request_time
                ).total_seconds()
                if time_since_last < self.min_delay:
                    time.sleep(self.min_delay - time_since_last)

            client = OpenAI(api_key=OPENAI_API_KEY)

            completion = client.chat.completions.create(
                model="gpt-4o-search-preview",
                web_search_options={
                    "search_context_size": "medium",
                    "user_location": {
                        "type": "approximate",
                        "approximate": {
                            "country": "GB",
                            "city": "London",
                            "region": "London",
                        },
                    },
                },
                messages=[{"role": "user", "content": query}],
            )

            result = completion.choices[0].message.content

            if hasattr(completion.choices[0].message, "annotations"):
                sources = []
                for annotation in completion.choices[0].message.annotations:
                    if annotation.type == "url_citation":
                        sources.append(
                            f"Source: {annotation.url_citation.title} ({annotation.url_citation.url})"
                        )
                if sources:
                    result += "\n\n" + "\n".join(sources)

            self.last_request_time = datetime.now()
            return result

        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            return error_msg
