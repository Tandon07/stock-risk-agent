"""
Dynamic Sector Screener Tool for Indian Stocks
Uses NSE/BSE data, Yahoo Finance, and Screener.in to get real sector compositions
"""

import requests
import json
from typing import List, Dict, Optional
import re
from collections import defaultdict
import os

class SectorScreener:
    def __init__(self):
        """Initialize the sector screener"""
        self.cache = {}
        self.sector_mappings = self._load_sector_mappings()
    
    def _load_sector_mappings(self) -> Dict[str, List[str]]:
        """
        Load flexible sector name mappings to handle various user inputs
        Maps user queries to standardized sector names
        """
        return {
            # Technology & IT
            'it': ['Information Technology', 'IT', 'Technology'],
            'technology': ['Information Technology', 'IT', 'Technology'],
            'software': ['Information Technology', 'IT', 'Technology'],
            'tech': ['Information Technology', 'IT', 'Technology'],
            
            # Banking & Finance
            'banking': ['Banks', 'Banking', 'Finance'],
            'bank': ['Banks', 'Banking', 'Finance'],
            'finance': ['Finance', 'Financial Services', 'Banking'],
            'financial': ['Finance', 'Financial Services', 'Banking'],
            'nbfc': ['Finance', 'Financial Services', 'NBFC'],
            
            # Energy & Power
            'energy': ['Energy', 'Oil & Gas', 'Power'],
            'power': ['Power', 'Energy'],
            'oil': ['Oil & Gas', 'Energy'],
            'gas': ['Oil & Gas', 'Energy'],
            
            # Automobiles & EV
            'auto': ['Automobile', 'Auto', 'Automobiles'],
            'automobile': ['Automobile', 'Auto', 'Automobiles'],
            'ev': ['Automobile', 'Electric Vehicles', 'Auto'],
            'electric vehicle': ['Automobile', 'Electric Vehicles'],
            
            # Pharma & Healthcare
            'pharma': ['Pharmaceuticals', 'Pharma', 'Healthcare'],
            'pharmaceutical': ['Pharmaceuticals', 'Pharma', 'Healthcare'],
            'healthcare': ['Healthcare', 'Pharma', 'Pharmaceuticals'],
            
            # FMCG & Consumer
            'fmcg': ['FMCG', 'Consumer Goods', 'Consumer'],
            'consumer': ['Consumer Goods', 'FMCG', 'Consumer'],
            
            # Infrastructure & Construction
            'infrastructure': ['Infrastructure', 'Construction'],
            'construction': ['Construction', 'Infrastructure'],
            
            # Metals & Mining
            'metal': ['Metals', 'Metal', 'Mining'],
            'metals': ['Metals', 'Metal', 'Mining'],
            'mining': ['Mining', 'Metals'],
            'steel': ['Metals', 'Steel'],
            
            # Telecom
            'telecom': ['Telecom', 'Telecommunications'],
            'telecommunications': ['Telecom', 'Telecommunications'],
            
            # Real Estate
            'realty': ['Real Estate', 'Realty'],
            'real estate': ['Real Estate', 'Realty'],
        }
    
    def _normalize_sector(self, sector: str) -> List[str]:
        """Convert user input to standardized sector names"""
        sector_lower = sector.lower().strip()
        
        if sector_lower in self.sector_mappings:
            return self.sector_mappings[sector_lower]
        
        # Return as-is if not in mappings (will search directly)
        return [sector.title()]
    
    def _fetch_nse_sector_stocks(self, sector: str) -> List[Dict]:
        """
        Fetch sector stocks from NSE India
        NSE provides sector-wise stock listings
        """
        try:
            # NSE has sector indices - try to fetch constituents
            # NIFTY sector indices endpoint
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            # Map sector to NSE index name
            nse_index_map = {
                'Information Technology': 'NIFTY IT',
                'IT': 'NIFTY IT',
                'Technology': 'NIFTY IT',
                'Banks': 'NIFTY BANK',
                'Banking': 'NIFTY BANK',
                'Finance': 'NIFTY FINANCIAL SERVICES',
                'Financial Services': 'NIFTY FINANCIAL SERVICES',
                'Pharma': 'NIFTY PHARMA',
                'Pharmaceuticals': 'NIFTY PHARMA',
                'FMCG': 'NIFTY FMCG',
                'Consumer Goods': 'NIFTY FMCG',
                'Auto': 'NIFTY AUTO',
                'Automobile': 'NIFTY AUTO',
                'Metals': 'NIFTY METAL',
                'Metal': 'NIFTY METAL',
                'Energy': 'NIFTY ENERGY',
                'Oil & Gas': 'NIFTY ENERGY',
                'Realty': 'NIFTY REALTY',
                'Real Estate': 'NIFTY REALTY',
            }
            
            index_name = nse_index_map.get(sector)
            if not index_name:
                return []
            
            # Try NSE official API (may require proper headers)
            url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name.replace(' ', '%20')}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                stocks = []
                
                for item in data.get('data', []):
                    symbol = item.get('symbol')
                    if symbol and symbol not in ['Nifty', 'NIFTY']:
                        stocks.append({
                            'symbol': symbol,
                            'name': item.get('meta', {}).get('companyName', symbol),
                            'source': 'nse'
                        })
                
                return stocks
        
        except Exception as e:
            pass
        
        return []
    
    def _fetch_yahoo_sector_stocks(self, sector: str) -> List[Dict]:
        """
        Fetch sector stocks from Yahoo Finance using screener
        """
        try:
            # Yahoo Finance screener (basic search)
            search_url = "https://query2.finance.yahoo.com/v1/finance/search"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            # Search for sector name + India
            params = {
                'q': f'{sector} India stock NSE',
                'quotesCount': 20,
                'newsCount': 0,
                'enableFuzzyQuery': True
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                stocks = []
                
                for quote in data.get('quotes', []):
                    symbol = quote.get('symbol', '')
                    
                    # Only Indian stocks
                    if '.NS' in symbol or '.BO' in symbol:
                        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
                        stocks.append({
                            'symbol': clean_symbol,
                            'name': quote.get('longname') or quote.get('shortname', clean_symbol),
                            'source': 'yahoo'
                        })
                
                return stocks[:15]  # Limit to top 15
        
        except Exception:
            pass
        
        return []
    
    def _fetch_screener_sector_stocks(self, sector: str) -> List[Dict]:
        """
        Fetch sector stocks from Screener.in
        Screener.in has excellent sector classifications
        """
        try:
            # Screener.in has a screens API
            # We can search by sector
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
            
            # Search for companies in sector
            search_url = "https://www.screener.in/api/company/search/"
            params = {'q': sector}
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    stocks = []
                    
                    for company in data[:15]:  # Top 15
                        stocks.append({
                            'symbol': company.get('nse_code') or company.get('bse_code'),
                            'name': company.get('name', ''),
                            'source': 'screener'
                        })
                    
                    return [s for s in stocks if s['symbol']]  # Filter out None
        
        except Exception:
            pass
        
        return []
    
    def _fetch_moneycontrol_sector(self, sector: str) -> List[Dict]:
        """
        Scrape sector data from MoneyControl (fallback)
        MoneyControl has good sector pages
        """
        try:
            # MoneyControl has sector pages
            sector_slug = sector.lower().replace(' ', '-')
            url = f"https://www.moneycontrol.com/stocks/marketstats/sectoral-gainers/{sector_slug}/"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                
                # Extract stock symbols (basic regex)
                # MoneyControl shows NSE symbols
                symbols = re.findall(r'/company/[^/]+/([A-Z0-9]+)', text)
                
                if symbols:
                    # Deduplicate
                    unique_symbols = list(dict.fromkeys(symbols))[:15]
                    
                    return [
                        {
                            'symbol': sym,
                            'name': sym,  # Don't have full name
                            'source': 'moneycontrol'
                        }
                        for sym in unique_symbols
                    ]
        
        except Exception:
            pass
        
        return []
    
    def _deduplicate_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        Deduplicate stocks from multiple sources
        Prefer stocks with full names
        """
        seen = {}
        
        for stock in stocks:
            symbol = stock['symbol']
            
            if symbol not in seen:
                seen[symbol] = stock
            else:
                # Prefer entry with longer/better name
                if len(stock.get('name', '')) > len(seen[symbol].get('name', '')):
                    seen[symbol] = stock
        
        return list(seen.values())
    
    def search_sector_stocks(self, sector: str) -> List[str]:
        """
        Search for stocks in a given sector
        
        Args:
            sector: Sector name (e.g., 'IT', 'Banking', 'Pharma', 'EV')
            limit: Maximum number of stocks to return
            use_cache: Whether to use cached results
        
        Returns:
            List of stock symbols (NSE)
        
        Examples:
            >>> search_sector_stocks('IT', limit=5)
            ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM']
            
            >>> search_sector_stocks('Banking')
            ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', ...]
        """
        limit: int = 10
        use_cache: bool = True

        if not sector:
            return []
        
        # Check cache
        cache_key = f"{sector.lower()}:{limit}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        print(f"\n🔍 Searching for {sector.upper()} sector stocks...")
        
        # Normalize sector name
        sector_variants = self._normalize_sector(sector)
        
        all_stocks = []
        
        # Try multiple sources for each variant
        for variant in sector_variants:
            print(f"  ↳ Trying: {variant}")
            
            # Source 1: NSE (most reliable)
            nse_stocks = self._fetch_nse_sector_stocks(variant)
            if nse_stocks:
                print(f"    ✓ NSE: Found {len(nse_stocks)} stocks")
                all_stocks.extend(nse_stocks)
            
            # Source 2: Yahoo Finance
            yahoo_stocks = self._fetch_yahoo_sector_stocks(variant)
            if yahoo_stocks:
                print(f"    ✓ Yahoo: Found {len(yahoo_stocks)} stocks")
                all_stocks.extend(yahoo_stocks)
            
            # Source 3: Screener.in
            screener_stocks = self._fetch_screener_sector_stocks(variant)
            if screener_stocks:
                print(f"    ✓ Screener: Found {len(screener_stocks)} stocks")
                all_stocks.extend(screener_stocks)
            
            # If we have enough stocks, stop
            if len(all_stocks) >= limit * 2:
                break
        
        # Deduplicate
        unique_stocks = self._deduplicate_stocks(all_stocks)
        
        # Extract just symbols
        symbols = [s['symbol'] for s in unique_stocks if s.get('symbol')]
        
        # Limit results
        result = symbols[:limit]
        
        if result:
            print(f"  ✓ Returning {len(result)} stocks: {', '.join(result[:5])}{'...' if len(result) > 5 else ''}")
        else:
            print(f"  ✗ No stocks found for sector: {sector}")
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def get_sector_info(self, sector: str) -> Dict:
        """
        Get detailed information about a sector
        
        Returns:
            Dictionary with sector info including stocks and metadata
        """
        stocks = self.search_sector_stocks(sector)
        limit=20
        return {
            'sector': sector,
            'stock_count': len(stocks),
            'stocks': stocks,
            'sector_variants': self._normalize_sector(sector)
        }


# Convenience function
_screener_instance = None

def search_sector_stocks(sector: str, limit: int = 10) -> List[str]:
    """
    Returns a list of representative stocks for a sector.
    
    Args:
        sector: Sector name (e.g., 'IT', 'Banking', 'Pharma', 'EV', 'Energy')
        limit: Maximum number of stocks to return (default: 10)
    
    Returns:
        List of NSE stock symbols
    
    Examples:
        >>> search_sector_stocks('IT', limit=5)
        ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM']
        
        >>> search_sector_stocks('Banking')
        ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'SBIN', ...]
        
        >>> search_sector_stocks('EV')
        ['TATAMOTORS', 'M&M', 'TIINDIA', 'MOTHERSON', ...]
    
    Note:
        - Uses NSE India, Yahoo Finance, and Screener.in
        - Results are cached for performance
        - No API keys required
    """
    global _screener_instance
    
    if _screener_instance is None:
        _screener_instance = SectorScreener()
    
    return _screener_instance.search_sector_stocks(sector)

# Test the function
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Sector Screener Tool")
    print("=" * 60)
    
    # Test various sectors
    test_sectors = ['EV']
    
    for sector in test_sectors:
        stocks = search_sector_stocks(sector)
        print(f"\n{'='*60}")
        print(f"Top 5 {sector.upper()} stocks: {stocks}")