"""Global Instrument Registry and Market Metadata.

Provides standardized instrument definitions across countries, exchanges, and asset classes.
Data model:
{
    "symbol": "AAPL",
    "providerSymbol": "AAPL",
    "name": "Apple Inc.",
    "country": "United States",
    "countryCode": "US",
    "exchange": "NASDAQ",
    "assetClass": "EQUITY",
    "currency": "USD",
    "timezone": "America/New_York",
    "session": "09:30-16:00 EST"
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Supported Country to Exchange Map
COUNTRY_EXCHANGES: Dict[str, List[Dict[str, str]]] = {
    "India": [
        {"code": "NSE", "name": "National Stock Exchange of India", "timezone": "Asia/Kolkata", "currency": "INR"},
        {"code": "BSE", "name": "Bombay Stock Exchange", "timezone": "Asia/Kolkata", "currency": "INR"},
    ],
    "United States": [
        {"code": "NASDAQ", "name": "NASDAQ Stock Market", "timezone": "America/New_York", "currency": "USD"},
        {"code": "NYSE", "name": "New York Stock Exchange", "timezone": "America/New_York", "currency": "USD"},
        {"code": "AMEX", "name": "NYSE American", "timezone": "America/New_York", "currency": "USD"},
        {"code": "CME", "name": "Chicago Mercantile Exchange (Futures)", "timezone": "America/Chicago", "currency": "USD"},
        {"code": "CBOT", "name": "Chicago Board of Trade (Futures)", "timezone": "America/Chicago", "currency": "USD"},
        {"code": "COMEX", "name": "Commodity Exchange Inc. (Futures)", "timezone": "America/New_York", "currency": "USD"},
        {"code": "NYMEX", "name": "New York Mercantile Exchange", "timezone": "America/New_York", "currency": "USD"},
    ],
    "Germany": [
        {"code": "XETRA", "name": "Deutsche Börse Xetra", "timezone": "Europe/Berlin", "currency": "EUR"},
    ],
    "United Kingdom": [
        {"code": "LSE", "name": "London Stock Exchange", "timezone": "Europe/London", "currency": "GBP"},
    ],
    "Japan": [
        {"code": "TSE", "name": "Tokyo Stock Exchange / JPX", "timezone": "Asia/Tokyo", "currency": "JPY"},
    ],
    "Hong Kong": [
        {"code": "HKEX", "name": "Hong Kong Exchanges and Clearing", "timezone": "Asia/Hong_Kong", "currency": "HKD"},
    ],
    "Australia": [
        {"code": "ASX", "name": "Australian Securities Exchange", "timezone": "Australia/Sydney", "currency": "AUD"},
    ],
    "Canada": [
        {"code": "TSX", "name": "Toronto Stock Exchange", "timezone": "America/Toronto", "currency": "CAD"},
    ],
    "Global": [
        {"code": "CRYPTO", "name": "Cryptocurrency Markets", "timezone": "UTC", "currency": "USD"},
        {"code": "FOREX", "name": "Foreign Exchange Markets", "timezone": "UTC", "currency": "USD"},
        {"code": "INDEX", "name": "Global Benchmark Indices", "timezone": "UTC", "currency": "USD"},
    ]
}

# Master Global Instrument Catalog
INSTRUMENT_CATALOG: List[Dict[str, Any]] = [
    # --- UNITED STATES: NASDAQ Equities ---
    {"symbol": "AAPL", "providerSymbol": "AAPL", "name": "Apple Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "MSFT", "providerSymbol": "MSFT", "name": "Microsoft Corporation", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "NVDA", "providerSymbol": "NVDA", "name": "NVIDIA Corporation", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "AMZN", "providerSymbol": "AMZN", "name": "Amazon.com Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "GOOGL", "providerSymbol": "GOOGL", "name": "Alphabet Inc. (Class A)", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "META", "providerSymbol": "META", "name": "Meta Platforms Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "TSLA", "providerSymbol": "TSLA", "name": "Tesla Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "NFLX", "providerSymbol": "NFLX", "name": "Netflix Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "AMD", "providerSymbol": "AMD", "name": "Advanced Micro Devices", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "INTC", "providerSymbol": "INTC", "name": "Intel Corporation", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "QCOM", "providerSymbol": "QCOM", "name": "QUALCOMM Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "AVGO", "providerSymbol": "AVGO", "name": "Broadcom Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "CSCO", "providerSymbol": "CSCO", "name": "Cisco Systems Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "ADBE", "providerSymbol": "ADBE", "name": "Adobe Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "COST", "providerSymbol": "COST", "name": "Costco Wholesale Corp.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "PEP", "providerSymbol": "PEP", "name": "PepsiCo Inc.", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "QQQ", "providerSymbol": "QQQ", "name": "Invesco QQQ Trust", "country": "United States", "countryCode": "US", "exchange": "NASDAQ", "assetClass": "ETF", "currency": "USD", "timezone": "America/New_York"},

    # --- UNITED STATES: NYSE / AMEX Equities ---
    {"symbol": "JPM", "providerSymbol": "JPM", "name": "JPMorgan Chase & Co.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "UNH", "providerSymbol": "UNH", "name": "UnitedHealth Group Inc.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "V", "providerSymbol": "V", "name": "Visa Inc.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "MA", "providerSymbol": "MA", "name": "Mastercard Inc.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "PG", "providerSymbol": "PG", "name": "Procter & Gamble Co.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "JNJ", "providerSymbol": "JNJ", "name": "Johnson & Johnson", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "HD", "providerSymbol": "HD", "name": "Home Depot Inc.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "BAC", "providerSymbol": "BAC", "name": "Bank of America Corp.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "XOM", "providerSymbol": "XOM", "name": "Exxon Mobil Corp.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "WMT", "providerSymbol": "WMT", "name": "Walmart Inc.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "LLY", "providerSymbol": "LLY", "name": "Eli Lilly and Company", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "DIS", "providerSymbol": "DIS", "name": "Walt Disney Co.", "country": "United States", "countryCode": "US", "exchange": "NYSE", "assetClass": "EQUITY", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "SPY", "providerSymbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "country": "United States", "countryCode": "US", "exchange": "AMEX", "assetClass": "ETF", "currency": "USD", "timezone": "America/New_York"},

    # --- UNITED STATES: Futures (CME / CBOT / COMEX / NYMEX) ---
    {"symbol": "ES=F", "providerSymbol": "ES=F", "name": "E-mini S&P 500 Futures", "country": "United States", "countryCode": "US", "exchange": "CME", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/Chicago"},
    {"symbol": "NQ=F", "providerSymbol": "NQ=F", "name": "E-mini Nasdaq-100 Futures", "country": "United States", "countryCode": "US", "exchange": "CME", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/Chicago"},
    {"symbol": "YM=F", "providerSymbol": "YM=F", "name": "E-mini Dow Jones Futures", "country": "United States", "countryCode": "US", "exchange": "CBOT", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/Chicago"},
    {"symbol": "RTY=F", "providerSymbol": "RTY=F", "name": "E-mini Russell 2000 Futures", "country": "United States", "countryCode": "US", "exchange": "CME", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/Chicago"},
    {"symbol": "GC=F", "providerSymbol": "GC=F", "name": "Gold Futures", "country": "United States", "countryCode": "US", "exchange": "COMEX", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "SI=F", "providerSymbol": "SI=F", "name": "Silver Futures", "country": "United States", "countryCode": "US", "exchange": "COMEX", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "CL=F", "providerSymbol": "CL=F", "name": "Crude Oil Futures", "country": "United States", "countryCode": "US", "exchange": "NYMEX", "assetClass": "FUTURES", "currency": "USD", "timezone": "America/New_York"},

    # --- INDIA: NSE / BSE Equities ---
    {"symbol": "RELIANCE", "providerSymbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "TCS", "providerSymbol": "TCS.NS", "name": "Tata Consultancy Services Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "INFY", "providerSymbol": "INFY.NS", "name": "Infosys Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "HDFCBANK", "providerSymbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "ICICIBANK", "providerSymbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "SBIN", "providerSymbol": "SBIN.NS", "name": "State Bank of India", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "BHARTIARTL", "providerSymbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "ITC", "providerSymbol": "ITC.NS", "name": "ITC Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "LARSEN", "providerSymbol": "LT.NS", "name": "Larsen & Toubro Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "AXISBANK", "providerSymbol": "AXISBANK.NS", "name": "Axis Bank Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "DLF", "providerSymbol": "DLF.NS", "name": "DLF Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "COFORGE", "providerSymbol": "COFORGE.NS", "name": "Coforge Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "APLAPOLLO", "providerSymbol": "APLAPOLLO.NS", "name": "APL Apollo Tubes Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "KOTAKBANK", "providerSymbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "MARUTI", "providerSymbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "TATAMOTORS", "providerSymbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "SUNPHARMA", "providerSymbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Industries Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "TITAN", "providerSymbol": "TITAN.NS", "name": "Titan Company Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "APOLLOHOSP", "providerSymbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "CUMMINSIND", "providerSymbol": "CUMMINSIND.NS", "name": "Cummins India Ltd.", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "CHOLAFIN", "providerSymbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment & Finance", "country": "India", "countryCode": "IN", "exchange": "NSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "TATASTEEL", "providerSymbol": "TATASTEEL.BO", "name": "Tata Steel Ltd. (BSE)", "country": "India", "countryCode": "IN", "exchange": "BSE", "assetClass": "EQUITY", "currency": "INR", "timezone": "Asia/Kolkata"},

    # --- GERMANY: XETRA Equities ---
    {"symbol": "SAP", "providerSymbol": "SAP.DE", "name": "SAP SE", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "DB1", "providerSymbol": "DB1.DE", "name": "Deutsche Börse AG", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "SIE", "providerSymbol": "SIE.DE", "name": "Siemens AG", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "ALV", "providerSymbol": "ALV.DE", "name": "Allianz SE", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "BMW", "providerSymbol": "BMW.DE", "name": "Bayerische Motoren Werke AG", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "MBG", "providerSymbol": "MBG.DE", "name": "Mercedes-Benz Group AG", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "VOW3", "providerSymbol": "VOW3.DE", "name": "Volkswagen AG", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "BAS", "providerSymbol": "BAS.DE", "name": "BASF SE", "country": "Germany", "countryCode": "DE", "exchange": "XETRA", "assetClass": "EQUITY", "currency": "EUR", "timezone": "Europe/Berlin"},

    # --- UNITED KINGDOM: LSE Equities ---
    {"symbol": "SHEL", "providerSymbol": "SHEL.L", "name": "Shell PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "AZN", "providerSymbol": "AZN.L", "name": "AstraZeneca PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "HSBA", "providerSymbol": "HSBA.L", "name": "HSBC Holdings PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "ULVR", "providerSymbol": "ULVR.L", "name": "Unilever PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "BP", "providerSymbol": "BP.L", "name": "BP PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "BARC", "providerSymbol": "BARC.L", "name": "Barclays PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},
    {"symbol": "RIO", "providerSymbol": "RIO.L", "name": "Rio Tinto PLC", "country": "United Kingdom", "countryCode": "GB", "exchange": "LSE", "assetClass": "EQUITY", "currency": "GBP", "timezone": "Europe/London"},

    # --- JAPAN: TSE / JPX Equities ---
    {"symbol": "7203", "providerSymbol": "7203.T", "name": "Toyota Motor Corp.", "country": "Japan", "countryCode": "JP", "exchange": "TSE", "assetClass": "EQUITY", "currency": "JPY", "timezone": "Asia/Tokyo"},
    {"symbol": "6758", "providerSymbol": "6758.T", "name": "Sony Group Corp.", "country": "Japan", "countryCode": "JP", "exchange": "TSE", "assetClass": "EQUITY", "currency": "JPY", "timezone": "Asia/Tokyo"},
    {"symbol": "9984", "providerSymbol": "9984.T", "name": "SoftBank Group Corp.", "country": "Japan", "countryCode": "JP", "exchange": "TSE", "assetClass": "EQUITY", "currency": "JPY", "timezone": "Asia/Tokyo"},
    {"symbol": "9983", "providerSymbol": "9983.T", "name": "Fast Retailing Co. (Uniqlo)", "country": "Japan", "countryCode": "JP", "exchange": "TSE", "assetClass": "EQUITY", "currency": "JPY", "timezone": "Asia/Tokyo"},
    {"symbol": "8306", "providerSymbol": "8306.T", "name": "Mitsubishi UFJ Financial", "country": "Japan", "countryCode": "JP", "exchange": "TSE", "assetClass": "EQUITY", "currency": "JPY", "timezone": "Asia/Tokyo"},

    # --- HONG KONG: HKEX Equities ---
    {"symbol": "0700", "providerSymbol": "0700.HK", "name": "Tencent Holdings Ltd.", "country": "Hong Kong", "countryCode": "HK", "exchange": "HKEX", "assetClass": "EQUITY", "currency": "HKD", "timezone": "Asia/Hong_Kong"},
    {"symbol": "9988", "providerSymbol": "9988.HK", "name": "Alibaba Group Holding", "country": "Hong Kong", "countryCode": "HK", "exchange": "HKEX", "assetClass": "EQUITY", "currency": "HKD", "timezone": "Asia/Hong_Kong"},
    {"symbol": "3690", "providerSymbol": "3690.HK", "name": "Meituan", "country": "Hong Kong", "countryCode": "HK", "exchange": "HKEX", "assetClass": "EQUITY", "currency": "HKD", "timezone": "Asia/Hong_Kong"},
    {"symbol": "1810", "providerSymbol": "1810.HK", "name": "Xiaomi Corporation", "country": "Hong Kong", "countryCode": "HK", "exchange": "HKEX", "assetClass": "EQUITY", "currency": "HKD", "timezone": "Asia/Hong_Kong"},

    # --- AUSTRALIA: ASX Equities ---
    {"symbol": "BHP", "providerSymbol": "BHP.AX", "name": "BHP Group Ltd.", "country": "Australia", "countryCode": "AU", "exchange": "ASX", "assetClass": "EQUITY", "currency": "AUD", "timezone": "Australia/Sydney"},
    {"symbol": "CBA", "providerSymbol": "CBA.AX", "name": "Commonwealth Bank of Australia", "country": "Australia", "countryCode": "AU", "exchange": "ASX", "assetClass": "EQUITY", "currency": "AUD", "timezone": "Australia/Sydney"},
    {"symbol": "CSL", "providerSymbol": "CSL.AX", "name": "CSL Ltd.", "country": "Australia", "countryCode": "AU", "exchange": "ASX", "assetClass": "EQUITY", "currency": "AUD", "timezone": "Australia/Sydney"},

    # --- CANADA: TSX Equities ---
    {"symbol": "RY", "providerSymbol": "RY.TO", "name": "Royal Bank of Canada", "country": "Canada", "countryCode": "CA", "exchange": "TSX", "assetClass": "EQUITY", "currency": "CAD", "timezone": "America/Toronto"},
    {"symbol": "TD", "providerSymbol": "TD.TO", "name": "Toronto-Dominion Bank", "country": "Canada", "countryCode": "CA", "exchange": "TSX", "assetClass": "EQUITY", "currency": "CAD", "timezone": "America/Toronto"},
    {"symbol": "SHOP", "providerSymbol": "SHOP.TO", "name": "Shopify Inc.", "country": "Canada", "countryCode": "CA", "exchange": "TSX", "assetClass": "EQUITY", "currency": "CAD", "timezone": "America/Toronto"},

    # --- GLOBAL BENCHMARK INDICES ---
    {"symbol": "SP500", "providerSymbol": "^GSPC", "name": "S&P 500 Index", "country": "United States", "countryCode": "US", "exchange": "INDEX", "assetClass": "INDEX", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "NASDAQ100", "providerSymbol": "^NDX", "name": "NASDAQ-100 Index", "country": "United States", "countryCode": "US", "exchange": "INDEX", "assetClass": "INDEX", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "DOW", "providerSymbol": "^DJI", "name": "Dow Jones Industrial Average", "country": "United States", "countryCode": "US", "exchange": "INDEX", "assetClass": "INDEX", "currency": "USD", "timezone": "America/New_York"},
    {"symbol": "NIFTY50", "providerSymbol": "^NSEI", "name": "NIFTY 50 Index", "country": "India", "countryCode": "IN", "exchange": "INDEX", "assetClass": "INDEX", "currency": "INR", "timezone": "Asia/Kolkata"},
    {"symbol": "DAX", "providerSymbol": "^GDAXI", "name": "DAX Index", "country": "Germany", "countryCode": "DE", "exchange": "INDEX", "assetClass": "INDEX", "currency": "EUR", "timezone": "Europe/Berlin"},
    {"symbol": "FTSE100", "providerSymbol": "^FTSE", "name": "FTSE 100 Index", "country": "United Kingdom", "countryCode": "GB", "exchange": "INDEX", "assetClass": "INDEX", "currency": "GBP", "timezone": "Europe/London"},

    # --- CRYPTO & FOREX ---
    {"symbol": "BTC-USD", "providerSymbol": "BTC-USD", "name": "Bitcoin USD", "country": "Global", "countryCode": "GLOBAL", "exchange": "CRYPTO", "assetClass": "CRYPTO", "currency": "USD", "timezone": "UTC"},
    {"symbol": "ETH-USD", "providerSymbol": "ETH-USD", "name": "Ethereum USD", "country": "Global", "countryCode": "GLOBAL", "exchange": "CRYPTO", "assetClass": "CRYPTO", "currency": "USD", "timezone": "UTC"},
    {"symbol": "EURUSD=X", "providerSymbol": "EURUSD=X", "name": "EUR/USD Currency Pair", "country": "Global", "countryCode": "GLOBAL", "exchange": "FOREX", "assetClass": "FOREX", "currency": "USD", "timezone": "UTC"},
    {"symbol": "USDINR=X", "providerSymbol": "USDINR=X", "name": "USD/INR Currency Pair", "country": "Global", "countryCode": "GLOBAL", "exchange": "FOREX", "assetClass": "FOREX", "currency": "INR", "timezone": "UTC"},
]


def get_all_countries() -> List[str]:
    """Return distinct sorted list of supported countries."""
    countries = ["ALL"] + sorted(list(COUNTRY_EXCHANGES.keys()))
    return countries


def get_exchanges_for_country(country: str = "ALL") -> List[Dict[str, str]]:
    """Return list of exchange dictionaries for specified country."""
    if not country or country.upper() == "ALL":
        all_exchanges: List[Dict[str, str]] = [{"code": "ALL", "name": "All Global Exchanges", "timezone": "UTC", "currency": "USD"}]
        seen = set()
        for ex_list in COUNTRY_EXCHANGES.values():
            for ex in ex_list:
                if ex["code"] not in seen:
                    seen.add(ex["code"])
                    all_exchanges.append(ex)
        return all_exchanges

    ex_list = COUNTRY_EXCHANGES.get(country, [])
    return [{"code": "ALL", "name": f"All {country} Exchanges", "timezone": "UTC", "currency": "USD"}] + ex_list


def get_asset_classes() -> List[str]:
    """Return distinct asset classes supported by system."""
    return ["ALL", "EQUITY", "ETF", "INDEX", "FUTURES", "CRYPTO", "FOREX"]


def find_instrument(symbol: str, exchange: str = "", country: str = "") -> Optional[Dict[str, Any]]:
    """Find instrument from catalog matching symbol and optional exchange/country."""
    clean_sym = (symbol or "").strip().upper()
    if not clean_sym:
        return None

    # Strip .NS, .BO, .DE etc for matching
    base_sym = clean_sym.split(".")[0]

    for item in INSTRUMENT_CATALOG:
        match_sym = item["symbol"].upper() == clean_sym or item["providerSymbol"].upper() == clean_sym or item["symbol"].upper() == base_sym
        if match_sym:
            if exchange and exchange.upper() != "ALL" and item["exchange"].upper() != exchange.upper():
                continue
            if country and country.upper() != "ALL" and item["country"].upper() != country.upper():
                continue
            return item

    return None


def search_instruments(
    query: str = "",
    country: str = "ALL",
    exchange: str = "ALL",
    asset_class: str = "ALL"
) -> List[Dict[str, Any]]:
    """Filter instrument catalog based on text search and global filter selections."""
    q = (query or "").strip().upper()
    c = (country or "ALL").strip()
    e = (exchange or "ALL").strip().upper()
    ac = (asset_class or "ALL").strip().upper()

    results = []
    for item in INSTRUMENT_CATALOG:
        if c != "ALL" and item["country"].upper() != c.upper():
            continue
        if e != "ALL" and item["exchange"].upper() != e:
            continue
        if ac != "ALL" and item["assetClass"].upper() != ac:
            continue

        if q:
            match = (
                q in item["symbol"].upper()
                or q in item["providerSymbol"].upper()
                or q in item["name"].upper()
                or q in item["exchange"].upper()
            )
            if not match:
                continue

        results.append(item)

    return results
