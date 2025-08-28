from fastapi import APIRouter

router = APIRouter(prefix="/bots", tags=["bot management"])

@router.post("/create-bot")
async def create_bot():
    # Mock bot creation
    return {
        "message": "Bot created successfully", 
        "bot_id": "bot_123", 
        "name": "Invoice Bot", 
        "status": "active"
    }

@router.get("/get-bots")
async def get_bots():
    # Mock get all bots
    return {"bots": [
        {
            "id": "bot_1", 
            "name": "Invoice Bot", 
            "type": "invoice_processor", 
            "status": "active"
        },
        {
            "id": "bot_2", 
            "name": "Reminder Bot", 
            "type": "scheduler", 
            "status": "inactive"
        }
    ]}