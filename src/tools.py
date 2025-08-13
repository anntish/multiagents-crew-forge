from typing import Optional

from crewai.tools import BaseTool


class WordCountTool(BaseTool):
    name: str = "WordCountTool"
    description: str = "Count words, characters and sentences in text. Input should be the text to analyze."
    agent_id: Optional[str] = None

    def _run(self, text: str) -> str:
        if not text.strip():
            return "Empty text"

        words = len(text.split())
        characters = len(text)
        characters_no_spaces = len(text.replace(" ", ""))
        sentences = len(
            [
                s
                for s in text.replace("!", ".").replace("?", ".").split(".")
                if s.strip()
            ]
        )

        return f"Words: {words}\nSymbols: {characters}\nSymbols without spaces: {characters_no_spaces}\nSentences: {sentences}"
