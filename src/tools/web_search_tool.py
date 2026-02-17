"""
Advanced AI-Powered Internet Search - Optimized for Indian Market
Uses Groq LLM (via LangChain) for answer generation

Installation:
    pip install langchain-groq beautifulsoup4 requests lxml python-dotenv ddgs

Usage:
    from ai_search import search_and_get_answer
    
    answer = search_and_get_answer("gold price today")
    print(answer)
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage
    from ddgs import DDGS
except ImportError:
    print("Error: Please install required packages:")
    print("pip install langchain-groq beautifulsoup4 requests lxml python-dotenv ddgs")
    exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.1  # Lower for more consistent answers
DEFAULT_MAX_TOKENS = 2000
DEFAULT_NUM_RESULTS = 15  # More results for better coverage
DEFAULT_NUM_TO_EXTRACT = 5  # Extract from more sources
DEFAULT_MAX_CONTENT_LENGTH = 5000
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_RETRY_ATTEMPTS = 2

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Priority sources for Indian market - organized by category
PRIORITY_SOURCES = [
    # Commodities & Precious Metals
    'goldpriceindia.com',
    'goldrate.in',
    'goodreturns.in',
    'mcxindia.com',              # Multi Commodity Exchange (coal, metals, energy)
    'in.investing.com',          # All commodities
    
    # Energy & Industrial Commodities
    'tradingeconomics.com',      # Coal, oil, gas prices
    'coal.nic.in',               # Ministry of Coal (official)
    'coalindia.in',              # Coal India Ltd
    
    # Stock Market
    'moneycontrol.com',
    'economictimes.indiatimes.com',
    'livemint.com',
    'business-standard.com',
    
    # Stock Exchanges
    'nseindia.com',
    'bseindia.com',
    
    # DMAT & Brokers
    'zerodha.com',
    'groww.in',
    'upstox.com',
    'angelone.in',
    'icicidirect.com',
    'hdfcsec.com',
    
    # Portfolio & Analysis
    'valueresearchonline.com',
    'tickertape.in',
    'marketsmojo.com',
    'screener.in',
    
    # Education & Guides
    'cleartax.in',
    'etmoney.com',
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _search_web(query, num_results=DEFAULT_NUM_RESULTS):
    """Search with smart source prioritization based on query type"""
    results = []
    seen_urls = set()
    
    try:
        ddgs = DDGS()
        print(f"🔍 Searching for: {query}")
        
        query_lower = query.lower()

        # --- Strict query type detection (order matters: most specific first) ---

        # Precious metals: must mention the metal explicitly
        is_precious_metal = any(w in query_lower for w in ['gold', 'silver', 'platinum', 'palladium'])

        # Energy: must mention energy commodity explicitly
        is_energy = any(w in query_lower for w in ['coal', 'crude oil', 'crude', 'petroleum', 'natural gas', 'lng', 'lpg'])

        # Industrial metals: must mention metal explicitly
        is_industrial = any(w in query_lower for w in ['copper', 'zinc', 'aluminium', 'aluminum', 'nickel', 'steel', 'iron ore'])

        # DMAT/broker
        is_dmat = any(w in query_lower for w in ['dmat', 'demat', 'account', 'broker', 'transfer', 'depository'])

        # Stocks/equity
        is_stock = any(w in query_lower for w in ['stock', 'share', 'nifty', 'sensex', 'equity', 'ipo', 'nse', 'bse'])

        # Mutual funds/SIP
        is_mf = any(w in query_lower for w in ['mutual fund', 'sip', 'nav', 'amc', 'elss'])

        # General market/sector queries - no specific commodity
        is_general_market = any(w in query_lower for w in ['sector', 'market', 'economy', 'trend', 'booming', 'bull', 'bear', 'rally', 'crash'])

        # Build source priority based on detected type
        sources = PRIORITY_SOURCES.copy()

        if is_precious_metal:
            priority = ['goldpriceindia.com', 'goldrate.in', 'goodreturns.in', 'mcxindia.com', 'in.investing.com']
        elif is_energy:
            priority = ['tradingeconomics.com', 'mcxindia.com', 'in.investing.com', 'coal.nic.in', 'coalindia.in', 'economictimes.indiatimes.com']
        elif is_industrial:
            priority = ['mcxindia.com', 'in.investing.com', 'tradingeconomics.com', 'moneycontrol.com']
        elif is_dmat:
            priority = ['zerodha.com', 'groww.in', 'cleartax.in', 'angelone.in', 'upstox.com', 'icicidirect.com']
        elif is_stock:
            priority = ['moneycontrol.com', 'nseindia.com', 'bseindia.com', 'economictimes.indiatimes.com', 'tickertape.in']
        elif is_mf:
            priority = ['valueresearchonline.com', 'moneycontrol.com', 'groww.in', 'etmoney.com', 'cleartax.in']
        elif is_general_market:
            # General market / sector queries → broad financial news first
            priority = ['economictimes.indiatimes.com', 'moneycontrol.com', 'livemint.com', 'business-standard.com', 'ndtvprofit.com']
        else:
            # Fully general query → financial news + education
            priority = ['economictimes.indiatimes.com', 'moneycontrol.com', 'livemint.com', 'cleartax.in', 'zerodha.com']

        # Reorder sources so priority ones come first
        for src in reversed(priority):
            if src in sources:
                sources.remove(src)
                sources.insert(0, src)

        print(f"🎯 Query type: {'precious_metal' if is_precious_metal else 'energy' if is_energy else 'industrial' if is_industrial else 'dmat' if is_dmat else 'stock' if is_stock else 'mutual_fund' if is_mf else 'general_market' if is_general_market else 'general'}")
        
        print("📊 Searching priority financial sources...")
        
        # Search priority sources
        for source in sources:
            if len(results) >= num_results:
                break
            
            try:
                source_query = f"{query} site:{source}"
                source_results = ddgs.text(query=source_query, region='in-en', max_results=3)
                
                for result in source_results:
                    url = result.get('href', result.get('link', ''))
                    if url in seen_urls or len(results) >= num_results:
                        continue
                    
                    seen_urls.add(url)
                    results.append({
                        'url': url,
                        'title': result.get('title', ''),
                        'snippet': result.get('body', result.get('snippet', '')),
                        'source': source
                    })
                
                time.sleep(0.2)
            except:
                continue
        
        # General search if needed
        if len(results) < num_results:
            print("🌐 Adding general results...")
            try:
                general_results = ddgs.text(query=f"{query} India", region='in-en', max_results=num_results * 2)
                blocked = ['zhihu.com', 'mobile01.com', 'gold.de', 'weibo.com']
                
                for result in general_results:
                    if len(results) >= num_results:
                        break
                    
                    url = result.get('href', result.get('link', ''))
                    if url in seen_urls or any(b in url for b in blocked):
                        continue
                    
                    seen_urls.add(url)
                    results.append({
                        'url': url,
                        'title': result.get('title', ''),
                        'snippet': result.get('body', result.get('snippet', '')),
                        'source': 'general'
                    })
            except:
                pass
        
        priority_count = len([r for r in results if r.get('source') != 'general'])
        print(f"✅ Found {len(results)} results ({priority_count} from priority sources)")
        
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    return results


def _extract_content(url, max_length=DEFAULT_MAX_CONTENT_LENGTH):
    """Extract content with focus on price tables and financial data"""
    try:
        print(f"📄 Extracting: {url[:60]}...")
        
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()
        
        title = soup.title.string if soup.title else ""
        
        # Priority: Find price tables and financial data
        text = ""
        price_sections = soup.find_all(['table', 'div'], class_=re.compile(r'price|rate|commodity|quote|stock', re.I))
        
        if price_sections:
            for section in price_sections[:3]:
                text += section.get_text(separator=' ', strip=True) + " "
        
        # Get main content
        main = None
        for selector in ['main', 'article', '[role="main"]', '.main-content']:
            main = soup.select_one(selector)
            if main:
                break
        
        if not main:
            divs = soup.find_all('div')
            if divs:
                main = max(divs, key=lambda d: len(d.get_text(strip=True)))
        
        if main:
            text += main.get_text(separator=' ', strip=True)
        
        # Clean
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'Cookie.*?Accept|Subscribe|Sign up', '', text, flags=re.I)
        
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        if len(text) < 200:
            return None
        
        return {'url': url, 'title': title, 'content': text}
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"⚠️  403 Forbidden")
        else:
            print(f"⚠️  HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"⚠️  Error: {str(e)[:50]}")
        return None


def _extract_with_retry(url, max_retries=DEFAULT_RETRY_ATTEMPTS):
    """Extract with retry"""
    for attempt in range(max_retries):
        content = _extract_content(url)
        if content:
            return content
        if attempt < max_retries - 1:
            time.sleep(1)
    return None


def _generate_answer(query, extracted_contents):
    """Generate answer using Groq LLM"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return "Error: GROQ_API_KEY not found in .env file"
    
    print("🤖 Generating answer with Groq LLM...")
    
    llm = ChatGroq(api_key=api_key, model=DEFAULT_MODEL, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS)
    
    # Prepare context
    context = ""
    for i, content in enumerate(extracted_contents, 1):
        if content:
            context += f"\n\n--- Source {i}: {content['title']} ---\n"
            context += f"URL: {content['url']}\n"
            context += f"Content: {content['content'][:3000]}\n"
    
    system_message = SystemMessage(content="""You are an expert research assistant for the Indian Financial Market.

Expertise:
- Stock market (NSE, BSE) - stocks, indices, trading
- Commodities (gold, silver, oil, etc.) - prices, trends
- DMAT accounts - opening, transferring, managing
- Portfolio management - tracking, analysis
- Mutual funds & SIPs
- Banking & finance
- Personal finance - tax, insurance

Guidelines:
1. Synthesize information from all sources
2. Do NOT make up information - only use what's in sources
3. For prices: Give specific numbers with units (₹/INR per gram/10g/kg)
4. For DMAT/accounts: Give step-by-step guidance
5. For comparisons: Present clear pros/cons
6. Be factual, avoid speculation
7. Focus on Indian market (INR, Indian regulations)
8. If sources lack info, acknowledge clearly
9. Do not mention Sources""")
    
    human_message = HumanMessage(content=f"""Based on web search results, answer this question:

Question: {query}

Search Results:
{context}

Provide comprehensive answer:""")
    
    try:
        response = llm.invoke([system_message, human_message])
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def search_and_get_answer_advanced(query):
    """
    Search and get AI-generated answer
    
    Args:
        query (str): Search query
    
    Returns:
        str: AI-generated answer
    """
    print("=" * 80)
    print(f"🚀 AI Search: {query}")
    print("=" * 80)
    
    # Search
    search_results = _search_web(query, num_results=DEFAULT_NUM_RESULTS)
    if not search_results:
        return "No search results found. Please try a different query."
    
    # Extract content
    extracted = []
    attempts = 0
    max_attempts = min(len(search_results), DEFAULT_NUM_TO_EXTRACT * 3)
    
    for result in search_results:
        if len(extracted) >= DEFAULT_NUM_TO_EXTRACT or attempts >= max_attempts:
            break
        
        attempts += 1
        content = _extract_with_retry(result['url'])
        if content:
            extracted.append(content)
        time.sleep(0.3)
    
    if not extracted:
        return "Could not extract content. Sites may be blocking access."
    
    # Generate answer
    answer = _generate_answer(query, extracted)
    
    print("=" * 80)
    print(f"✅ Completed - Used {len(extracted)} sources")
    print("=" * 80)
    
    return answer


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("Testing AI Search...")
    
    answer = search_and_get_answer_advanced("'which sector is booming right now")
    print("\nANSWER:")
    print(answer)