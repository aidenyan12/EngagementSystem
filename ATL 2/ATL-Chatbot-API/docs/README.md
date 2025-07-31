# ATL Chatbot with RAG System

A sophisticated AI chatbot for the Arts Technology Lab (ATL) at The University of Hong Kong, featuring both enhanced feed methods and Retrieval-Augmented Generation (RAG) for accurate information delivery.

## ⚡ **NEW: Modular Architecture**

The chatbot has been refactored into a modular architecture for better maintainability and extensibility. You can now use either:
- **`chatbot_new.py`** - New modular version (recommended)
- **`chatbot.py`** - Original monolithic version (legacy)

### Modular Benefits
- 🛠️ **Better Maintainability**: Each module has a single responsibility
- 🧪 **Enhanced Testability**: Individual modules can be tested separately  
- 📈 **Improved Scalability**: Easy to add new features and response types
- 💾 **Memory Efficiency**: Better caching and resource management
- 🏗️ **Clean Architecture**: Clear separation of concerns

## Features

### 🤖 Enhanced AI Chatbot
- **Base Model Integration**: Uses Qwen base model for natural language understanding
- **Feed Method**: Provides structured ATL information without fine-tuning
- **RAG Integration**: Real-time information retrieval from the ATL website
- **Timing Analytics**: Detailed performance metrics and logging
- **Terminology Standardization**: Consistent formatting for English and Chinese text
- **Modular Architecture**: Maintainable, testable, and scalable code structure

### 🔍 RAG System
- **Web Scraping**: Automatically extracts information from [https://www.atlab.hku.hk/](https://www.atlab.hku.hk/)
- **Content Chunking**: Intelligent text segmentation for optimal retrieval
- **Keyword Search**: Fast and accurate information retrieval
- **Dynamic Updates**: Easy system for keeping information current
- **Management Tools**: Command-line interface for RAG operations

### 📊 Information Sources
- **Structured Data**: Facility details, equipment lists, software catalogs
- **FAQ Database**: Common questions and answers from website conversations
- **Real-time Web Content**: Latest information from the ATL website
- **Metadata Tracking**: Comprehensive logging of information sources

## Installation

### Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended for optimal performance)

### Setup
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ATL-Chatbot-API-Testing
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the base model**:
   ```bash
   # Download Qwen base model to models/qwen_base/
   # (Model files should be placed in the models directory)
   ```

## Usage

### Starting the Chatbot

#### New Modular Version (Recommended)
```bash
# Start interactive chat (default)
python src/chatbot_new.py

# Test with a single question
python src/chatbot_new.py --test "What facilities are available?"

# Display system information
python src/chatbot_new.py --info

# Update RAG database
python src/chatbot_new.py --update-rag
```

#### Legacy Version
```bash
# Start interactive chat
python src/chatbot.py chat

# Display project information
python src/chatbot.py info

# Show help
python src/chatbot.py help
```

### Interactive Commands (New Version)
- `help` - Show available commands
- `info` - Display system information
- `reload` - Reload all data sources
- `update-rag` - Update RAG database
- `clear-cache` - Clear model cache
- `quit/exit/q` - Exit the chatbot

### RAG System Management
```bash
# Update RAG data from the ATL website
python src/manage_rag.py --update

# Check RAG system status
python src/manage_rag.py --status

# Test RAG retrieval
python src/manage_rag.py --test
```

### Legacy Chat Commands
- `/think` - Enable thinking mode (step-by-step reasoning)
- `/nothink` - Disable thinking mode (direct answers)
- `/context` - Show information sources being used
- `/rag-update` - Update RAG data from website
- `/rag-status` - Check RAG system status
- `exit`, `quit`, or `q` - End chat session

## Project Structure

```
ATL-Chatbot-API-Testing/
├── src/
│   ├── chatbot_new.py      # New modular chatbot (recommended)
│   ├── chatbot.py          # Original chatbot (legacy)
│   ├── data_loader.py      # Data loading and management
│   ├── model_manager.py    # Model loading and caching
│   ├── text_processors.py  # Text processing utilities
│   ├── response_generators.py # Response generation functions
│   ├── rag_system.py       # RAG system implementation
│   ├── terminology.py      # Terminology standardization
│   ├── website_links.py    # Website link management
│   └── manage_rag.py       # RAG management script
├── data/
│   ├── source_data/        # Structured ATL information
│   ├── rag_data/          # RAG scraped data and chunks
│   ├── client_questions/   # Saved conversations
│   └── logs/              # Timing and performance logs
├── conversations/          # Saved chat conversations (new)
├── models/
│   └── qwen_base/         # Base model files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Modular Architecture

### Module Overview
The new modular architecture separates concerns into distinct modules:

1. **`data_loader.py`** - Data Loading and Information Management
   - `InformationFeed` class for managing all data sources
   - Base information, FAQ, and website data loading
   - RAG system integration and context retrieval

2. **`model_manager.py`** - Model Loading and Management
   - Model loading with intelligent caching
   - Memory management and cache clearing utilities
   - Model information and status tracking

3. **`text_processors.py`** - Text Processing Utilities
   - Language detection and text validation
   - Facility name extraction and matching
   - Text normalization and formatting functions

4. **`response_generators.py`** - Response Generation
   - Specialized response generators (pricing, facilities, staff, events)
   - Lightweight and comprehensive response modes
   - Response formatting and fallback handling

5. **`chatbot_new.py`** - Main Orchestrator
   - Interactive chat interface with enhanced commands
   - Command-line argument handling
   - Integration of all modular components

### Migration Guide

#### For Users
- Use `python src/chatbot_new.py` instead of `python src/chatbot.py`
- All existing functionality is preserved with enhanced features
- New command-line options provide more flexibility

#### For Developers
```python
# Import specific modules as needed
from data_loader import InformationFeed
from model_manager import load_model
from response_generators import generate_response
from text_processors import is_non_text_input

# Initialize components
info_feed = InformationFeed()
model, tokenizer = load_model(lightweight_mode=True)

# Generate responses
if not is_non_text_input(user_input):
    response = generate_response(
        model=model,
        tokenizer=tokenizer,
        user_input=user_input,
        info_feed=info_feed,
        lightweight_mode=True
    )
```

## RAG System Details

### How It Works
1. **Web Scraping**: The system scrapes the ATL website to extract current information
2. **Content Processing**: Raw HTML is cleaned and structured into meaningful content
3. **Chunking**: Large content is split into manageable chunks for efficient retrieval
4. **Indexing**: Content is indexed for fast keyword-based search
5. **Retrieval**: When users ask questions, relevant chunks are retrieved and provided as context

### Information Sources
The RAG system extracts information from:
- **Main Pages**: Homepage, about pages, facility descriptions
- **Event Information**: Current and upcoming events
- **Resource Details**: Equipment, software, and facility specifications
- **Contact Information**: Location, hours, booking procedures
- **Research Areas**: Lab focus areas and research projects

### Adding New Information
The system is designed for easy expansion:

1. **Automatic Updates**: Run `--update-rag` to refresh website data
2. **Manual Data**: Add structured data to `data/source_data/`
3. **Custom Sources**: Extend the scraper to include additional websites
4. **API Integration**: Connect to external APIs for real-time data

## Performance Features

### Timing Analytics
- **Total Response Time**: Complete processing time
- **Generation Time**: Model inference time
- **Token Count**: Input and output token statistics
- **Speed Metrics**: Tokens per second performance
- **Logging**: All metrics saved to `data/logs/timing.log`

### Optimization
- **Efficient Retrieval**: Fast keyword-based search
- **Context Optimization**: Smart chunk selection
- **Memory Management**: Efficient data storage and loading
- **Error Handling**: Graceful fallbacks for missing data
- **Modular Caching**: Component-level caching for better performance

## Configuration

### RAG Settings
- **Chunk Size**: 1000 words (configurable)
- **Overlap**: 200 words between chunks
- **Max Pages**: 30 pages per scraping session
- **Update Frequency**: Manual or scheduled updates

### Model Settings
- **Temperature**: 0.2 (for factual responses)
- **Max Tokens**: 2048
- **Top-p**: 0.85
- **Repetition Penalty**: 1.2

## Troubleshooting

### Common Issues
1. **RAG System Not Available**: Install dependencies with `pip install requests beautifulsoup4 lxml`
2. **Model Loading Errors**: Ensure model files are in `models/qwen_base/`
3. **Scraping Failures**: Check internet connection and website availability
4. **Memory Issues**: Reduce chunk size or max pages in RAG settings
5. **Import Errors**: Ensure all modules are in the `src/` directory
6. **Module Dependencies**: Check that all required modules are available

### Debug Mode
Enable detailed logging:
```bash
export CHATBOT_DEBUG=1
python src/chatbot_new.py
```

### Getting Help
- Check system status: `python src/chatbot_new.py --info`
- Test with single question: `python src/chatbot_new.py --test "your question"`
- View logs: Check `data/logs/` directory
- Review documentation: See inline code comments

## Contributing

### Adding Features
1. **New Data Sources**: Extend the scraper in `rag_system.py`
2. **Enhanced Retrieval**: Implement semantic search or embeddings
3. **UI Improvements**: Add web interface or API endpoints
4. **Performance**: Optimize chunking or retrieval algorithms
5. **New Modules**: Follow the modular architecture pattern

### Code Standards
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include error handling
- Update documentation for new features
- Use the modular architecture for new components

## License

This project is developed for the Arts Technology Lab at The University of Hong Kong.

## Support

For technical support or questions about the ATL chatbot:
- Check the troubleshooting section above
- Review the inline documentation
- Use the `--info` command for system diagnostics
- Contact the development team

---

**Note**: This chatbot uses information from the [Arts Tech Lab website](https://www.atlab.hku.hk/) and is designed to provide accurate, up-to-date information about ATL facilities, events, and resources. The new modular architecture provides a solid foundation for future development while maintaining all existing functionality. 