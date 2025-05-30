# 🤖 Environment-Controlled AI Agent

An advanced AI agent with real-time thinking process visualization, interactive confirmation, and multi-tool capabilities including Python execution, Gmail integration, and web search.

## ✨ Features

- **🧠 Real-time Thinking Process**: Visual step-by-step breakdown of agent reasoning
- **🔧 Multi-Tool Integration**: Python calculator, Gmail sender, web search
- **👤 Interactive Confirmation**: User approval for sensitive actions with modification capabilities
- **🔍 Web Search**: Real-time information retrieval using Tavily
- **📧 Gmail Integration**: Send emails with user confirmation
- **🎨 Beautiful UI**: Modern Streamlit interface with animations

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### 2. Environment Setup

**Option A: Automated Setup**
```bash
python setup_env.py
```

**Option B: Manual Setup**
```bash
# Copy the template
cp env_template.txt .env

# Edit .env with your credentials
nano .env
```

### 3. Configure Environment Variables

Edit your `.env` file with the following credentials:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for email functionality)
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password_here

# Optional (for web search)
TAVILY_API_KEY=your_tavily_api_key_here
```

### 4. Run the Application

```bash
# Using Poetry
poetry run streamlit run app.py

# Or directly
streamlit run app.py
```

## 🔑 API Keys Setup

### OpenAI API Key (Required)
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### Gmail App Password (Optional)
1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings → Security → App passwords
3. Generate an app password for "Mail"
4. Add to `.env`: 
   - `GMAIL_EMAIL=your_email@gmail.com`
   - `GMAIL_APP_PASSWORD=your_app_password_here`

### Tavily API Key (Optional)
1. Visit [Tavily](https://tavily.com)
2. Sign up for a free account
3. Get your API key
4. Add to `.env`: `TAVILY_API_KEY=your_key_here`

## 🛡️ Security Best Practices

- **Never commit `.env` files** to version control
- **Keep API keys secure** and private
- **Use environment variables** for all sensitive data
- **Regularly rotate** your API keys
- **Monitor usage** of your API keys

## 🔧 Configuration Check

Check your configuration status:

```bash
python setup_env.py check
```

## 📋 Available Tools

1. **🐍 Python Calculator**: Execute mathematical calculations and data processing
2. **📧 Gmail Email Sender**: Send emails with user confirmation and modification
3. **🔍 Web Search**: Real-time information retrieval using Tavily

## 🎯 Example Queries

- **Math**: "Calculate 25 * 8 + 15"
- **Email**: "Send an email to john@example.com with subject 'Meeting Reminder'"
- **Search**: "What's the latest news about artificial intelligence?"
- **Complex**: "Search for the current Bitcoin price and email the result to my friend"

## 🔄 Agent Workflow

1. **🔍 Perception**: Understand the task
2. **🧠 Reasoning**: Choose appropriate tools
3. **🔧 Action**: Execute tools
4. **📝 Feedback**: Evaluate results
5. **👤 Confirmation**: User approval (if needed)

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Error**: Check your API key and billing status
2. **Gmail Authentication Failed**: Verify app password and 2FA setup
3. **Web Search Not Working**: Check Tavily API key
4. **Environment Variables Not Loading**: Ensure `.env` file exists and is properly formatted

### Debug Mode

Enable debug logging in your `.env`:
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 📁 Project Structure

```
poc/
├── agent.py              # Core agent logic
├── app.py                # Streamlit UI
├── setup_env.py          # Environment setup script
├── env_template.txt      # Environment template
├── test_web_search.py    # Web search testing
├── .env                  # Your credentials (not in git)
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for educational and development purposes. Always review and approve actions before execution, especially for email sending and external API calls. 