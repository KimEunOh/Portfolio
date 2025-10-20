import os
from tavily import TavilyClient

print(os.getenv("TAVILY_API_KEY"))

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
response = tavily_client.search("Who is Leo Messi?")

print(response)
