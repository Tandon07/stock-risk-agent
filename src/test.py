import requests
import json
from typing import Dict, Optional, List
import re
from difflib import SequenceMatcher
import os

def search_google_finance(company_name: str) -> Optional[Dict]:
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
    
print(search_google_finance("Mahindra and Mahindra Limited"))