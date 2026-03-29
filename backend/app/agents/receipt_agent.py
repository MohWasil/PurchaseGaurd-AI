"""
LangGraph AI Agent - Receipt Processing Workflow
With robust error handling
"""
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta, timezone
import logging

from app.core.ocr_service import ocr_service
from app.core.llm_service import hf_service

logger = logging.getLogger(__name__)

class ReceiptState(TypedDict):
    """Agent state for receipt processing"""
    image_path: Optional[str]
    image_bytes: Optional[bytes]
    ocr_text: str
    extracted_data: Dict[str, Any]
    store_policy: Dict[str, int]
    deadlines: Dict[str, Any]
    alerts: List[Dict[str, str]]
    errors: List[str]

def parse_receipt_node(state: ReceiptState) -> ReceiptState:
    """Node 1: Extract text from receipt image using OCR"""
    try:
        if state.get("image_bytes"):
            ocr_text = ocr_service.extract_text_from_bytes(state["image_bytes"])
        elif state.get("image_path"):
            ocr_text = ocr_service.extract_text_from_image(state["image_path"])
        else:
            state["errors"].append("No image provided")
            return state
        
        if not ocr_text or len(ocr_text.strip()) < 5:
            state["errors"].append("OCR returned empty or invalid text")
            return state
        
        state["ocr_text"] = ocr_text
        logger.info(f" OCR completed: {len(ocr_text)} characters")
        return state
    except Exception as e:
        error_msg = f"OCR failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state

def extract_data_node(state: ReceiptState) -> ReceiptState:
    """Node 2: Extract structured data using LLM or fallback"""
    if not state.get("ocr_text"):
        state["errors"].append("No OCR text to process")
        # Set default data so upload can continue
        state["extracted_data"] = {
            "merchant_name": "Unknown Store",
            "purchase_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_amount": 0.0,
            "currency": "USD"
        }
        return state
    
    try:
        extracted = hf_service.extract_receipt_data(state["ocr_text"])
        
        # Validate extracted data
        if not extracted:
            raise ValueError("Empty extraction result")
        
        state["extracted_data"] = extracted
        logger.info(" Data extraction completed")
        return state
    except Exception as e:
        error_msg = f"Data extraction failed: {str(e)}"
        logger.warning(error_msg)
        state["errors"].append(error_msg)
        
        # Set fallback data so upload can continue
        state["extracted_data"] = {
            "merchant_name": "Unknown Store",
            "purchase_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_amount": 0.0,
            "currency": "USD"
        }
        return state

def get_policy_node(state: ReceiptState) -> ReceiptState:
    """Node 3: Get store return/warranty policy"""
    try:
        merchant = state.get("extracted_data", {}).get("merchant_name", "Unknown")
        policy = hf_service.calculate_store_policy(merchant)
        state["store_policy"] = policy
        logger.info(f" Store policy retrieved: {policy}")
        return state
    except Exception as e:
        error_msg = f"Policy lookup failed: {str(e)}"
        logger.warning(error_msg)
        state["errors"].append(error_msg)
        # Default policy
        state["store_policy"] = {"return_days": 30, "warranty_months": 12}
        return state

def calculate_deadlines_node(state: ReceiptState) -> ReceiptState:
    """Node 4: Calculate return deadline and warranty expiry"""
    try:
        extracted = state.get("extracted_data", {})
        policy = state.get("store_policy", {"return_days": 30, "warranty_months": 12})
        
        # Parse purchase date
        purchase_date_str = extracted.get("purchase_date")
        purchase_date = datetime.now(timezone.utc)  
        
        if purchase_date_str:
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"]:
                try:
                    purchase_date = datetime.strptime(str(purchase_date_str), fmt)
                    break
                except (ValueError, TypeError):
                    continue
        
        # Calculate deadlines
        return_days = policy.get("return_days", 30)
        warranty_months = policy.get("warranty_months", 12)
        
        return_deadline = purchase_date + timedelta(days=return_days)
        warranty_expiry = purchase_date + timedelta(days=warranty_months * 30)
        
        state["deadlines"] = {
            "purchase_date": purchase_date,
            "return_deadline": return_deadline,
            "warranty_expiry": warranty_expiry
        }
        
        logger.info(f" Deadlines calculated: return={return_deadline}, warranty={warranty_expiry}")
        return state
    except Exception as e:
        error_msg = f"Deadline calculation failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        
        # Default deadlines
        now = datetime.now(timezone.utc)
        state["deadlines"] = {
            "purchase_date": now,
            "return_deadline": now + timedelta(days=30),
            "warranty_expiry": now + timedelta(days=365)
        }
        return state

def generate_alerts_node(state: ReceiptState) -> ReceiptState:
    """Node 5: Generate alerts for user"""
    try:
        deadlines = state.get("deadlines", {})
        extracted = state.get("extracted_data", {})
        
        alerts = []
        
        # Return deadline alert
        return_deadline = deadlines.get("return_deadline")
        if return_deadline:
            alerts.append({
                "type": "return_deadline",
                "message": f"Return deadline: {return_deadline.strftime('%Y-%m-%d')}",
                "priority": "high"
            })
        
        # Warranty expiry alert
        warranty_expiry = deadlines.get("warranty_expiry")
        if warranty_expiry:
            alerts.append({
                "type": "warranty_expiry",
                "message": f"Warranty expires: {warranty_expiry.strftime('%Y-%m-%d')}",
                "priority": "medium"
            })
        
        # Amount alert
        amount = extracted.get("total_amount", 0)
        if amount and float(amount) > 500:
            alerts.append({
                "type": "high_value",
                "message": f"High value purchase: ${float(amount):.2f} - keep receipt safe!",
                "priority": "high"
            })
        
        state["alerts"] = alerts
        logger.info(f" Generated {len(alerts)} alerts")
        return state
    except Exception as e:
        error_msg = f"Alert generation failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["alerts"] = []
        return state

def build_receipt_agent() -> StateGraph:
    """Build the LangGraph workflow"""
    workflow = StateGraph(ReceiptState)
    
    workflow.add_node("parse_receipt", parse_receipt_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("get_policy", get_policy_node)
    workflow.add_node("calculate_deadlines", calculate_deadlines_node)
    workflow.add_node("generate_alerts", generate_alerts_node)
    
    workflow.set_entry_point("parse_receipt")
    workflow.add_edge("parse_receipt", "extract_data")
    workflow.add_edge("extract_data", "get_policy")
    workflow.add_edge("get_policy", "calculate_deadlines")
    workflow.add_edge("calculate_deadlines", "generate_alerts")
    workflow.add_edge("generate_alerts", END)
    
    return workflow.compile()

receipt_agent = build_receipt_agent()
