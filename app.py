from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
import uvicorn
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Optional
import json

# Import validation utilities
from validators import (
    validate_phone_number, validate_email, validate_budget, validate_name,
    extract_location, extract_property_type, calculate_lead_score
)

load_dotenv()

app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# In-memory storage (replace with database for production)
conversations = {}
conversation_states = {}

# Enhanced system prompt for natural, professional sales conversations
SYSTEM_PROMPT = """You are Aisha, a warm and professional real estate consultant for a premium Dubai-based real estate company. You're having a natural WhatsApp conversation with a potential client.

🎯 YOUR PERSONALITY:
- Warm, friendly, and genuinely helpful (like a trusted friend who happens to be a real estate expert)
- Professional but conversational (not robotic or scripted)
- Enthusiastic about helping people find their dream property
- Patient and understanding when clients need clarification
- Use natural language, occasional emojis (sparingly and professionally), and conversational phrases

💼 YOUR ROLE & GOALS:
1. Build genuine rapport and trust
2. Understand the client's needs deeply (not just collect data)
3. Qualify leads by gathering: name, budget, location preference, property type, contact details
4. Create urgency naturally (limited inventory, hot market, exclusive opportunities)
5. Schedule appointments or next steps
6. Handle objections gracefully

🗣️ CONVERSATION STYLE:
- Use natural greetings: "Hey there! 👋", "Great to hear from you!", "Thanks for reaching out!"
- Ask questions conversationally: "What brings you to Dubai's property market?" instead of "What is your requirement?"
- Show active listening: "Got it, so you're looking for...", "That makes sense!", "I understand..."
- Use encouraging language: "Perfect!", "Excellent choice!", "You're going to love..."
- Avoid robotic phrases like "Please provide", "Kindly share", "As per your request"

📋 INFORMATION GATHERING (Natural Flow):
When you need information, ask naturally and explain WHY:

❌ DON'T: "Please provide your budget"
✅ DO: "To show you the best options that match what you're looking for, what budget range works for you? Are we talking around 1-2 million AED, or perhaps a different range?"

❌ DON'T: "Invalid phone number. Please provide a valid number."
✅ DO: "I'd love to send you some amazing property listings! Could you share your WhatsApp number with the country code? Something like +971 50 123 4567 😊"

❌ DON'T: "What is your name?"
✅ DO: "By the way, I don't think I caught your name! What should I call you?"

🔄 HANDLING INVALID INPUTS:
When someone gives invalid information (like "123423" for a phone number):
- Stay positive and helpful
- Gently guide them to the correct format
- Give examples
- Never say "invalid" or "error" - instead say things like "Just to make sure I can reach you..." or "Let me get that right..."

Example for invalid phone:
"Just to make sure I can reach you on WhatsApp, could you share your number with the country code? For example: +971 50 123 4567"

Example for unclear budget:
"I want to make sure I show you properties in the right range! Are you thinking more like 500K, 1 million, or perhaps 2 million AED? Just a ballpark is fine! 😊"

🎯 SALES TECHNIQUES (Natural Application):
- Create FOMO naturally: "We actually just got 3 new listings in Marina this morning!"
- Build urgency: "The market is really hot right now, especially in that area"
- Social proof: "I've helped several families find their perfect home in JBR recently"
- Assume the sale: "When would you like to view some properties?" (not "Would you like to view?")
- Trial close: "If we find the perfect place within your budget, how soon are you looking to move?"

🚫 IMPORTANT RULES:
1. NEVER use markdown formatting (no **, __, etc.) - WhatsApp doesn't render it well
2. Keep messages concise (2-4 sentences usually) - this is WhatsApp, not email
3. Don't overwhelm with too many questions at once
4. If you don't have information, be honest and offer to connect them with a specialist
5. Always end with a clear next step or question
6. Remember everything from the conversation - show you're paying attention

🎭 OBJECTION HANDLING:
- "Just browsing": "No pressure at all! I'm here whenever you're ready. Mind if I ask what type of property catches your eye? Just curious! 😊"
- "Too expensive": "I totally get it! Let me show you some incredible options that offer amazing value. What's your comfortable range?"
- "Need to think": "Of course! Take your time. Would it help if I sent you some options to look at while you think it over?"
- "Working with another agent": "That's great! If you'd like a second opinion or want to see what else is out there, I'm happy to help. No obligations!"
- "Not interested right now": "I understand! The timing has to be right. Would it be okay if I check in with you in a few weeks? The market moves fast here!"
- "Too busy": "I completely get it! How about I send you a quick summary of what's available, and you can look when you have a moment? No rush!"
- "Just want information": "Perfect! I love helping people learn about the market. What specific information would be most helpful for you right now?"

💡 CONTEXT AWARENESS:
- If it's their first message: Warm welcome, build rapport
- If continuing conversation: Reference previous discussion, show continuity
- If they've been qualified: Focus on scheduling and next steps
- If they're hesitant: Address concerns, provide value, reduce pressure

Remember: You're not a form-filling robot. You're a skilled sales professional having a genuine conversation. Be human, be helpful, be yourself! 🌟"""

def get_conversation_state(phone_number: str) -> Dict:
    """Get or create conversation state for a phone number"""
    if phone_number not in conversation_states:
        conversation_states[phone_number] = {
            "stage": "greeting",  # greeting, qualifying, scheduling, completed
            "lead_data": {
                "name": None,
                "phone": None,
                "email": None,
                "budget": None,
                "location_preference": None,
                "property_type": None,
                "validated_fields": []
            },
            "retry_count": {},
            "lead_score": 0,
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }
    return conversation_states[phone_number]

def update_conversation_state(phone_number: str, updates: Dict):
    """Update conversation state"""
    state = get_conversation_state(phone_number)
    state.update(updates)
    state["last_activity"] = datetime.now().isoformat()
    conversation_states[phone_number] = state

def get_conversation_history(phone_number: str, limit: int = 10):
    """Get recent conversation history for a phone number"""
    if phone_number not in conversations:
        conversations[phone_number] = []
    return conversations[phone_number][-limit:]

def save_message(phone_number: str, role: str, content: str):
    """Save a message to conversation history"""
    if phone_number not in conversations:
        conversations[phone_number] = []
    conversations[phone_number].append({
        "role": role, 
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

def process_user_input(phone_number: str, user_message: str) -> Dict:
    """
    Process user input and extract/validate information
    Returns dict with extracted and validated data
    """
    state = get_conversation_state(phone_number)
    lead_data = state["lead_data"]
    extracted_data = {}
    
    # Try to extract and validate different types of information
    
    # 1. Name validation (if asking for name or seems like a name)
    if not lead_data.get("name"):
        # Check if message looks like a name (short, no special chars, etc.)
        if len(user_message.split()) <= 4 and len(user_message) < 50:
            name_result = validate_name(user_message)
            if name_result.is_valid:
                extracted_data["name"] = name_result.value
                lead_data["validated_fields"].append("name")
    
    # 2. Phone number validation
    phone_result = validate_phone_number(user_message)
    if phone_result.is_valid:
        extracted_data["phone"] = phone_result.value
        lead_data["validated_fields"].append("phone")
    
    # 3. Email validation
    email_result = validate_email(user_message)
    if email_result.is_valid:
        extracted_data["email"] = email_result.value
        lead_data["validated_fields"].append("email")
    
    # 4. Budget validation
    budget_result = validate_budget(user_message)
    if budget_result.is_valid:
        extracted_data["budget"] = budget_result.value
        lead_data["validated_fields"].append("budget")
    
    # 5. Location extraction
    location = extract_location(user_message)
    if location:
        extracted_data["location_preference"] = location
    
    # 6. Property type extraction
    property_type = extract_property_type(user_message)
    if property_type:
        extracted_data["property_type"] = property_type
    
    # Update lead data with extracted information
    for key, value in extracted_data.items():
        if value:
            lead_data[key] = value
    
    # Calculate lead score
    lead_score = calculate_lead_score(lead_data)
    
    return {
        "extracted_data": extracted_data,
        "lead_data": lead_data,
        "lead_score": lead_score
    }

def build_context_message(phone_number: str) -> str:
    """
    Build a context message for the AI about the current conversation state
    This helps the AI understand what information has been collected
    """
    state = get_conversation_state(phone_number)
    lead_data = state["lead_data"]
    
    context_parts = ["\n--- INTERNAL CONTEXT (User cannot see this) ---"]
    context_parts.append(f"Conversation Stage: {state['stage']}")
    context_parts.append(f"Message Count: {state['message_count']}")
    context_parts.append(f"Lead Score: {state['lead_score']}/100")
    
    context_parts.append("\nCollected Information:")
    for field, value in lead_data.items():
        if field != "validated_fields" and value:
            context_parts.append(f"  ✓ {field}: {value}")
    
    missing_fields = []
    if not lead_data.get("name"):
        missing_fields.append("name")
    if not lead_data.get("phone"):
        missing_fields.append("phone number")
    if not lead_data.get("budget"):
        missing_fields.append("budget")
    if not lead_data.get("location_preference"):
        missing_fields.append("location preference")
    
    if missing_fields:
        context_parts.append(f"\nStill need to collect: {', '.join(missing_fields)}")
    
    context_parts.append("\nNext steps: Continue natural conversation and gather missing info organically.")
    context_parts.append("--- END INTERNAL CONTEXT ---\n")
    
    return "\n".join(context_parts)

def get_ai_response(phone_number: str, user_message: str) -> str:
    """Get AI response using GPT-4o with enhanced context"""
    try:
        # Process user input and extract data
        processing_result = process_user_input(phone_number, user_message)
        
        # Save user message
        save_message(phone_number, "user", user_message)
        
        # Update conversation state
        state = get_conversation_state(phone_number)
        state["message_count"] += 1
        state["lead_data"] = processing_result["lead_data"]
        state["lead_score"] = processing_result["lead_score"]
        
        # Update stage based on progress
        if state["lead_score"] >= 80:
            state["stage"] = "scheduling"
        elif state["lead_score"] >= 40:
            state["stage"] = "qualifying"
        
        update_conversation_state(phone_number, state)
        
        # Get conversation history
        history = get_conversation_history(phone_number)
        
        # Build context message for AI
        context_message = build_context_message(phone_number)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": context_message}
        ]
        messages.extend(history)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.8,  # Higher temperature for more natural, varied responses
            max_tokens=300,   # Shorter responses for WhatsApp
            presence_penalty=0.6,  # Encourage diverse responses
            frequency_penalty=0.3  # Reduce repetition
        )
        
        ai_message = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting that might have slipped through
        ai_message = ai_message.replace('**', '').replace('__', '').replace('*', '')
        
        # Save AI response
        save_message(phone_number, "assistant", ai_message)
        
        # Log lead data for high-score leads
        if state["lead_score"] >= 70:
            print(f"\n🌟 HIGH-QUALITY LEAD DETECTED (Score: {state['lead_score']})")
            print(f"Lead Data: {json.dumps(state['lead_data'], indent=2)}\n")
        
        return ai_message
    
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "I apologize, I'm having a brief technical moment! 😅 Could you send that again? I want to make sure I don't miss anything important!"

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(None)
):
    """Handle incoming WhatsApp messages from Twilio"""
    
    user_message = Body.strip()
    phone_number = From  # Format: whatsapp:+1234567890
    
    print(f"\n📱 Message from {phone_number}: {user_message}")
    
    # Get AI response
    ai_response = get_ai_response(phone_number, user_message)
    
    print(f"🤖 Response: {ai_response}\n")
    
    # Create TwiML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{ai_response}</Message>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Professional WhatsApp Sales Agent is running",
        "model": "GPT-4o",
        "features": [
            "Natural conversation flow",
            "Input validation (phone, email, budget)",
            "Lead qualification & scoring",
            "Intelligent retry logic"
        ]
    }

@app.get("/conversations/{phone_number}")
async def get_conversation(phone_number: str):
    """View conversation history and state for a phone number (for debugging)"""
    full_phone = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number
    history = get_conversation_history(full_phone)
    state = get_conversation_state(full_phone)
    
    return {
        "phone_number": phone_number,
        "conversation_state": state,
        "messages": history
    }

@app.get("/leads")
async def get_all_leads():
    """Get all leads with their scores (for dashboard/CRM integration)"""
    leads = []
    for phone, state in conversation_states.items():
        if state["lead_score"] > 0:
            leads.append({
                "phone": phone,
                "score": state["lead_score"],
                "stage": state["stage"],
                "data": state["lead_data"],
                "last_activity": state["last_activity"],
                "message_count": state["message_count"]
            })
    
    # Sort by lead score (highest first)
    leads.sort(key=lambda x: x["score"], reverse=True)
    
    return {"total_leads": len(leads), "leads": leads}

@app.get("/leads/export")
async def export_leads_csv():
    """Export leads as CSV for CRM import"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Phone', 'Name', 'Email', 'Budget', 'Location', 'Property Type',
        'Lead Score', 'Stage', 'Message Count', 'Last Activity'
    ])
    
    # Write data
    for phone, state in conversation_states.items():
        if state["lead_score"] > 0:
            data = state["lead_data"]
            budget_str = ""
            if data.get("budget"):
                if data["budget"].get("type") == "range":
                    budget_str = f"{data['budget']['min']}-{data['budget']['max']} AED"
                else:
                    budget_str = f"{data['budget']['value']} AED"
            
            writer.writerow([
                phone,
                data.get('name', ''),
                data.get('email', ''),
                budget_str,
                data.get('location_preference', ''),
                data.get('property_type', ''),
                state['lead_score'],
                state['stage'],
                state['message_count'],
                state['last_activity']
            ])
    
    from fastapi.responses import StreamingResponse
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )

@app.get("/conversation-summary/{phone_number}")
async def get_conversation_summary(phone_number: str):
    """Get AI-generated summary of conversation for quick review"""
    full_phone = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number
    history = get_conversation_history(full_phone)
    state = get_conversation_state(full_phone)
    
    if not history:
        return {"error": "No conversation found"}
    
    # Create summary using AI
    try:
        summary_prompt = f"""Summarize this WhatsApp conversation between a real estate agent and a lead. 
        Focus on: key requirements, budget, timeline, objections, and next steps.
        
        Conversation:
        {json.dumps(history, indent=2)}
        
        Provide a concise 3-4 sentence summary."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        summary = response.choices[0].message.content.strip()
        
        return {
            "phone": phone_number,
            "lead_score": state["lead_score"],
            "stage": state["stage"],
            "summary": summary,
            "lead_data": state["lead_data"]
        }
    except Exception as e:
        return {"error": f"Could not generate summary: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Starting Professional WhatsApp Sales Agent...")
    print("✅ Natural conversation flow enabled")
    print("✅ Input validation active")
    print("✅ Lead scoring enabled")
    print("\nMake sure to set OPENAI_API_KEY in your .env file")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
