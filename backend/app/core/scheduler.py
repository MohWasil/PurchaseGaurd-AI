"""
Scheduler - APScheduler
Run periodic tasks for deadline checking and email alerts
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv
import os
from app.core.database import async_session_maker
from app.core.email_service import email_service
from app.models.models import User, Purchase, Alert

load_dotenv()

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Background task scheduler for alerts"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.check_interval = int(os.getenv("ALERT_CHECK_INTERVAL_HOURS", "24"))
    
    async def check_deadlines_and_send_alerts(self):
        """
        Check all purchases for upcoming deadlines
        Send email alerts if needed
        """
        logger.info("Starting deadline check task...")
        
        try:
            async with async_session_maker() as db:
                # Get all active purchases with deadlines
                result = await db.execute(
                    select(Purchase).where(
                        Purchase.return_deadline != None,
                        Purchase.is_returned == False
                    )
                )
                purchases = result.scalars().all()
                
                alerts_created = 0
                
                for purchase in purchases:
                    # Get user info
                    user_result = await db.execute(
                        select(User).where(User.id == purchase.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    
                    if not user or not user.is_active:
                        continue
                    
                    # Check return deadline
                    if purchase.return_deadline:
                        days_until_return = (purchase.return_deadline - datetime.now(timezone.utc)).days
                        
                        if days_until_return <= 7:  # Alert within 7 days
                            # Create database alert
                            alert = Alert(
                                user_id=user.id,
                                purchase_id=purchase.id,
                                alert_type="return_deadline",
                                message=f"Return deadline for {purchase.merchant_name} in {days_until_return} days!"
                            )
                            db.add(alert)
                            alerts_created += 1
                            
                            # Send email
                            email_service.send_return_deadline_alert(
                                user_email=user.email,
                                merchant=purchase.merchant_name,
                                deadline=purchase.return_deadline,
                                amount=purchase.total_amount
                            )
                    
                    # Check warranty expiry
                    if purchase.warranty_expiry:
                        days_until_warranty = (purchase.warranty_expiry - datetime.now(timezone.utc)).days
                        
                        if days_until_warranty <= 14:  # Alert within 14 days
                            alert = Alert(
                                user_id=user.id,
                                purchase_id=purchase.id,
                                alert_type="warranty_expiry",
                                message=f"Warranty for {purchase.merchant_name} expires in {days_until_warranty} days!"
                            )
                            db.add(alert)
                            alerts_created += 1
                            
                            # Send email
                            email_service.send_warranty_expiry_alert(
                                user_email=user.email,
                                merchant=purchase.merchant_name,
                                expiry=purchase.warranty_expiry,
                                amount=purchase.total_amount
                            )
                
                await db.commit()
                logger.info(f"Deadline check complete. Created {alerts_created} alerts.")
                
        except Exception as e:
            logger.error(f"Deadline check failed: {str(e)}")
    
    async def send_weekly_summaries(self):
        """Send weekly summary emails to all users"""
        logger.info("Sending weekly summaries...")
        
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(User).where(User.is_active == True))
                users = result.scalars().all()
                
                for user in users:
                    # Get user's purchase stats
                    purchases_result = await db.execute(
                        select(Purchase).where(Purchase.user_id == user.id)
                    )
                    purchases = purchases_result.scalars().all()
                    
                    total_amount = sum(p.total_amount for p in purchases)
                    upcoming = sum(
                        1 for p in purchases 
                        if p.return_deadline and 
                        (p.return_deadline - datetime.now(timezone.utc)).days <= 7
                    )
                    
                    email_service.send_weekly_summary(
                        user_email=user.email,
                        purchases_count=len(purchases),
                        total_amount=total_amount,
                        upcoming_deadlines=upcoming
                    )
                
                logger.info(f"Weekly summaries sent to {len(users)} users.")
                
        except Exception as e:
            logger.error(f"Weekly summary failed: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        # Add deadline check job
        self.scheduler.add_job(
            self.check_deadlines_and_send_alerts,
            trigger=IntervalTrigger(hours=self.check_interval),
            id="deadline_check",
            replace_existing=True
        )
        
        # Add weekly summary job (every Monday 9 AM)
        # For simplicity, using interval here
        self.scheduler.add_job(
            self.send_weekly_summaries,
            trigger=IntervalTrigger(days=7),
            id="weekly_summary",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started. Checking deadlines every {self.check_interval} hours.")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()

# Singleton instance
scheduler = TaskScheduler()