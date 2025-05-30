# 🚀 Deploy to Streamlit Cloud

## Prerequisites

1. **GitHub Repository**: Your code must be in a public GitHub repository
2. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **API Keys**: You'll need these API keys for full functionality

## Required API Keys

### 🔑 Essential (Required)
- **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com/api-keys)
  - Used for: Agent reasoning, data formatting, all core functionality

### 🔑 Optional (Enhanced Features)
- **Tavily API Key**: Get from [tavily.com](https://tavily.com)
  - Used for: Web search functionality
- **Gmail App Password**: From your Google account settings
  - Used for: Email sending functionality

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file: `app.py`
6. Click "Deploy"

### 3. Configure Secrets
In your Streamlit Cloud app settings, add these secrets:

```toml
# Required
OPENAI_API_KEY = "your_openai_api_key_here"

# Optional - for web search
TAVILY_API_KEY = "your_tavily_api_key_here"

# Optional - for email functionality
GMAIL_EMAIL = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "your_app_password_here"
```

## App Features by Configuration

### ✅ With OpenAI API Key Only
- ✅ Math calculations
- ✅ Data formatting
- ✅ Agent reasoning
- ✅ All core functionality
- ❌ Web search (will show fallback message)
- ❌ Email sending (will show configuration message)

### ✅ With OpenAI + Tavily API Keys
- ✅ All math and reasoning features
- ✅ **Web search with intelligent formatting**
- ✅ Weather, stock prices, real-time data
- ❌ Email sending (will show configuration message)

### ✅ Full Configuration (All API Keys)
- ✅ **Complete functionality**
- ✅ Math calculations
- ✅ Web search with intelligent AI formatting
- ✅ **Email sending capabilities**
- ✅ All demo prompts work perfectly

## Security Notes

🔒 **Your API keys are secure**: Streamlit Cloud secrets are encrypted and not visible to users
🔒 **Environment isolation**: Each user session is isolated
🔒 **No data persistence**: The app doesn't store user data between sessions

## Troubleshooting

### Common Issues:
1. **Import errors**: Check `requirements.txt` has all dependencies
2. **API key errors**: Verify secrets are set correctly in Streamlit Cloud
3. **Slow first load**: Normal for cold starts, subsequent loads are faster

### Performance Tips:
- First load may take 30-60 seconds (cold start)
- Subsequent loads are much faster
- Web search and AI formatting may take 5-10 seconds

## App URL
After deployment, your app will be available at:
`https://[your-app-name].streamlit.app`

## Updates
To update your deployed app:
1. Push changes to your GitHub repository
2. Streamlit Cloud will automatically redeploy
3. Changes appear within 1-2 minutes

---

🎉 **Your AI Agent is now publicly accessible!** 