from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()

def web_search(query: str, max_results: int = 5) -> str:
    # DuckDuckGoSearchRun returns a text blob of results
    return search.run(query)
print(web_search("How to open Dmat account?"))