"""
Email Service - SMTP (Free Gmail)
Send deadline alerts and notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    """Free SMTP Email Service"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "")
        self.send_enabled = os.getenv("SEND_EMAIL_ALERTS", "false").lower() == "true"
        
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("Email credentials not configured. Email sending disabled.")
            self.send_enabled = False
    
    def send_alert_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send alert email to user
        Returns True if sent successfully
        """
        if not self.send_enabled:
            logger.info("Email sending disabled. Skipping.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #2c3e50;">🛡️ PurchaseGuard Alert</h2>
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        {body.replace(chr(10), '<br>')}
                    </div>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        This is an automated alert from PurchaseGuard AI.<br>
                        Login to your dashboard to manage your purchases.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_return_deadline_alert(self, user_email: str, merchant: str, deadline: datetime, amount: float) -> bool:
        """Send return deadline warning email"""
        days_left = (deadline - datetime.now(timezone.utc)).days
        
        if days_left < 0:
            subject = f"⚠️ RETURN EXPIRED - {merchant}"
            body = f"""
            Your return window for {merchant} has EXPIRED.
            
            Purchase Amount: ${amount:.2f}
            Return Deadline: {deadline.strftime('%Y-%m-%d')}
            
            Contact the store immediately if you need to return this item.
            """
        elif days_left <= 3:
            subject = f"🔴 URGENT: Return Deadline in {days_left} days - {merchant}"
            body = f"""
            URGENT: Your return window expires soon!
            
            Merchant: {merchant}
            Purchase Amount: ${amount:.2f}
            Return Deadline: {deadline.strftime('%Y-%m-%d')}
            Days Remaining: {days_left}
            
            Act now to avoid losing your return option.
            """
        elif days_left <= 7:
            subject = f"🟡 Return Deadline in {days_left} days - {merchant}"
            body = f"""
            Reminder: Your return window is closing.
            
            Merchant: {merchant}
            Purchase Amount: ${amount:.2f}
            Return Deadline: {deadline.strftime('%Y-%m-%d')}
            Days Remaining: {days_left}
            """
        else:
            return False  # Too early to send
        
        return self.send_alert_email(user_email, subject, body)
    
    def send_warranty_expiry_alert(self, user_email: str, merchant: str, expiry: datetime, amount: float) -> bool:
        """Send warranty expiry warning email"""
        days_left = (expiry - datetime.now(timezone.utc)).days
        
        if days_left < 0:
            subject = f"⚠️ WARRANTY EXPIRED - {merchant}"
            body = f"""
            Your warranty for {merchant} has EXPIRED.
            
            Purchase Amount: ${amount:.2f}
            Warranty Expiry: {expiry.strftime('%Y-%m-%d')}
            
            Keep your receipt for future reference.
            """
        elif days_left <= 14:
            subject = f"🔴 Warranty Expiring in {days_left} days - {merchant}"
            body = f"""
            Your product warranty is expiring soon!
            
            Merchant: {merchant}
            Purchase Amount: ${amount:.2f}
            Warranty Expiry: {expiry.strftime('%Y-%m-%d')}
            Days Remaining: {days_left}
            
            Check your product for any issues before warranty expires.
            """
        else:
            return False  # Too early to send
        
        return self.send_alert_email(user_email, subject, body)
    
    def send_weekly_summary(self, user_email: str, purchases_count: int, total_amount: float, upcoming_deadlines: int) -> bool:
        """Send weekly summary email"""
        subject = f"📊 PurchaseGuard Weekly Summary - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""
        Your Weekly Purchase Summary
        
        📦 Total Purchases Tracked: {purchases_count}
        💰 Total Amount: ${total_amount:.2f}
        ⏰ Upcoming Deadlines: {upcoming_deadlines}
        
        Login to your dashboard for more details.
        
        Stay protected!
        🛡️ PurchaseGuard AI
        """
        
        return self.send_alert_email(user_email, subject, body)

# Singleton instance
email_service = EmailService()