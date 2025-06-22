# Telegram Bot with GPT Integration

## Overview

This is a Python-based Telegram bot that integrates with OpenAI's GPT models to provide conversational AI capabilities. The bot features local conversation caching, maintains context across messages, and includes a Flask web server for deployment on Replit. The system is designed to handle Arabic text and provides a simple interface for users to interact with AI through Telegram.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

**Core Components:**
- **Bot Layer** (`bot.py`): Main Telegram bot logic and OpenAI integration
- **Configuration Layer** (`config.py`): Environment variable management and validation
- **Data Layer** (`data_manager.py`): Local JSON-based caching system
- **Web Layer** (`main.py`): Flask server for Replit deployment
- **Storage** (`data.json`): Local file-based data persistence

**Deployment Strategy:**
- Replit-optimized with Flask server to maintain uptime
- Environment variable-based configuration
- Thread-safe operations for concurrent user handling

## Key Components

### Telegram Bot (`bot.py`)
- **Purpose**: Core bot functionality with GPT integration
- **Features**: 
  - OpenAI GPT-4o integration for AI responses
  - Conversation context management per user
  - Command handlers for `/start`, `/help`, `/clear`
  - Arabic language support
- **Architecture Decision**: Uses python-telegram-bot library for robust Telegram API integration
- **Rationale**: Provides async support and comprehensive bot features

### Configuration Management (`config.py`)
- **Purpose**: Centralized configuration with validation
- **Features**:
  - Environment variable loading with fallbacks
  - Required token validation
  - Secure credential handling
- **Architecture Decision**: Class-based configuration with validation
- **Rationale**: Ensures bot fails fast if misconfigured and provides clear error messages

### Data Manager (`data_manager.py`)
- **Purpose**: Local data persistence and caching
- **Features**:
  - Thread-safe JSON file operations
  - Q&A pair caching (structure prepared)
  - Automatic file creation and validation
- **Architecture Decision**: File-based storage instead of database
- **Rationale**: Simplifies deployment and reduces dependencies for small-scale usage

### Web Server (`main.py`)
- **Purpose**: Keep bot alive on Replit platform
- **Features**:
  - Flask server with health endpoints
  - Threading for concurrent bot and web operations
  - Replit-specific deployment optimizations
- **Architecture Decision**: Combined Flask + Telegram bot in single process
- **Rationale**: Replit requires HTTP server for continuous running

## Data Flow

1. **User Interaction**: User sends message to Telegram bot
2. **Message Processing**: Bot receives message via webhook/polling
3. **Context Management**: Bot retrieves/updates conversation context
4. **AI Integration**: Message sent to OpenAI GPT-4o for response
5. **Response Delivery**: AI response sent back to user via Telegram
6. **Data Persistence**: Conversation data cached locally (when implemented)

## External Dependencies

### Required Services:
- **Telegram Bot API**: Bot registration and message handling
- **OpenAI API**: GPT model access for AI responses

### Python Packages:
- `python-telegram-bot==22.1`: Telegram bot framework
- `openai>=1.90.0`: OpenAI API client
- `flask>=3.1.1`: Web server for Replit deployment

### Environment Variables:
- `TELEGRAM_BOT_TOKEN`: Required for Telegram API access
- `OPENAI_API_KEY`: Required for OpenAI GPT access

## Deployment Strategy

**Platform**: Replit
**Approach**: Combined web server + bot process
**Configuration**: 
- Uses Python 3.11 runtime
- Flask server on port 5000 for platform requirements
- Bot runs in background thread
- Automatic restart via Replit workflows

**Deployment Process**:
1. Environment variables configured in Replit secrets
2. Flask server starts for platform compliance
3. Telegram bot initializes in separate thread
4. Health endpoints available for monitoring

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**June 22, 2025:**
✓ Fixed Telegram bot library compatibility issues  
✓ Updated to use GPT-4o-mini for natural conversations
✓ Disabled local caching to ensure fresh GPT responses for every message
✓ Removed fallback template responses that were causing repetitive answers
✓ Enhanced conversation system for genuine human-like interactions
✓ Increased conversation context memory (30 messages)
✓ Ensured all responses come directly from GPT API calls
✓ Enhanced error handling without showing technical failure messages
✓ Configured robust retry logic with exponential backoff
✓ Optimized Flask server to keep bot alive on Replit platform

## Changelog

- June 22, 2025: Initial setup and comprehensive error handling implementation