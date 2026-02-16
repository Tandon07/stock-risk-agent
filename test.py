"""
Advanced AI-Powered Internet Search - Simple Function Version
Uses Groq LLM (via LangChain) for answer generation

Installation:
    pip install langchain-groq beautifulsoup4 requests lxml python-dotenv

Usage:
    from ai_search import search_and_get_answer
    
    answer = search_and_get_answer("What is quantum computing?")
    print(answer)
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangChain and Groq imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("Error: Please install required packages:")
    print("pip install langchain-groq beautifulsoup4 requests lxml python-dotenv")
    exit(1)


# ============================================================================
# DEFAULT CONFIGURATION - Modify these as needed
# ============================================================================

DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Options: llama-3.3-70b-versatile, llama-3.1-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2000
DEFAULT_NUM_RESULTS = 5  # Number of search results to fetch
DEFAULT_NUM_TO_EXTRACT = 3  # Number of pages to extract content from
DEFAULT_MAX_CONTENT_LENGTH = 5000  # Maximum content length per page
DEFAULT_REQUEST_TIMEOUT = 15  # Timeout for web requests in seconds
DEFAULT_RETRY_ATTEMPTS = 3  # Number of retry attempts for failed extractions

SEARCH_ENGINE_URL = 'https://html.duckduckgo.com/html/'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

def _search_web(query, num_results=DEFAULT_NUM_RESULTS):
    """Search the web using DuckDuckGo"""
    results = []
    headers = {'User-Agent': USER_AGENT}
    query = query + "in Indian Stock Market"
    
    try:
        params = {'q': query}
        response = requests.post(
            SEARCH_ENGINE_URL,
            data=params,
            headers=headers,
            timeout=DEFAULT_REQUEST_TIMEOUT
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.find_all('div', class_='result')[:num_results]:
            try:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    url = title_elem.get('href')
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet
                    })
            except:
                continue
    except:
        pass
    
    return results


def _extract_content(url, max_length=DEFAULT_MAX_CONTENT_LENGTH):
    """Extract clean content from a webpage"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else ""
        
        # Extract main content
        main_content = None
        for tag in ['main', 'article', 'div[role="main"]']:
            main_content = soup.find(tag)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body
        
        # Get text
        text = main_content.get_text(separator=' ', strip=True) if main_content else ""
        text = re.sub(r'\s+', ' ', text)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return {
            'url': url,
            'title': title,
            'content': text
        }
    except:
        return None


def _extract_with_retry(url, max_retries=DEFAULT_RETRY_ATTEMPTS):
    """Extract content with retry logic"""
    for attempt in range(max_retries):
        content = _extract_content(url)
        if content:
            return content
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    return None


def _generate_answer_with_llm(query, extracted_contents):
    """Generate answer using Groq LLM"""
    # Get API key from environment
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return "Error: GROQ_API_KEY not found in environment variables. Please add it to your .env file."
    
    # Initialize LLM
    llm = ChatGroq(
        api_key=api_key,
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS
    )
    
    # Prepare context
    context = ""
    for i, content in enumerate(extracted_contents, 1):
        if content:
            context += f"\n\n--- Source {i}: {content['title']} ---\n"
            context += f"URL: {content['url']}\n"
            context += f"Content: {content['content'][:3000]}\n"
    
    # Create messages
    system_message = SystemMessage(content="""You are an expert research assistant for Indian Stock Market that synthesizes information from multiple web sources.
Your task is to provide comprehensive, accurate answers based on the provided sources.

Guidelines:
1. Synthesize information from all sources to provide a comprehensive answer
2. Do not make up information
3. Provide a clear, well-structured answer
4. Be factual and avoid speculation
5. Write in a natural, informative style""")
    
    human_message = HumanMessage(content=f"""Based on the following web search results, please provide a comprehensive answer to the user's question.

User's Question: {query}

Search Results and Extracted Content:
{context}

Please provide your answer now:""")
    
    try:
        messages = [system_message, human_message]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"


# ============================================================================
# MAIN PUBLIC FUNCTION
# ============================================================================

def search_and_get_answer(query):
    """
    Search the web and get an AI-generated answer
    
    Args:
        query (str): The search query/question
    
    Returns:
        str: AI-generated answer based on web search results
    
    Example:
        answer = search_and_get_answer("What is quantum computing?")
        print(answer)
    """
    # Step 1: Search the web
    search_results = _search_web(query, num_results=DEFAULT_NUM_RESULTS)
    
    if not search_results:
        return "No search results found. Please try a different query."
    
    # Step 2: Extract content from top results
    extracted_contents = []
    for result in search_results[:DEFAULT_NUM_TO_EXTRACT]:
        content = _extract_with_retry(result['url'])
        if content:
            extracted_contents.append(content)
        time.sleep(0.5)  # Be polite to servers
    
    if not extracted_contents:
        return "Could not extract content from search results. Please try again."
    
    # Step 3: Generate answer using LLM
    answer = _generate_answer_with_llm(query, extracted_contents)
    
    return answer


# ============================================================================
# OPTIONAL: Function with custom parameters
# ============================================================================

def search_and_get_answer_advanced(
    query, 
    num_results=DEFAULT_NUM_RESULTS,
    num_to_extract=DEFAULT_NUM_TO_EXTRACT,
    model=DEFAULT_MODEL,
    temperature=DEFAULT_TEMPERATURE
):
    """
    Advanced version with customizable parameters
    
    Args:
        query (str): The search query/question
        num_results (int): Number of search results to fetch
        num_to_extract (int): Number of pages to extract content from
        model (str): Groq model to use
        temperature (float): LLM temperature (0.0 to 1.0)
    
    Returns:
        str: AI-generated answer
    """
    # Get API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return "Error: GROQ_API_KEY not found in environment variables."
    
    # Search
    search_results = _search_web(query, num_results=num_results)
    if not search_results:
        return "No search results found."
    
    # Extract
    extracted_contents = []
    for result in search_results[:num_to_extract]:
        content = _extract_with_retry(result['url'])
        if content:
            extracted_contents.append(content)
        time.sleep(0.5)
    
    if not extracted_contents:
        return "Could not extract content from search results."
    
    # Generate answer with custom parameters
    llm = ChatGroq(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=DEFAULT_MAX_TOKENS
    )
    
    context = ""
    for i, content in enumerate(extracted_contents, 1):
        if content:
            context += f"\n\n--- Source {i}: {content['title']} ---\n"
            context += f"URL: {content['url']}\n"
            context += f"Content: {content['content'][:3000]}\n"
    
    system_message = SystemMessage(content="""You are an expert research assistant for Indian Stock Market that synthesizes information from multiple web sources.
Your task is to provide comprehensive, accurate answers based on the provided sources.

Guidelines:
1. Synthesize information from all sources to provide a comprehensive answer
2. Do not make up information
3. Provide a clear, well-structured answer
4. Be factual and avoid speculation
5. Write in a natural, informative style
6. Don't mention sources""")

    human_message = HumanMessage(content=f"""Based on the web search results, answer this question:

Question: {query}

Search Results:
{context}

Provide your answer:""")
    
    try:
        response = llm.invoke([system_message, human_message])
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Simple usage
    # print("Example 1: Simple search")
    # print("=" * 80)
    # answer = search_and_get_answer("What is quantum computing?")
    # print(answer)
    # print("\n" + "=" * 80)
    
    # Advanced usage with custom parameters
    print("\nExample 2: Advanced search with custom parameters")
    print("=" * 80)
    answer = search_and_get_answer_advanced(
        query="which one is better to invest TCS or Infosys considering today's trend?",
        num_results=7,
        num_to_extract=4,
        model="llama-3.3-70b-versatile",
        temperature=0.5
    )
    print(answer)