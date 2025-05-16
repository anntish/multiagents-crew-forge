from hivetrace import HivetraceSDK

from src.config import HIVETRACE_ACCESS_TOKEN, HIVETRACE_URL

try:
    hivetrace = HivetraceSDK(
        config={
            "HIVETRACE_URL": HIVETRACE_URL,
            "HIVETRACE_ACCESS_TOKEN": HIVETRACE_ACCESS_TOKEN,
        },
        async_mode=False,
    )
except Exception as e:
    print(f"Error initializing HivetraceSDK: {str(e)}")
    hivetrace = None
