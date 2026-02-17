COMMODITY_MAP = {
    # 🟡 Precious Metals (MCX)
    "gold": "GOLD",
    "silver": "SILVER",

    # 🔩 Base Metals (MCX)
    "copper": "COPPER",
    "aluminium": "ALUMINIUM",
    "aluminum": "ALUMINIUM",   # alias
    "zinc": "ZINC",
    "lead": "LEAD",
    "nickel": "NICKEL",

    # 🛢 Energy (MCX)
    "crude oil": "CRUDEOIL",
    "oil": "CRUDEOIL",         # alias
    "natural gas": "NATGAS",
    "gas": "NATGAS",           # alias

    # 🌾 Agri (MCX)
    "cotton": "COTTON",
    "kapas": "KAPAS",

    # 🌾 Agri (NCDEX)
    "soybean": "SOYBEAN",
    "soy oil": "SOYOIL",
    "crude palm oil": "CPO",
    "mustard": "MUSTARD",
    "mustard seed": "MUSTARD",
    "refined soya oil": "REFSOYOIL",
    "castor seed": "CASTORSEED",
    "cotton seed oilcake": "CSO",
    "chana": "CHANA",
    "turmeric": "TURMERIC",
    "jeera": "JEERA",
    "dhaniya": "DHANIYA",
    "sugar": "SUGAR",
    "wheat": "WHEAT",
    "paddy": "PADDY",
    "maize": "MAIZE",
    "barley": "BARLEY",
}

def resolve_commodity_symbol(name: str) -> str | None:
    if not name:
        return None

    name = name.lower()
    for key, symbol in COMMODITY_MAP.items():
        if key in name:
            return symbol
    return None


# print(resolve_commodity_symbol("gold price")      )  # "GOLD"
# print(resolve_commodity_symbol("crude oil today") ) # "CRUDEOIL"
# print(resolve_commodity_symbol("natural gas mcx") ) # "NATGAS"
# print(resolve_commodity_symbol("jeera futures")   ) # "JEERA"
# print(resolve_commodity_symbol("silver")          ) # "SILVER"
