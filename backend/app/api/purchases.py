# """
# Purchase API - Receipt Upload & Management
# """
# from unittest import result
# from logging import Logger
# from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from datetime import datetime, timezone
# import os
# import uuid
# from typing import List

# from app.core.database import get_db
# from app.core.security import get_current_user, encrypt_sensitive_data
# from app.models.models import User, Purchase, Alert
# from app.schemas.schemas import PurchaseCreate, PurchaseResponse, AlertResponse
# from app.agents.receipt_agent import receipt_agent, ReceiptState

# router = APIRouter(prefix="/purchases", tags=["Purchases"])

# # Configuration
# UPLOAD_DIR = "data/receipts"
# MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
# ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# def validate_file(file: UploadFile) -> bool:
#     """Validate uploaded file"""
#     # Check extension
#     ext = os.path.splitext(file.filename or "")[1].lower()
#     if ext not in ALLOWED_EXTENSIONS:
#         return False
#     return True

# @router.post("/upload", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
# async def upload_receipt(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Upload receipt image and process with AI agent
#     """
#     # Validate file
#     if not validate_file(file):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
#         )
    
#     # Check file size
#     contents = await file.read()
#     if len(contents) > MAX_FILE_SIZE:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"File too large. Max: {MAX_FILE_SIZE // 1024 // 1024}MB"
#         )
    
#     # Generate unique filename
#     file_id = str(uuid.uuid4())
#     ext = os.path.splitext(file.filename or "")[1].lower()
#     filename = f"{file_id}{ext}"
#     filepath = os.path.join(UPLOAD_DIR, filename)
    
#     # Ensure upload directory exists
#     os.makedirs(UPLOAD_DIR, exist_ok=True)
    
#     # Save file
#     try:
#         with open(filepath, "wb") as f:
#             f.write(contents)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to save file: {str(e)}"
#         )
    
#     # Process with AI Agent
#     try:
#         initial_state: ReceiptState = {
#             "image_path": filepath,
#             "image_bytes": None,
#             "ocr_text": "",
#             "extracted_data": {},
#             "store_policy": {},
#             "deadlines": {},
#             "alerts": [],
#             "errors": []
#         }
        
#         result = await receipt_agent.ainvoke(initial_state)
        
#         if result.get("errors"):
#             # Still create purchase but note errors
#             print(f"Agent warnings: {result['errors']}")
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"AI processing failed: {str(e)}"
#         )
    
#     # Extract data for database
#     extracted = result.get("extracted_data", {})
#     deadlines = result.get("deadlines", {})
#     alerts = result.get("alerts", [])
    
#     # Create purchase record
#     purchase = Purchase(
#         user_id=current_user.id,
#         merchant_name=extracted.get("merchant_name", "Unknown"),
#         purchase_date=deadlines.get("purchase_date", datetime.utcnow()),
#         total_amount=extracted.get("total_amount", 0.0),
#         currency=extracted.get("currency", "USD"),
#         return_deadline=deadlines.get("return_deadline"),
#         warranty_expiry=deadlines.get("warranty_expiry"),
#         receipt_path=filepath,
#         encrypted_data=encrypt_sensitive_data(str(extracted))
#     )
    
#     db.add(purchase)
    
#     # Create alerts
#     for alert_data in alerts:
#         alert = Alert(
#             user_id=current_user.id,
#             purchase_id=purchase.id,  # Will be set after commit
#             alert_type=alert_data["type"],
#             message=alert_data["message"]
#         )
#         db.add(alert)
    
#     await db.commit()
#     await db.refresh(purchase)
    
#     # Update alert purchase_ids
#     result = await db.execute(select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.id.desc()).limit(len(alerts)))
#     for alert in result.scalars():
#         alert.purchase_id = purchase.id
    
#     await db.commit()
    
#     return purchase

# # @router.get("/", response_model=List[PurchaseResponse])
# # async def get_purchases(
# #     current_user: User = Depends(get_current_user),
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     """Get all purchases for current user"""
# #     result = await db.execute(
# #         select(Purchase)
# #         .where(Purchase.user_id == current_user.id)
# #         .order_by(Purchase.created_at.desc())
# #     )
# #     purchases = result.scalars().all()
# #     return purchases
# @router.get("/")
# async def get_purchases(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get all purchases for current user"""
#     try:
#         result = await db.execute(
#             select(Purchase)
#             .where(Purchase.user_id == current_user.id)
#             .order_by(Purchase.created_at.desc())
#         )
#         purchases = result.scalars().all()
        
#         # Convert to simple dict format
#         purchase_list = []
#         for p in purchases:
#             purchase_list.append({
#                 "id": p.id,
#                 "user_id": p.user_id,
#                 "merchant_name": p.merchant_name or "Unknown",
#                 "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
#                 "total_amount": float(p.total_amount or 0),
#                 "currency": p.currency or "USD",
#                 "return_deadline": p.return_deadline.isoformat() if p.return_deadline else None,
#                 "warranty_expiry": p.warranty_expiry.isoformat() if p.warranty_expiry else None,
#                 "is_returned": p.is_returned or False,
#                 "is_claimed": p.is_claimed or False,
#                 "created_at": p.created_at.isoformat() if p.created_at else None
#             })
        
#         return purchase_list
    
#     except Exception as e:
#         Logger.error(f"Get purchases error: {str(e)}")
#         return []




# @router.get("/{purchase_id}", response_model=PurchaseResponse)
# async def get_purchase(
#     purchase_id: int,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get specific purchase"""
#     result = await db.execute(
#         select(Purchase).where(
#             Purchase.id == purchase_id,
#             Purchase.user_id == current_user.id
#         )
#     )
#     purchase = result.scalar_one_or_none()
    
#     if not purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Purchase not found"
#         )
    
#     return purchase

# @router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_purchase(
#     purchase_id: int,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Delete purchase and associated receipt"""
#     result = await db.execute(
#         select(Purchase).where(
#             Purchase.id == purchase_id,
#             Purchase.user_id == current_user.id
#         )
#     )
#     purchase = result.scalar_one_or_none()
    
#     if not purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Purchase not found"
#         )
    
#     # Delete receipt file
#     if purchase.receipt_path and os.path.exists(purchase.receipt_path):
#         os.remove(purchase.receipt_path)
    
#     # Delete from database
#     await db.delete(purchase)
#     await db.commit()
    
#     return None

# # @router.get("/alerts", response_model=List[AlertResponse])
# # async def get_alerts(
# #     current_user: User = Depends(get_current_user),
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     """Get all alerts for current user"""
# #     result = await db.execute(
# #         select(Alert)
# #         .where(Alert.user_id == current_user.id)
# #         .order_by(Alert.created_at.desc())
# #     )
# #     alerts = result.scalars().all()
# #     return alerts

# @router.get("/alerts")
# async def get_alerts(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get all alerts for current user"""
#     try:
#         result = await db.execute(
#             select(Alert)
#             .where(Alert.user_id == current_user.id)
#             .order_by(Alert.created_at.desc())
#         )
#         alerts = result.scalars().all()
        
#         # Convert to simple dict (avoid Pydantic validation issues)
#         alert_list = []
#         for alert in alerts:
#             alert_list.append({
#                 "id": alert.id,
#                 "alert_type": alert.alert_type or "info",
#                 "message": alert.message or "",
#                 "is_sent": alert.is_sent or False,
#                 "priority": "high" if "return" in (alert.alert_type or "").lower() else "medium",
#                 "created_at": alert.created_at.isoformat() if alert.created_at else None
#             })
        
#         return alert_list
    
#     except Exception as e:
#         Logger.error(f"Alerts endpoint error: {str(e)}")
#         return []

# # ============== NEW ENDPOINTS FOR PHASE 3 ==============

# # @router.get("/stats", response_model=dict)
# # async def get_purchase_stats(
# #     current_user: User = Depends(get_current_user),
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     """Get purchase statistics for dashboard"""
# #     result = await db.execute(
# #         select(Purchase).where(Purchase.user_id == current_user.id)
# #     )
# #     purchases = result.scalars().all()
    
# #     if not purchases:
# #         return {
# #             "total_purchases": 0,
# #             "total_amount": 0,
# #             "avg_purchase": 0,
# #             "categories": {},
# #             "upcoming_returns": 0,
# #             "active_warranties": 0
# #         }
    
# #     total_amount = sum(p.total_amount for p in purchases)
    
# #     # Count upcoming returns (within 7 days)
# #     upcoming_returns = sum(
# #         1 for p in purchases 
# #         if p.return_deadline and 
# #         (p.return_deadline - datetime.utcnow()).days <= 7
# #     )
    
# #     # Count active warranties
# #     active_warranties = sum(
# #         1 for p in purchases 
# #         if p.warranty_expiry and 
# #         p.warranty_expiry > datetime.utcnow()
# #     )
    
# #     # Categorize purchases (simple keyword matching)
# #     categories = {}
# #     for purchase in purchases:
# #         merchant_lower = purchase.merchant_name.lower()
        
# #         if any(word in merchant_lower for word in ["electronics", "best buy", "apple", "samsung"]):
# #             cat = "Electronics"
# #         elif any(word in merchant_lower for word in ["clothing", "fashion", "nike", "adidas", "zara"]):
# #             cat = "Clothing"
# #         elif any(word in merchant_lower for word in ["grocery", "food", "restaurant", "walmart", "target"]):
# #             cat = "Groceries"
# #         elif any(word in merchant_lower for word in ["home", "furniture", "ikea"]):
# #             cat = "Home"
# #         else:
# #             cat = "Other"
        
# #         categories[cat] = categories.get(cat, 0) + 1
    
# #     return {
# #         "total_purchases": len(purchases),
# #         "total_amount": total_amount,
# #         "avg_purchase": total_amount / len(purchases) if purchases else 0,
# #         "categories": categories,
# #         "upcoming_returns": upcoming_returns,
# #         "active_warranties": active_warranties
# #     }


# @router.get("/stats")
# async def get_purchase_stats(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get purchase statistics for dashboard"""
#     try:
#         result = await db.execute(
#             select(Purchase).where(Purchase.user_id == current_user.id)
#         )
#         purchases = result.scalars().all()
        
#         if not purchases:
#             return {
#                 "total_purchases": 0,
#                 "total_amount": 0.0,
#                 "avg_purchase": 0.0,
#                 "categories": {},
#                 "upcoming_returns": 0,
#                 "active_warranties": 0
#             }
        
#         total_amount = sum(p.total_amount or 0 for p in purchases)
        
#         # Count upcoming returns (within 7 days)
#         now = datetime.now(timezone.utc)
#         upcoming_returns = 0
#         active_warranties = 0
        
#         for p in purchases:
#             if p.return_deadline:
#                 try:
#                     deadline = p.return_deadline
#                     if isinstance(deadline, str):
#                         deadline = datetime.fromisoformat(deadline.replace("Z", ""))
#                     if (deadline - now).days <= 7:
#                         upcoming_returns += 1
#                 except:
#                     pass
            
#             if p.warranty_expiry:
#                 try:
#                     expiry = p.warranty_expiry
#                     if isinstance(expiry, str):
#                         expiry = datetime.fromisoformat(expiry.replace("Z", ""))
#                     if expiry > now:
#                         active_warranties += 1
#                 except:
#                     pass
        
#         # Categorize purchases (simple keyword matching)
#         categories = {}
#         for purchase in purchases:
#             merchant_lower = (purchase.merchant_name or "unknown").lower()
            
#             if any(word in merchant_lower for word in ["electronics", "best buy", "apple", "samsung"]):
#                 cat = "Electronics"
#             elif any(word in merchant_lower for word in ["clothing", "fashion", "nike", "adidas", "zara"]):
#                 cat = "Clothing"
#             elif any(word in merchant_lower for word in ["grocery", "food", "restaurant", "walmart", "target"]):
#                 cat = "Groceries"
#             elif any(word in merchant_lower for word in ["home", "furniture", "ikea"]):
#                 cat = "Home"
#             else:
#                 cat = "Other"
            
#             categories[cat] = categories.get(cat, 0) + 1
        
#         return {
#             "total_purchases": len(purchases),
#             "total_amount": float(total_amount),
#             "avg_purchase": float(total_amount / len(purchases)) if purchases else 0.0,
#             "categories": categories,
#             "upcoming_returns": upcoming_returns,
#             "active_warranties": active_warranties
#         }
    
#     except Exception as e:        
#         Logger.error(f"Stats endpoint error: {str(e)}")
#         return {
#             "total_purchases": 0,
#             "total_amount": 0.0,
#             "avg_purchase": 0.0,
#             "categories": {},
#             "upcoming_returns": 0,
#             "active_warranties": 0
#         }


# @router.get("/export/csv")
# async def export_purchases_csv(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Export purchases as CSV"""
#     from io import StringIO
#     import csv
    
#     result = await db.execute(
#         select(Purchase).where(Purchase.user_id == current_user.id)
#     )
#     purchases = result.scalars().all()
    
#     output = StringIO()
#     writer = csv.writer(output)
    
#     # Header
#     writer.writerow([
#         "ID", "Merchant", "Date", "Amount", "Currency",
#         "Return Deadline", "Warranty Expiry", "Returned", "Claimed"
#     ])
    
#     # Data
#     for p in purchases:
#         writer.writerow([
#             p.id,
#             p.merchant_name,
#             p.purchase_date.strftime("%Y-%m-%d") if p.purchase_date else "",
#             p.total_amount,
#             p.currency,
#             p.return_deadline.strftime("%Y-%m-%d") if p.return_deadline else "",
#             p.warranty_expiry.strftime("%Y-%m-%d") if p.warranty_expiry else "",
#             p.is_returned,
#             p.is_claimed
#         ])
    
#     output.seek(0)
    
#     from fastapi.responses import StreamingResponse
#     return StreamingResponse(
#         iter([output.getvalue()]),
#         media_type="text/csv",
#         headers={"Content-Disposition": "attachment; filename=purchases.csv"}
#     )

# @router.patch("/{purchase_id}/return", response_model=PurchaseResponse)
# async def mark_as_returned(
#     purchase_id: int,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Mark purchase as returned"""
#     result = await db.execute(
#         select(Purchase).where(
#             Purchase.id == purchase_id,
#             Purchase.user_id == current_user.id
#         )
#     )
#     purchase = result.scalar_one_or_none()
    
#     if not purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Purchase not found"
#         )
    
#     purchase.is_returned = True
#     await db.commit()
#     await db.refresh(purchase)
    
#     return purchase

# @router.patch("/{purchase_id}/claim", response_model=PurchaseResponse)
# async def mark_as_claimed(
#     purchase_id: int,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Mark purchase as warranty claimed"""
#     result = await db.execute(
#         select(Purchase).where(
#             Purchase.id == purchase_id,
#             Purchase.user_id == current_user.id
#         )
#     )
#     purchase = result.scalar_one_or_none()
    
#     if not purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Purchase not found"
#         )
    
#     purchase.is_claimed = True
#     await db.commit()
#     await db.refresh(purchase)
    
#     return purchase




"""
Purchase API - Receipt Upload & Management
FINAL FIXED VERSION - Route Order Corrected
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import os
import uuid
from typing import List
import logging

from app.core.database import get_db
from app.core.security import get_current_user, encrypt_sensitive_data
from app.models.models import User, Purchase, Alert
from app.schemas.schemas import PurchaseCreate, PurchaseResponse, AlertResponse
from app.agents.receipt_agent import receipt_agent, ReceiptState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["Purchases"])

# Configuration
UPLOAD_DIR = "data/receipts"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    return True

# ============================================
# ✅ CRITICAL: ROUTE ORDER - SPECIFIC FIRST!
# ============================================
# All specific routes (/stats, /alerts, /export) MUST come BEFORE /{purchase_id}
# Otherwise FastAPI matches "stats" as purchase_id causing 422 errors!

# 1. UPLOAD RECEIPT (Your working code - KEEP AS IS)
@router.post("/upload", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload receipt image and process with AI agent"""
    # Validate file
    if not validate_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1].lower()
    filename = f"{file_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    try:
        with open(filepath, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Process with AI Agent
    try:
        initial_state: ReceiptState = {
            "image_path": filepath,
            "image_bytes": None,
            "ocr_text": "",
            "extracted_data": {},
            "store_policy": {},
            "deadlines": {},
            "alerts": [],
            "errors": []
        }
        
        result = await receipt_agent.ainvoke(initial_state)
        
        if result.get("errors"):
            # Still create purchase but note errors
            logger.warning(f"Agent warnings: {result['errors']}")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )
    
    # Extract data for database
    extracted = result.get("extracted_data", {})
    deadlines = result.get("deadlines", {})
    alerts = result.get("alerts", [])
    
    # Create purchase record
    purchase = Purchase(
        user_id=current_user.id,
        merchant_name=extracted.get("merchant_name", "Unknown"),
        purchase_date=deadlines.get("purchase_date", datetime.utcnow()),
        total_amount=extracted.get("total_amount", 0.0),
        currency=extracted.get("currency", "USD"),
        return_deadline=deadlines.get("return_deadline"),
        warranty_expiry=deadlines.get("warranty_expiry"),
        receipt_path=filepath,
        encrypted_data=encrypt_sensitive_data(str(extracted))
    )
    
    db.add(purchase)
    
    # Create alerts
    for alert_data in alerts:
        alert = Alert(
            user_id=current_user.id,
            purchase_id=purchase.id,
            alert_type=alert_data["type"],
            message=alert_data["message"]
        )
        db.add(alert)
    
    await db.commit()
    await db.refresh(purchase)
    
    # Update alert purchase_ids
    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.id.desc())
        .limit(len(alerts))
    )
    for alert in result.scalars():
        alert.purchase_id = purchase.id
    
    await db.commit()
    
    return purchase

# 2. STATS (BEFORE /{purchase_id}!) - NO response_model
@router.get("/stats")
async def get_purchase_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get purchase statistics for dashboard"""
    try:
        result = await db.execute(
            select(Purchase).where(Purchase.user_id == current_user.id)
        )
        purchases = result.scalars().all()
        
        if not purchases:
            return {
                "total_purchases": 0,
                "total_amount": 0.0,
                "avg_purchase": 0.0,
                "categories": {},
                "upcoming_returns": 0,
                "active_warranties": 0
            }
        
        total_amount = sum(p.total_amount or 0 for p in purchases)
        
        # Count upcoming returns (within 7 days)
        now = datetime.utcnow()
        upcoming_returns = 0
        active_warranties = 0
        
        for p in purchases:
            if p.return_deadline:
                try:
                    deadline = p.return_deadline
                    if isinstance(deadline, datetime):
                        if (deadline - now).days <= 7:
                            upcoming_returns += 1
                except:
                    pass
            
            if p.warranty_expiry:
                try:
                    expiry = p.warranty_expiry
                    if isinstance(expiry, datetime):
                        if expiry > now:
                            active_warranties += 1
                except:
                    pass
        
        # Categorize purchases (simple keyword matching)
        categories = {}
        for purchase in purchases:
            merchant_lower = (purchase.merchant_name or "unknown").lower()
            
            if any(word in merchant_lower for word in ["electronics", "best buy", "apple", "samsung"]):
                cat = "Electronics"
            elif any(word in merchant_lower for word in ["clothing", "fashion", "nike", "adidas", "zara"]):
                cat = "Clothing"
            elif any(word in merchant_lower for word in ["grocery", "food", "restaurant", "walmart", "target"]):
                cat = "Groceries"
            elif any(word in merchant_lower for word in ["home", "furniture", "ikea"]):
                cat = "Home"
            else:
                cat = "Other"
            
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_purchases": len(purchases),
            "total_amount": float(total_amount),
            "avg_purchase": float(total_amount / len(purchases)) if purchases else 0.0,
            "categories": categories,
            "upcoming_returns": upcoming_returns,
            "active_warranties": active_warranties
        }
    
    except Exception as e:
        logger.error(f"Stats endpoint error: {str(e)}")
        return {
            "total_purchases": 0,
            "total_amount": 0.0,
            "avg_purchase": 0.0,
            "categories": {},
            "upcoming_returns": 0,
            "active_warranties": 0
        }

# 3. ALERTS (BEFORE /{purchase_id}!) - NO response_model
@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts for current user"""
    try:
        result = await db.execute(
            select(Alert)
            .where(Alert.user_id == current_user.id)
            .order_by(Alert.created_at.desc())
        )
        alerts = result.scalars().all()
        
        # Convert to simple dict (avoid Pydantic validation issues)
        alert_list = []
        for alert in alerts:
            alert_list.append({
                "id": alert.id,
                "alert_type": alert.alert_type or "info",
                "message": alert.message or "",
                "is_sent": alert.is_sent or False,
                "priority": "high" if "return" in (alert.alert_type or "").lower() else "medium",
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
        
        return alert_list
    
    except Exception as e:
        logger.error(f"Alerts endpoint error: {str(e)}")
        return []

# 4. EXPORT CSV (BEFORE /{purchase_id}!)
@router.get("/export/csv")
async def export_purchases_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export purchases as CSV"""
    from io import StringIO
    import csv
    from fastapi.responses import StreamingResponse
    
    result = await db.execute(
        select(Purchase).where(Purchase.user_id == current_user.id)
    )
    purchases = result.scalars().all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Merchant", "Date", "Amount", "Currency",
        "Return Deadline", "Warranty Expiry", "Returned", "Claimed"
    ])
    
    # Data
    for p in purchases:
        writer.writerow([
            p.id,
            p.merchant_name,
            p.purchase_date.strftime("%Y-%m-%d") if p.purchase_date else "",
            p.total_amount,
            p.currency,
            p.return_deadline.strftime("%Y-%m-%d") if p.return_deadline else "",
            p.warranty_expiry.strftime("%Y-%m-%d") if p.warranty_expiry else "",
            p.is_returned,
            p.is_claimed
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=purchases.csv"}
    )

# 5. ALL PURCHASES (BEFORE /{purchase_id}!) - NO response_model
@router.get("/")
async def get_purchases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all purchases for current user"""
    try:
        result = await db.execute(
            select(Purchase)
            .where(Purchase.user_id == current_user.id)
            .order_by(Purchase.created_at.desc())
        )
        purchases = result.scalars().all()
        
        # Convert to simple dict format
        purchase_list = []
        for p in purchases:
            purchase_list.append({
                "id": p.id,
                "user_id": p.user_id,
                "merchant_name": p.merchant_name or "Unknown",
                "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
                "total_amount": float(p.total_amount or 0),
                "currency": p.currency or "USD",
                "return_deadline": p.return_deadline.isoformat() if p.return_deadline else None,
                "warranty_expiry": p.warranty_expiry.isoformat() if p.warranty_expiry else None,
                "is_returned": p.is_returned or False,
                "is_claimed": p.is_claimed or False,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        
        return purchase_list
    
    except Exception as e:
        logger.error(f"Get purchases error: {str(e)}")
        return []

# ============================================
# ⚠️ GENERIC ROUTES WITH {purchase_id} - MUST BE LAST!
# ============================================

# 6. SINGLE PURCHASE (LAST!)
@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific purchase"""
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id,
            Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    return purchase

# 7. DELETE (LAST!)
@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete purchase and associated receipt"""
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id,
            Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    # Delete receipt file
    if purchase.receipt_path and os.path.exists(purchase.receipt_path):
        os.remove(purchase.receipt_path)
    
    # Delete from database
    await db.delete(purchase)
    await db.commit()
    
    return None

# 8. PATCH ROUTES (LAST!)
@router.patch("/{purchase_id}/return", response_model=PurchaseResponse)
async def mark_as_returned(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark purchase as returned"""
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id,
            Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    purchase.is_returned = True
    await db.commit()
    await db.refresh(purchase)
    
    return purchase

@router.patch("/{purchase_id}/claim", response_model=PurchaseResponse)
async def mark_as_claimed(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark purchase as warranty claimed"""
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id,
            Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    purchase.is_claimed = True
    await db.commit()
    await db.refresh(purchase)
    
    return purchase
