import requests
import json
from typing import Dict, Optional, List
import re
from difflib import SequenceMatcher
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
import time

class AITickerResolver:
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize the AI Ticker Resolver
        
        Args:
            groq_api_key: Optional Groq API key. If not provided, uses environment variable.
        """
        self.groq_api_key = groq_api_key
        self.cache = {}
        
        # Try to import langchain
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage
            self.ChatGroq = ChatGroq
            self.HumanMessage = HumanMessage
            self.has_langchain = True
        except ImportError:
            self.has_langchain = False
            if groq_api_key:
                print("⚠️  LangChain not installed. Install with: pip install langchain-groq")
    
    def _name_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple name similarity"""
        # Normalize
        s1 = re.sub(r'\b(limited|ltd|pvt|private|inc|corp)\b\.?', '', s1.lower())
        s2 = re.sub(r'\b(limited|ltd|pvt|private|inc|corp)\b\.?', '', s2.lower())
        s1 = re.sub(r'\s+', ' ', s1).strip()
        s2 = re.sub(r'\s+', ' ', s2).strip()
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _search_yahoo_finance(self, company_name: str) -> Optional[Dict]:
        """Search Yahoo Finance directly for ticker"""
        
        # Try multiple query variations
        queries = [
            company_name,
            f"{company_name} limited",
            f"{company_name} ltd",
        ]
        
        for query in queries:
            try:
                search_url = "https://query2.finance.yahoo.com/v1/finance/search"
                headers = {
                    'User-Agent': 'Mozilla/5.0'
                }
                params = {
                    'q': query,
                    'quotesCount': 15,
                    'newsCount': 0,
                    'enableFuzzyQuery': True
                }
                
                response = requests.get(search_url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    quotes = data.get('quotes', [])
                    
                    # Collect all Indian stocks
                    indian_stocks = []
                    
                    for quote in quotes:
                        symbol = quote.get('symbol', '')
                        exchange = quote.get('exchange', '')
                        name = quote.get('longname') or quote.get('shortname', '')
                        
                        # Check if it's an Indian stock
                        if '.NS' in symbol or '.BO' in symbol or 'NSE' in exchange or 'BSE' in exchange:
                            nse_symbol = None
                            bse_symbol = None
                            
                            if '.NS' in symbol:
                                nse_symbol = symbol.replace('.NS', '')
                            elif '.BO' in symbol:
                                bse_symbol = symbol.replace('.BO', '')
                            elif 'NSE' in exchange:
                                nse_symbol = symbol
                            elif 'BSE' in exchange:
                                bse_symbol = symbol
                            
                            indian_stocks.append({
                                'NSE': nse_symbol,
                                'BSE': bse_symbol,
                                'company_name': name,
                                'symbol': symbol,
                                'score': self._name_similarity(company_name.lower(), name.lower())
                            })
                    
                    # Sort by similarity score and return best match
                    if indian_stocks:
                        indian_stocks.sort(key=lambda x: x['score'], reverse=True)
                        best = indian_stocks[0]
                        
                        # Must have reasonable similarity
                        if best['score'] > 0.3:
                            return {
                                'NSE': best['NSE'],
                                'BSE': best['BSE'],
                                'company_name': best['company_name'],
                                'source': 'yahoo_finance'
                            }
            
            except Exception as e:
                continue
        
        return None
    
    def _search_google_finance(self, company_name: str) -> Optional[Dict]:
        """Search Google Finance for ticker info"""
        try:
            # Search Google for stock info
            search_url = "https://www.google.com/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {
                'q': f'{company_name} NSE BSE stock ticker India',
                'hl': 'en'
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                
                # Look for NSE: or BSE: patterns
                nse_match = re.search(r'NSE[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
                bse_match = re.search(r'BSE[:\s]+(\d+)', text, re.IGNORECASE)
                
                # Also look for stock card patterns
                symbol_match = re.search(r'data-symbol="([A-Z0-9]+)"', text)
                
                if nse_match or bse_match or symbol_match:
                    return {
                        'NSE': nse_match.group(1) if nse_match else (symbol_match.group(1) if symbol_match else None),
                        'BSE': bse_match.group(1) if bse_match else None,
                        'company_name': company_name,
                        'source': 'google_finance'
                    }
        
        except Exception as e:
            pass
        
        return None
    
    def _search_screener_in(self, company_name: str) -> Optional[Dict]:
        """
        Search Screener.in for ticker info using proper URL encoding
        and scraping the company page for BSE/NSE codes
        """
        try:
            # URL encode the company name to handle special characters like &
            encoded_name = quote(company_name)
            search_url = f"https://www.screener.in/api/company/search/?q={encoded_name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.screener.in/'
            }
            
            print(f"  ↳ Screener.in search URL: {search_url}")
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                search_results = response.json()
                
                if not search_results:
                    return None
                
                # Get the FIRST result (most relevant)
                first_result = search_results[0]
                company_url = first_result.get('url')
                
                if not company_url:
                    return None
                
                # Fetch the company page to get BSE/NSE codes
                base_url = "https://www.screener.in"
                full_url = f"{base_url}{company_url}"
                
                print(f"  ↳ Fetching company page: {full_url}")
                time.sleep(0.5)  # Be respectful
                
                page_response = requests.get(full_url, headers=headers, timeout=10)
                page_response.raise_for_status()
                
                # Parse the HTML
                soup = BeautifulSoup(page_response.content, 'html.parser')
                
                # Extract company name from h1
                company_heading = soup.find('h1')
                company_name_full = company_heading.text.strip() if company_heading else first_result.get('name')
                
                # Search for BSE and NSE tickers in the page text
                page_text = soup.get_text()
                
                bse_match = re.search(r'BSE:\s*(\d+)', page_text)
                nse_match = re.search(r'NSE:\s*([A-Z&]+)', page_text)
                
                bse_code = bse_match.group(1) if bse_match else None
                nse_code = nse_match.group(1) if nse_match else None
                
                if bse_code or nse_code:
                    return {
                        'NSE': nse_code,
                        'BSE': bse_code,
                        'company_name': company_name_full,
                        'source': 'screener_in'
                    }
        
        except Exception as e:
            print(f"  ⚠️  Screener.in error: {e}")
        
        return None
    
    def _search_web(self, query: str) -> List[str]:
        """Search web for stock ticker information"""
        try:
            # Using DuckDuckGo HTML search (no API key needed)
            search_url = "https://html.duckduckgo.com/html/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {
                'q': query,
                'kl': 'in-en'  # India region
            }
            
            response = requests.post(search_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Extract text snippets from results
                text = response.text
                
                # Simple extraction of result snippets
                snippets = []
                
                # Look for result divs and extract text
                results = re.findall(r'class="result__snippet">(.*?)</a>', text, re.DOTALL)
                
                for result in results[:5]:  # Top 5 results
                    # Clean HTML tags
                    clean = re.sub(r'<[^>]+>', '', result)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    if clean and len(clean) > 20:
                        snippets.append(clean)
                
                return snippets
        except Exception as e:
            pass
        
        return []
    
    def _extract_ticker_with_llm(self, company_name: str, context: str) -> Optional[Dict]:
        """Use Groq LLM (via LangChain) to extract ticker from search results"""
        
        if not self.has_langchain:
            print("  ⚠️  LangChain not available, skipping LLM extraction")
            return None
        
        prompt = f"""Given the following web search results about "{company_name}", extract the stock ticker symbols for NSE and BSE exchanges.

Search Results:
{context}

Please extract and return ONLY a JSON object with this exact format:
{{
    "NSE": "SYMBOL or null",
    "BSE": "SYMBOL or null",
    "company_name": "Full official company name",
    "confidence": "high/medium/low"
}}

Rules:
- NSE symbols are usually alphabetic (e.g., INFY, TCS, RELIANCE)
- BSE symbols can be numeric (e.g., 500209, 532540) or alphabetic
- Return null if not found
- Only return the JSON, nothing else"""

        try:
            # Initialize Groq LLM via LangChain
            llm = self.ChatGroq(
                model="llama-3.3-70b-versatile",  # Fast and accurate
                groq_api_key=self.groq_api_key,
                temperature=0,  # Deterministic output
                max_tokens=500
            )
            
            # Create message and invoke
            message = self.HumanMessage(content=prompt)
            response = llm.invoke([message])
            
            # Extract JSON from response
            content = response.content
            
            # Try to find JSON in response
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                ticker_info = json.loads(json_match.group())
                ticker_info['source'] = 'groq_llm'
                return ticker_info
        
        except Exception as e:
            print(f"  ⚠️  LLM extraction error: {e}")
        
        return None
    
    def resolve_ticker(self, company_name: str, use_llm: bool = True) -> Dict:
        """
        Resolve company name to ticker symbol(s)
        
        Args:
            company_name: Company name to search for
            use_llm: Whether to use LLM for extraction (requires API key)
        
        Returns:
            Dictionary with NSE/BSE tickers and match information
        """
        if not company_name:
            return {
                'NSE': None,
                'BSE': None,
                'error': 'Empty company name provided'
            }
        
        # Check cache
        cache_key = company_name.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        print(f"\n🔍 Searching for: {company_name}")
        
        # Collect results from all sources
        result = {
            'NSE': None,
            'BSE': None,
            'company_name': company_name,
            'sources': []
        }
        
        # Strategy 1: Try Yahoo Finance first (fastest and reliable)
        print("  ↳ Trying Yahoo Finance...")
        yahoo_result = self._search_yahoo_finance(company_name)
        if yahoo_result:
            if yahoo_result.get('NSE'):
                result['NSE'] = yahoo_result['NSE']
                result['sources'].append('yahoo_finance')
            if yahoo_result.get('BSE'):
                result['BSE'] = yahoo_result['BSE']
                if 'yahoo_finance' not in result['sources']:
                    result['sources'].append('yahoo_finance')
            if yahoo_result.get('company_name'):
                result['company_name'] = yahoo_result['company_name']
        
        # Strategy 2: Try Screener.in (improved with proper encoding and scraping)
        print("  ↳ Trying Screener.in...")
        screener_result = self._search_screener_in(company_name)
        if screener_result:
            if screener_result.get('NSE') and not result['NSE']:
                result['NSE'] = screener_result['NSE']
                result['sources'].append('screener_in')
            if screener_result.get('BSE') and not result['BSE']:
                result['BSE'] = screener_result['BSE']
                if 'screener_in' not in result['sources']:
                    result['sources'].append('screener_in')
            # Use screener name if we don't have a good one
            if screener_result.get('company_name') and result['company_name'] == company_name:
                result['company_name'] = screener_result['company_name']
        
        # If we have at least one ticker, try to find the other exchange
        if result['NSE'] and not result['BSE']:
            # Try searching for BSE code using NSE symbol
            print("  ↳ Looking for BSE code...")
            bse_result = self._search_yahoo_finance(f"{result['NSE']} BSE")
            if bse_result and bse_result.get('BSE'):
                result['BSE'] = bse_result['BSE']
        
        elif result['BSE'] and not result['NSE']:
            # Try searching for NSE code using BSE symbol
            print("  ↳ Looking for NSE code...")
            nse_result = self._search_yahoo_finance(f"{result['company_name']} NSE")
            if nse_result and nse_result.get('NSE'):
                result['NSE'] = nse_result['NSE']
        
        # Strategy 3: Try Google Finance if we still don't have both
        if not result['NSE'] or not result['BSE']:
            print("  ↳ Trying Google Finance...")
            gf_result = self._search_google_finance(company_name)
            if gf_result:
                if gf_result.get('NSE') and not result['NSE']:
                    result['NSE'] = gf_result['NSE']
                    result['sources'].append('google_finance')
                if gf_result.get('BSE') and not result['BSE']:
                    result['BSE'] = gf_result['BSE']
                    if 'google_finance' not in result['sources']:
                        result['sources'].append('google_finance')
        
        # Check if we found anything
        if result['NSE'] or result['BSE']:
            result['source'] = ', '.join(result['sources'])
            print(f"  ✓ Found: NSE={result['NSE'] or 'N/A'}, BSE={result['BSE'] or 'N/A'}")
            self.cache[cache_key] = result
            return result
        
        # Strategy 4: Web search + LLM extraction (last resort)
        if use_llm and self.groq_api_key:
            print("  ↳ Trying web search + Groq LLM...")
            
            # Build search query
            search_queries = [
                f"{company_name} NSE BSE stock ticker symbol",
                f"{company_name} stock code NSE India",
                f"{company_name} share price NSE BSE"
            ]
            
            all_snippets = []
            for query in search_queries[:2]:  # Use first 2 queries
                snippets = self._search_web(query)
                all_snippets.extend(snippets)
            
            if all_snippets:
                context = "\n\n".join(all_snippets[:10])
                llm_result = self._extract_ticker_with_llm(company_name, context)
                
                if llm_result and (llm_result.get('NSE') or llm_result.get('BSE')):
                    print(f"  ✓ Found via Groq LLM extraction")
                    self.cache[cache_key] = llm_result
                    return llm_result
        
        # Not found
        result = {
            'NSE': None,
            'BSE': None,
            'error': f'Could not find ticker for "{company_name}"',
            'company_name': company_name
        }
        
        print(f"  ✗ Not found")
        return result


# Convenience function
_resolver_instance = None

def resolve_ticker(company_name: str) -> Dict:
    """
    Resolve company name to stock ticker(s) using AI and web search
    
    Args:
        company_name: Company name (e.g., 'Infosys', 'Zomato', 'TCS', 'M&M')
    
    Returns:
        Dictionary with ticker information
    
    Examples:
        >>> resolve_ticker('Infosys')
        {'NSE': 'INFY', 'BSE': '500209', 'company_name': 'Infosys Limited', 'source': 'yahoo_finance'}
        
        >>> resolve_ticker('M&M')
        {'NSE': 'M&M', 'BSE': '500520', 'company_name': 'Mahindra & Mahindra Limited', 'source': 'screener_in'}
    
    Note:
        - Automatically takes the FIRST (most relevant) search result
        - Works WITHOUT API key for 99% of cases
        - Proper URL encoding handles special characters like & in M&M
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    use_llm = bool(groq_api_key)
    global _resolver_instance
    
    if _resolver_instance is None:
        _resolver_instance = AITickerResolver(groq_api_key=groq_api_key)
    
    return _resolver_instance.resolve_ticker(company_name, use_llm=use_llm)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("AI-Powered Indian Stock Ticker Resolver")
    print("=" * 70)
    
    # Test cases including M&M
    test_companies = [
        'gold',
        'silver',
        'copper'
    ]
    
    for company in test_companies:
        result = resolve_ticker(company)
        
        print(f"\n{'='*70}")
        print(f"Query: '{company}'")
        print(f"Company: {result.get('company_name', 'N/A')}")
        print(f"NSE: {result.get('NSE', 'N/A')}")
        print(f"BSE: {result.get('BSE', 'N/A')}")
        if 'source' in result:
            print(f"Source: {result['source']}")
        if 'error' in result:
            print(f"❌ {result['error']}")
        print("="*70)