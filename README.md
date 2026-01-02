# 🤖 AI WhatsApp Sales Agent

Professional WhatsApp sales agent powered by GPT-4o for automated lead qualification. Features natural conversations, smart validation, and persistent storage.

## ✨ Key Features

- **Natural Conversations** - Human-like responses, no robotic language
- **Smart Validation** - Phone numbers, emails, budgets (handles "500k", "1.5M", etc.)
- **Lead Scoring** - Automatic 0-100 scoring based on information completeness
- **Persistent Storage** - SQLite database survives server restarts
- **CRM Ready** - CSV export and API endpoints for integration

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run the agent
python3 app.py
```

Server starts on `http://0.0.0.0:8000`

## 📱 Twilio Setup

1. Get Twilio WhatsApp Sandbox from [Twilio Console](https://console.twilio.com)
2. Set webhook URL: `https://your-domain.com/webhook/whatsapp`
3. For local testing, use [ngrok](https://ngrok.com): `ngrok http 8000`

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook/whatsapp` | Receives WhatsApp messages from Twilio |
| `GET /` | Health check and status |
| `GET /stats` | Database statistics |
| `GET /leads` | All leads with scores (JSON) |
| `GET /leads/export` | Download leads as CSV |
| `GET /conversations/{phone}` | Full conversation history |
| `GET /conversation-summary/{phone}` | AI-generated summary |

## 💡 How It Works

### Conversation Flow
1. **Greeting** - Warm welcome, build rapport
2. **Qualifying** - Extract requirements, validate inputs
3. **Scheduling** - Book appointments, send listings

### Smart Validation
```
User: "03047127020"
Agent: "Could you add the country code? Like +971 50 123 4567"

User: "+923047127020"
Agent: "Got it, thank you! ✅"
```

### Lead Scoring
- Name: +10 | Phone: +25 | Email: +15
- Budget: +20 | Location: +15 | Property Type: +15
- **Total: 100 points**

Leads with 70+ score are flagged as high-quality.

## 🗄️ Database

**SQLite** database stores:
- All conversations (survives restarts)
- Lead data and scores
- Conversation states

**File**: `whatsapp_agent.db` (auto-created)

**Backup**:
```bash
cp whatsapp_agent.db backups/whatsapp_agent_$(date +%Y%m%d).db
```

## 🎯 Customization

### Change Agent Personality
Edit `SYSTEM_PROMPT` in `app.py`

### Adjust Validation Rules
Modify functions in `validators.py`:
- `validate_phone_number()` - Phone formats
- `validate_budget()` - Budget ranges
- `validate_name()` - Name rules

### Add Dubai Areas
Update `dubai_areas` list in `validators.py`

## 📊 Example Conversation

```
User: hey
Agent: Hey there! 👋 Are you exploring Dubai's property market?

User: yes, in downtown
Agent: Great choice! What budget range are you considering?

User: around 2M
Agent: Perfect! By the way, what should I call you?

User: Sanwal Khan
Agent: Lovely to meet you, Sanwal! When's good to chat about options?

[Lead Score: 85/100 - High Quality! 🌟]
```

## 🔒 Production Deployment

### Environment Variables
```env
OPENAI_API_KEY=sk-...
```

### Deploy Options
- **Heroku**: `git push heroku main`
- **Railway/Render**: Connect GitHub repo
- **AWS EC2**: Use systemd service
- **Docker**: Build and deploy container

### Security
- Use HTTPS only
- Validate Twilio webhook signatures
- Rate limit API endpoints
- Backup database regularly

## 📝 Project Structure

```
whatsapp_lead_agent/
├── app.py              # Main FastAPI application
├── validators.py       # Input validation utilities
├── database.py         # SQLite database management
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create from .env.example)
└── whatsapp_agent.db  # SQLite database (auto-created)
```

## 🧪 Testing

```bash
# Test validation
from validators import validate_phone_number, validate_budget

# Test phone
result = validate_phone_number("+971501234567")
print(result.is_valid)  # True

# Test budget
result = validate_budget("1.5M")
print(result.value)  # {'value': 1500000, 'type': 'fixed'}
```

## 📈 Monitoring

```bash
# View all leads
curl http://localhost:8000/leads

# Database stats
curl http://localhost:8000/stats

# Export CSV
curl http://localhost:8000/leads/export > leads.csv
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Multi-language support (Arabic, Hindi, Urdu)
- Voice message handling
- Property listing API integration
- Automated follow-up scheduling

## 📄 License

MIT License

---

**Built for professional real estate sales teams** 🏡
