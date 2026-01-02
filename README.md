# 🤖 Professional WhatsApp Sales Agent

A sophisticated AI-powered WhatsApp sales agent built with GPT-4o, designed specifically for real estate lead qualification and conversion. Features natural conversation flow, intelligent validation, and comprehensive lead management.

## ✨ Key Features

### 🗣️ Natural Conversation
- **Human-like interactions** - No robotic responses, uses conversational language
- **Context-aware** - Remembers entire conversation history
- **Personality-driven** - Warm, professional real estate consultant persona (Aisha)
- **Smart emojis** - Professional use of emojis for engagement

### ✅ Intelligent Validation
- **Phone Numbers** - Validates international formats, handles UAE numbers
- **Email Addresses** - RFC-compliant email validation
- **Budget Parsing** - Understands "500k", "1.5M", "2 million AED", ranges
- **Name Validation** - Filters invalid characters, proper capitalization
- **Retry Logic** - Asks again naturally when invalid input detected (max 2-3 attempts)

### 🎯 Sales Features
- **Lead Qualification** - Systematic collection of: name, budget, location, property type, contact
- **Lead Scoring** - Automatic scoring (0-100) based on information completeness
- **Objection Handling** - Pre-programmed responses for common objections
- **Urgency Creation** - Natural FOMO and urgency techniques
- **Appointment Scheduling** - Guides leads to book viewings

### 📊 CRM Integration Ready
- **Lead Dashboard** - View all leads with scores via API
- **CSV Export** - Export leads for CRM import (`/leads/export`)
- **Conversation Summaries** - AI-generated summaries of each conversation
- **Real-time Tracking** - Monitor conversations as they happen

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key
- Twilio Account (for WhatsApp)

### Installation

1. **Clone and setup**
```bash
cd whatsapp_lead_agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

4. **Run the agent**
```bash
python3 app.py
```

Server starts on `http://0.0.0.0:8000`

## 📱 Twilio WhatsApp Setup

1. **Get Twilio WhatsApp Sandbox**
   - Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Follow instructions to activate sandbox

2. **Configure Webhook**
   - In Twilio Console, set webhook URL to: `https://your-domain.com/webhook/whatsapp`
   - Use ngrok for local testing: `ngrok http 8000`

3. **Test**
   - Send a message to your Twilio WhatsApp number
   - Agent responds automatically!

## 🔌 API Endpoints

### Core Endpoints

#### `POST /webhook/whatsapp`
Receives WhatsApp messages from Twilio
- Processes user input
- Validates data
- Returns AI response

#### `GET /`
Health check
```json
{
  "status": "Professional WhatsApp Sales Agent is running",
  "model": "GPT-4o",
  "features": [...]
}
```

### Lead Management

#### `GET /leads`
Get all leads with scores
```json
{
  "total_leads": 5,
  "leads": [
    {
      "phone": "whatsapp:+971501234567",
      "score": 85,
      "stage": "scheduling",
      "data": {...},
      "last_activity": "2026-01-02T23:00:00",
      "message_count": 8
    }
  ]
}
```

#### `GET /leads/export`
Download leads as CSV for CRM import

#### `GET /conversations/{phone_number}`
View full conversation history
```json
{
  "phone_number": "+971501234567",
  "conversation_state": {...},
  "messages": [...]
}
```

#### `GET /conversation-summary/{phone_number}`
Get AI-generated conversation summary
```json
{
  "phone": "+971501234567",
  "lead_score": 85,
  "stage": "scheduling",
  "summary": "Sanwal Khan is interested in a 2M AED apartment in Downtown Dubai...",
  "lead_data": {...}
}
```

## 🎯 How It Works

### Conversation Flow

1. **Greeting Stage**
   - Warm welcome
   - Build initial rapport
   - Understand general interest

2. **Qualifying Stage**
   - Extract requirements (location, property type)
   - Validate budget
   - Collect contact information
   - Handle objections

3. **Scheduling Stage**
   - Book appointments
   - Send property listings
   - Confirm next steps

### Validation Examples

**Phone Number Validation:**
```
User: "03047127020"
Agent: "Just to make sure I can reach you on WhatsApp, could you add 
       the country code? For example: +971 50 123 4567"

User: "+923047127020"
Agent: "Got it, thank you! ✅"
```

**Budget Parsing:**
```
User: "around 500k"
✓ Parsed as: 500,000 AED

User: "1.5M to 2M"
✓ Parsed as: Range 1,500,000 - 2,000,000 AED

User: "expensive"
✗ Agent asks for specific range
```

### Lead Scoring

Points are awarded for:
- Name provided: +10
- Phone validated: +25
- Email validated: +15
- Budget specified: +20
- Location preference: +15
- Property type: +15

**Total: 100 points maximum**

Leads with 70+ score are flagged as high-quality in logs.

## 🛠️ Customization

### Change Agent Personality

Edit `SYSTEM_PROMPT` in `app.py`:
```python
SYSTEM_PROMPT = """You are [NAME], a [PERSONALITY] for [COMPANY]...
```

### Adjust Validation Rules

Modify functions in `validators.py`:
- `validate_phone_number()` - Phone format rules
- `validate_budget()` - Budget range limits
- `validate_name()` - Name character rules

### Add New Dubai Areas

Update `dubai_areas` list in `validators.py`:
```python
dubai_areas = [
    'Downtown Dubai', 'Dubai Marina', 'Your New Area', ...
]
```

### Change Lead Scoring

Modify `calculate_lead_score()` in `validators.py`:
```python
if lead_data.get('name'):
    score += 10  # Adjust points
```

## 📊 Monitoring & Analytics

### View Active Conversations
```bash
curl http://localhost:8000/leads
```

### Export for Analysis
```bash
curl http://localhost:8000/leads/export > leads.csv
```

### Check Specific Lead
```bash
curl http://localhost:8000/conversations/+971501234567
```

### Get Conversation Summary
```bash
curl http://localhost:8000/conversation-summary/+971501234567
```

## 🔒 Production Deployment

### Database Integration
Replace in-memory storage with PostgreSQL/MongoDB:

```python
# Instead of:
conversations = {}

# Use:
from database import get_conversation, save_conversation
```

### Environment Variables
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
```

### Deploy Options
- **Heroku**: `git push heroku main`
- **AWS EC2**: Use systemd service
- **Docker**: Build and deploy container
- **Railway/Render**: Connect GitHub repo

### Security
- Use HTTPS only
- Validate Twilio webhook signatures
- Rate limit API endpoints
- Encrypt sensitive data

## 🧪 Testing

### Test Validation Functions
```python
from validators import validate_phone_number, validate_budget

# Test phone
result = validate_phone_number("+971501234567")
print(result.is_valid)  # True

# Test budget
result = validate_budget("1.5M")
print(result.value)  # {'value': 1500000, 'type': 'fixed'}
```

### Test Conversation Flow
Send test messages via Twilio or use the API directly:
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -d "Body=Hello" \
  -d "From=whatsapp:+971501234567"
```

## 📝 Example Conversation

```
User: hey
Agent: Hey there! 👋 How's it going? Are you exploring Dubai's 
       property market, or just browsing around for now? 😊

User: yes I am exploring
Agent: That's exciting! Dubai has so many incredible options. Is there 
       a particular area or type of property that's caught your attention?

User: in downtown
Agent: Great choice! Downtown is vibrant with so much to offer. To help 
       you best, what budget range are you considering?

User: around 2M
Agent: Perfect! There are some stunning options in Downtown within that 
       range. By the way, I didn't catch your name earlier. What should 
       I call you? 😊

User: Sanwal Khan
Agent: Lovely to meet you, Sanwal! I'm Aisha. When's a good time for us 
       to chat about some options?

[Lead Score: 85/100 - High Quality Lead! 🌟]
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Multi-language support (Arabic, Hindi, Urdu)
- Voice message handling
- Image recognition for property photos
- Integration with property listing APIs
- Automated follow-up scheduling

## 📄 License

MIT License - feel free to use for commercial projects

## 🆘 Support

For issues or questions:
1. Check conversation logs in terminal
2. Review API endpoint responses
3. Test validation functions individually
4. Check OpenAI API key and credits

## 🎉 Features Summary

✅ Natural, human-like conversations (not robotic!)  
✅ Intelligent input validation with retry logic  
✅ Automatic lead scoring (0-100)  
✅ CRM-ready data export  
✅ Real-time conversation monitoring  
✅ Professional sales techniques built-in  
✅ Objection handling  
✅ Appointment scheduling  
✅ Context-aware responses  
✅ Production-ready architecture  

---

**Built with ❤️ for professional real estate sales teams**
