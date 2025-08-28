from fastapi import APIRouter

router = APIRouter(prefix="/emails", tags=["email management"])

@router.post("/send-email")
async def send_email():
    # Mock email sending
    return {
        "message": "Email sent successfully", 
        "email_id": "email_123", 
        "recipient": "user@example.com"
    }

@router.post("/scheduled-email/{recipient_email}")
async def send_scheduled_email(recipient_email: str):
    # Mock scheduled email sending
    return {
        "message": "Scheduled email sent successfully", 
        "email_id": "email_456", 
        "recipient": recipient_email,
        "scheduled_time": "2024-02-01T09:00:00"
    }