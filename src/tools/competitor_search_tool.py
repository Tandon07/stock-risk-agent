from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import re

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY)

search = DuckDuckGoSearchRun()

def search_competitors(company_name: str) -> list[str]:
    """
    Robust competitor finder that identifies publicly listed Indian companies.
    
    Args:
        company_name: Name of the company to find competitors for
        llm: Language model instance (e.g., ChatOpenAI, ChatGroq)
    
    Returns:
        List of top 5 competitor company names listed on Indian stock exchanges
    """
    
    # Step 1: Identify the company's sector and listing status
    sector_queries = [
        f"{company_name} sector industry NSE BSE India",
        f"{company_name} business segment Indian stock market"
    ]
    
    sector_results = []
    for query in sector_queries:
        try:
            result = search.run(query)
            sector_results.append(result)
        except Exception as e:
            print(f"Sector search failed: {e}")
            continue
    
    sector_combined = "\n\n".join(sector_results)
    
    # Step 2: Get sector information
    sector_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a financial analyst. Analyze the company and return ONLY valid JSON.

Output format (ensure valid JSON with no trailing commas):
{{
    "sector": "Primary sector",
    "business_segments": ["segment1", "segment2"]
}}"""),
        ("user", """Company: {company_name}

Information:
{search_text}

Return sector and business segments in valid JSON format.""")
    ])
    
    parser = JsonOutputParser()
    sector_chain = sector_prompt | llm | parser
    
    try:
        sector_info = sector_chain.invoke({
            "company_name": company_name,
            "search_text": sector_combined[:2500]
        })
        sector = sector_info.get("sector", "")
        segments = sector_info.get("business_segments", [])
    except Exception as e:
        print(f"Sector identification failed: {e}")
        sector = "general"
        segments = []
    
    print(f"Identified Sector: {sector}")
    
    # Step 3: Search for listed competitors with better queries
    competitor_queries = [
        f"top {sector} companies listed NSE BSE India stock market",
        f"{company_name} main competitors NSE BSE listed India",
        f"leading {sector} stocks India NSE BSE",
        f"{sector} listed companies Indian stock exchange market cap",
        f"{sector} listed companies Indian stock exchange market cap with new Listed Name"
    ]
    
    # Add segment-specific search
    if segments:
        competitor_queries.append(f"{segments[0]} companies NSE BSE listed India")
    
    competitor_results = []
    for query in competitor_queries:
        try:
            result = search.run(query)
            competitor_results.append(result)
        except Exception as e:
            print(f"Search failed: {e}")
            continue
    
    if not competitor_results:
        return []
    
    combined_text = "\n\n".join(competitor_results)
    
    # Step 4: Extract competitors with fixed JSON format
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Indian stock market expert. Extract ONLY NSE/BSE listed competitors.

CRITICAL JSON RULES:
- NO trailing commas in arrays
- All strings must use double quotes
- Return exactly 5-8 companies

MUST BE LISTED ON NSE/BSE:
✓ Publicly traded on Indian stock exchanges
✓ Direct competitors or sector peers
✓ Use official company names

EXCLUDE:
✗ Private/unlisted companies (Lenskart, Swiggy, etc.)
✗ Subsidiaries or brand names
✗ The target company itself
✗ Foreign companies without Indian listing

Return EXACTLY this format:
{{
    "competitors": ["Company One", "Company Two", "Company Three", "Company Four", "Company Five"]
}}

Example valid output:
{{
    "competitors": ["Reliance Industries", "HDFC Bank", "Infosys"]
}}

IMPORTANT: No trailing comma after the last element in the array!"""),
        ("user", """Target Company: {company_name}
Sector: {sector}

Search Results:
{search_text}

Extract top 5-8 NSE/BSE listed competitors. Return valid JSON only.""")
    ])
    
    chain = extraction_prompt | llm | parser
    
    try:
        result = chain.invoke({
            "company_name": company_name,
            "sector": sector,
            "search_text": combined_text[:4500]
        })
        
        competitors_raw = result.get("competitors", [])
        
        # Step 5: Clean and validate
        validated_competitors = []
        seen = set()
        
        for comp in competitors_raw:
            comp_name = str(comp).strip()
            
            # Remove ticker symbols and parentheses
            comp_name = re.sub(r'\s*\([^)]*\)\s*', '', comp_name)
            comp_name = re.sub(r'\s*\[[^\]]*\]\s*', '', comp_name)
            comp_name = re.sub(r'\s+', ' ', comp_name).strip()
            
            comp_lower = comp_name.lower()
            company_lower = company_name.lower()
            
            # Strict validation
            if (comp_name and 
                len(comp_name) > 3 and
                comp_lower != company_lower and
                comp_lower not in company_lower and
                company_lower not in comp_lower and
                comp_lower not in seen and
                not comp_name.replace(' ', '').isdigit() and  # Not just numbers
                # Not generic terms
                comp_name not in ['NSE', 'BSE', 'India', 'Limited', 'Ltd', 'Stock Market'] and
                not all(word in ['the', 'of', 'and', 'in', 'india', 'limited', 'ltd'] for word in comp_lower.split())):
                
                validated_competitors.append(comp_name)
                seen.add(comp_lower)
                
                if len(validated_competitors) >= 5:
                    break
        
        return validated_competitors[:5]  # Return exactly top 5
        
    except json.JSONDecodeError as je:
        print(f"JSON parsing failed: {je}")
        # Fallback: try to extract from raw text
        return []
    except Exception as e:
        print(f"Extraction failed: {e}")
        return []


if __name__ == "__main__":

    print(search_competitors("Zomato", llm))
    # Test with different companies
    # test_companies = ["Lenskart", "Infosys", "HDFC Bank", "Reliance Industries"]
    
    # for company in test_companies:
    #     print(f"\n{'='*60}")
    #     print(f"Testing: {company}")
    #     print(f"{'='*60}")
    #     competitors = search_competitors_robust(company, llm)
    #     print(f"\nTop 5 Listed Competitors:")
    #     for i, comp in enumerate(competitors, 1):
    #         print(f"{i}. {comp}")
        
    #     if len(competitors) == 0:
    #         print("⚠ No listed competitors found. Company may be in unlisted sector.")