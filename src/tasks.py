from crewai import Task

from src.agents import editor, planner, writer

plan = Task(
    description=(
        "1. Make one comprehensive search on the topic {topic}:\n"
        "   - Use WebSearchTool to get an overview\n"
        "   - Collect main facts, trends and key aspects\n"
        "2. Based on the collected information:\n"
        "   - Determine 3-4 key aspects for analysis\n"
        "   - Prepare 2-3 specific questions for each aspect\n"
        "3. Make focused searches only on the most important questions\n"
        "4. Create the article structure:\n"
        "   - Introduction with the definition of the topic\n"
        "   - Sections on each key aspect\n"
        "   - Conclusion with main conclusions"
    ),
    expected_output="Structured article plan with detailed information on each aspect of the topic.",
    agent=planner,
)

write = Task(
    description=(
        "1. Use the Content Planner plan to create an article.\n"
        "2. For each aspect:\n"
        "   - Use already collected information\n"
        "   - Make additional searches only if:\n"
        "     * Not enough specific examples\n"
        "     * Need actual data\n"
        "     * Need to clarify facts\n"
        "3. Structure the article:\n"
        "   - Start with an overview of the topic\n"
        "   - Consider each aspect sequentially\n"
        "   - Finish with general conclusions\n"
        "4. Use attractive headings and subheadings"
    ),
    expected_output="Full article in markdown format with well-structured information on the topic.",
    agent=writer,
)

edit = Task(
    description=(
        "1. Check the article for:\n"
        "   - Factual accuracy\n"
        "   - Logical structure\n"
        "   - Style and readability\n"
        "2. Make sure that:\n"
        "   - Information is presented sequentially\n"
        "   - Headings are informative\n"
        "   - Text is easy to read\n"
        "   - Conclusions are logical and justified\n"
        "3. If gaps in information are found:\n"
        "   - Make only one additional search\n"
        "   - Focus on the most important omission\n"
        "4. Make necessary corrections to improve the quality"
    ),
    expected_output="Edited article, ready for publication.",
    agent=editor,
)
