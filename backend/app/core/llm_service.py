# """
# Hugging Face LLM Service - Free Inference API
# Production-ready integration for receipt data extraction
# """
# import os
# from typing import Optional, Dict, Any
# from langchain_huggingface import HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from dotenv import load_dotenv
# import logging

# load_dotenv()

# logger = logging.getLogger(__name__)

# class HuggingFaceService:
#     """Free Hugging Face Inference API Service"""
    
#     def __init__(self):
#         self.api_key = os.getenv("HUGGINGFACE_API_KEY", "")
#         self.model_name = os.getenv("HF_MODEL_NAME", "microsoft/Phi-3-mini-4k-instruct")
#         self.rate_limit = int(os.getenv("HF_RATE_LIMIT", "5"))
        
#         if not self.api_key or self.api_key == "hf_your_free_token_here":
#             logger.warning("Hugging Face API key not configured. Using mock mode.")
#             self.mock_mode = True
#         else:
#             self.mock_mode = False
#             self._initialize_llm()
    
#     def _initialize_llm(self):
#         """Initialize Hugging Face LLM endpoint"""
#         try:
#             self.llm = HuggingFaceEndpoint(
#                 repo_id=self.model_name,
#                 huggingfacehub_api_token=self.api_key,
#                 task="text-generation",
#                 max_new_tokens=1024,
#                 temperature=0.1,  # Low temperature for structured output
#                 top_p=0.95,
#                 repetition_penalty=1.1,
#             )
#             logger.info(f"Initialized Hugging Face LLM: {self.model_name}")
#         except Exception as e:
#             logger.error(f"Failed to initialize LLM: {str(e)}")
#             self.mock_mode = True
    
#     def extract_receipt_data(self, ocr_text: str) -> Dict[str, Any]:
#         """
#         Extract structured data from OCR text using LLM
#         Returns: merchant, date, amount, items, etc.
#         """
#         if self.mock_mode:
#             return self._mock_extraction(ocr_text)
        
#         prompt_template = ChatPromptTemplate.from_messages([
#             ("system", """You are a receipt data extraction expert. 
#             Extract structured information from receipt text.
#             Return ONLY valid JSON with these fields:
#             - merchant_name: string (store name)
#             - purchase_date: string (YYYY-MM-DD format)
#             - total_amount: float (numeric only)
#             - currency: string (USD, EUR, etc.)
#             - items: array of objects with name and price
#             - payment_method: string (if mentioned)
            
#             If field not found, use null. Do not add explanations."""),
#             ("human", "Extract data from this receipt text:\n\n{receipt_text}")
#         ])
        
#         parser = JsonOutputParser()
#         chain = prompt_template | self.llm | parser
        
#         try:
#             result = chain.invoke({"receipt_text": ocr_text[:3000]})  # Limit text
#             logger.info("Receipt data extracted successfully")
#             return result
#         except Exception as e:
#             logger.error(f"LLM extraction failed: {str(e)}")
#             return self._mock_extraction(ocr_text)
    
#     def calculate_store_policy(self, merchant_name: str) -> Dict[str, int]:
#         """
#         Get return/warranty policy based on merchant
#         Returns days for return window and warranty
#         """
#         if self.mock_mode:
#             return {"return_days": 30, "warranty_months": 12}
        
#         prompt_template = ChatPromptTemplate.from_messages([
#             ("system", """You know store return policies. 
#             Return ONLY JSON: {{"return_days": number, "warranty_months": number}}
#             Common policies:
#             - Electronics stores: 30 days return, 12 months warranty
#             - Clothing stores: 60 days return, 0 months warranty
#             - Grocery stores: 7 days return, 0 months warranty
#             - Amazon: 30 days return, varies warranty
#             - Best Buy: 15-30 days return, 12 months warranty
#             - Walmart: 90 days return, varies warranty"""),
#             ("human", "What is the return policy for: {merchant}?")
#         ])
        
#         parser = JsonOutputParser()
#         chain = prompt_template | self.llm | parser
        
#         try:
#             result = chain.invoke({"merchant": merchant_name})
#             return result
#         except Exception as e:
#             logger.error(f"Policy lookup failed: {str(e)}")
#             return {"return_days": 30, "warranty_months": 12}  # Default
    
#     def _mock_extraction(self, ocr_text: str) -> Dict[str, Any]:
#         """Mock extraction for testing without API key"""
#         import re
        
#         # Simple regex fallback
#         amount_match = re.search(r'\$?(\d+\.\d{2})', ocr_text)
#         date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', ocr_text)
        
#         return {
#             "merchant_name": "Unknown Store",
#             "purchase_date": date_match.group(0) if date_match else None,
#             "total_amount": float(amount_match.group(1)) if amount_match else 0.0,
#             "currency": "USD",
#             "items": [],
#             "payment_method": None
#         }

# # Singleton instance
# hf_service = HuggingFaceService()

"""
Hugging Face LLM Service - Free Inference API
With robust fallback for when API fails
"""
import os
import re
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class HuggingFaceService:
    """Free Hugging Face Inference API Service with Fallback"""
    
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        self.model_name = os.getenv("HF_MODEL_NAME", "microsoft/Phi-3-mini-4k-instruct")
        
        # Check if API key is properly configured
        if not self.api_key or self.api_key == "hf_your_free_token_here" or len(self.api_key) < 20:
            logger.warning("⚠️ Hugging Face API key not configured. Using OCR fallback mode.")
            self.api_enabled = False
        else:
            self.api_enabled = True
            logger.info(f" Hugging Face API enabled with model: {self.model_name}")
    
    def extract_receipt_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extract structured data from OCR text
        Falls back to regex extraction if LLM fails
        """
        if self.api_enabled:
            try:
                result = self._extract_with_llm(ocr_text)
                if result and result.get("merchant_name"):
                    logger.info(" LLM extraction successful")
                    return result
                else:
                    logger.warning("LLM returned empty result, using fallback")
            except Exception as e:
                logger.warning(f"LLM extraction failed: {str(e)}. Using fallback.")
        
        # Fallback to regex extraction
        logger.info("Using regex fallback for data extraction")
        return self._extract_with_regex(ocr_text)
    
    def _extract_with_llm(self, ocr_text: str) -> Dict[str, Any]:
        """Extract using Hugging Face LLM"""
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            
            llm = HuggingFaceEndpoint(
                repo_id=self.model_name,
                huggingfacehub_api_token=self.api_key,
                task="text-generation",
                max_new_tokens=512,
                temperature=0.1,
                timeout=30,
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Extract receipt data as JSON only. Fields: merchant_name, purchase_date (YYYY-MM-DD), total_amount (number), currency. Return ONLY valid JSON, no explanations."""),
                ("human", "Extract from this receipt:\n\n{receipt_text}")
            ])
            
            parser = JsonOutputParser()
            chain = prompt | llm | parser
            
            result = chain.invoke({"receipt_text": ocr_text[:2000]})
            
            # Validate result
            if not isinstance(result, dict):
                raise ValueError("Invalid result format")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction error: {str(e)}")
            raise
    
    def _extract_with_regex(self, ocr_text: str) -> Dict[str, Any]:
        """Fallback regex-based extraction (works without API)"""
        logger.info("Extracting with regex fallback...")
        
        data = {
            "merchant_name": "Unknown Store",
            "purchase_date": None,
            "total_amount": 0.0,
            "currency": "USD",
            "items": [],
            "payment_method": None
        }
        
        # Extract merchant name (first line usually)
        lines = ocr_text.strip().split('\n')
        if lines:
            # Take first non-empty line as merchant
            for line in lines:
                line = line.strip()
                if line and len(line) > 2 and len(line) < 50:
                    # Skip common receipt words
                    if not any(word in line.lower() for word in ['total', 'date', 'time', 'receipt', 'thank', 'phone', 'www']):
                        data["merchant_name"] = line
                        break
        
        # Extract date (multiple formats)
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',      # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}-\d{2}-\d{2})',             # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',             # DD-MM-YYYY
            r'([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})'  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, ocr_text)
            if match:
                data["purchase_date"] = match.group(0)
                break
        
        # Extract total amount (look for TOTAL, Balance, etc.)
        amount_patterns = [
            r'[Tt]otal[:\s]*\$?(\d+\.?\d*)',
            r'[Bb]alance[:\s]*\$?(\d+\.?\d*)',
            r'[Aa]mount[:\s]*\$?(\d+\.?\d*)',
            r'\$(\d+\.\d{2})\s*(?:USD|EUR|GBP)?',
            r'(\d+\.\d{2})\s*(?:USD|EUR|GBP)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, ocr_text)
            if match:
                try:
                    amount = float(match.group(1))
                    if amount > 0:  # Valid amount
                        data["total_amount"] = amount
                        break
                except:
                    pass
        
        # Extract currency
        if 'EUR' in ocr_text:
            data["currency"] = "EUR"
        elif 'GBP' in ocr_text:
            data["currency"] = "GBP"
        elif 'CAD' in ocr_text:
            data["currency"] = "CAD"
        else:
            data["currency"] = "USD"
        
        logger.info(f"Regex extraction complete: {data['merchant_name']}, ${data['total_amount']}")
        return data
    
    def calculate_store_policy(self, merchant_name: str) -> Dict[str, int]:
        """
        Get return/warranty policy based on merchant
        Uses rule-based lookup (no LLM needed for this)
        """
        if not merchant_name:
            return {"return_days": 30, "warranty_months": 12}
        
        merchant_lower = merchant_name.lower()
        
        # Rule-based policy lookup (more reliable than LLM)
        policy_rules = [
            (["electronics", "best buy", "micro center"], {"return_days": 15, "warranty_months": 12}),
            (["apple", "samsung", "sony", "lg"], {"return_days": 14, "warranty_months": 12}),
            (["amazon"], {"return_days": 30, "warranty_months": 12}),
            (["walmart", "target", "costco"], {"return_days": 90, "warranty_months": 12}),
            (["home depot", "lowes", "menards"], {"return_days": 90, "warranty_months": 12}),
            (["ikea", "wayfair"], {"return_days": 365, "warranty_months": 12}),
            (["nike", "adidas", "foot locker"], {"return_days": 60, "warranty_months": 6}),
            (["macys", "nordstrom", "kohls"], {"return_days": 90, "warranty_months": 6}),
            (["grocery", "whole foods", "trader joe"], {"return_days": 7, "warranty_months": 0}),
            (["restaurant", "cafe", "starbucks"], {"return_days": 0, "warranty_months": 0}),
        ]
        
        for keywords, policy in policy_rules:
            if any(keyword in merchant_lower for keyword in keywords):
                logger.info(f"Policy matched for {merchant_name}: {policy}")
                return policy
        
        # Default policy
        return {"return_days": 30, "warranty_months": 12}

# Singleton instance
hf_service = HuggingFaceService()