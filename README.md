# YouTube RAG Tool

A powerful Retrieval-Augmented Generation (RAG) tool that allows you to chat with YouTube channel transcripts using Google's Gemini API File Search feature.

## Features

- **YouTube Channel Scraping**: Automatically scrape video titles and transcripts from any YouTube channel using Playwright
- **Gemini File Search Integration**: Upload transcripts to Gemini's managed RAG system for semantic search
- **Flexible Authentication**: Supports both API key and gcloud CLI authentication
- **Interactive & Non-Interactive Modes**: Run as an interactive chat or execute scripted prompts
- **Cost Tracking**: Track and report API costs with detailed breakdowns
- **Chat History**: Maintain complete conversation history with metadata
- **Idempotent Operations**: Re-run safely without duplicating work

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Non-Interactive Mode](#non-interactive-mode)
  - [Cost Reporting](#cost-reporting)
- [Project Structure](#project-structure)
- [Cost Information](#cost-information)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud account with Gemini API access
- Either:
  - Gemini API key, OR
  - gcloud CLI installed and configured

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/libertyteeth/gemini-api-rag.git
   cd gemini-api-rag
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Configure authentication** (choose ONE):

   **Option A: Using API Key**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

   **Option B: Using gcloud CLI**
   ```bash
   gcloud auth application-default login
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root (optional if using gcloud CLI):

```env
# Optional: Gemini API Key
GEMINI_API_KEY=your_api_key_here
```

If `GEMINI_API_KEY` is not set, the tool will automatically attempt to use gcloud CLI authentication.

### Authentication Priority

1. **API Key**: Checks `GEMINI_API_KEY` environment variable first
2. **gcloud CLI**: Falls back to `gcloud auth application-default` credentials
3. **Error**: Exits with helpful message if both methods fail

## Usage

### Interactive Mode

Start an interactive chat session:

```bash
python main.py
```

You'll be prompted for:
- YouTube channel URL
- Number of videos to process

Then you can chat with the transcripts:

```
You: What are the main topics discussed in these videos?
Assistant: Based on the transcripts, the main topics include...

You: Tell me more about topic X
Assistant: ...

You: quit
```

**Interactive Commands**:
- `quit`, `exit`, or `q` - Exit the chat
- `cost` - Show cost summary
- `history` - Show recent chat history

### Non-Interactive Mode

Specify all parameters via command line:

```bash
# Basic usage
python main.py --channel="https://youtube.com/@channelname" --numvideos=10

# With specific prompts (non-interactive)
python main.py \
  --channel="https://youtube.com/@channelname" \
  --numvideos=5 \
  --prompt="Summarize the main topics discussed" \
  --prompt="What insights are provided about AI?"
```

### Command-Line Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--channel=URL` | YouTube channel URL | (required for non-interactive) |
| `--numvideos=N` | Number of videos to retrieve | 5 |
| `--prompt="text"` | Prompt to execute (can repeat) | None |
| `--model=NAME` | Gemini model to use | gemini-2.0-flash-exp |
| `--skip-scraping` | Skip scraping, use existing transcripts | False |
| `--cost-report` | Show detailed cost report | - |
| `--cost-query="query"` | Query costs | - |

### Cost Reporting

**View detailed cost summary**:
```bash
python main.py --cost-report
```

**Query specific cost information**:
```bash
# Yesterday's costs
python main.py --cost-query="How much did yesterday cost?"

# Total costs since project began
python main.py --cost-query="Total cost since project began"

# This week's costs
python main.py --cost-query="This week's costs"

# This month's costs
python main.py --cost-query="This month's costs"

# Today's costs
python main.py --cost-query="What is today's cost?"
```

### Examples

**Example 1: Quick test with 3 videos**
```bash
python main.py \
  --channel="https://youtube.com/@lexfridman" \
  --numvideos=3 \
  --prompt="What topics are covered?"
```

**Example 2: Deep dive with multiple prompts**
```bash
python main.py \
  --channel="https://youtube.com/@3blue1brown" \
  --numvideos=10 \
  --prompt="List all mathematical concepts discussed" \
  --prompt="Explain the calculus topics in detail" \
  --prompt="What visualizations are described?"
```

**Example 3: Use existing transcripts**
```bash
python main.py \
  --skip-scraping \
  --prompt="Summarize everything we have so far"
```

## Project Structure

```
gemini-api-rag/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── main.py                  # Main entry point
│
├── src/
│   ├── __init__.py
│   ├── gemini_client.py     # Gemini API authentication
│   ├── youtube_scraper.py   # YouTube scraping with Playwright
│   ├── rag_manager.py       # Gemini File Search RAG management
│   ├── cost_tracker.py      # Cost tracking and reporting
│   └── chat_history.py      # Chat history management
│
├── data/
│   ├── transcripts/         # Downloaded video transcripts
│   ├── costs.json          # Cost tracking data
│   └── history.json        # Chat history data
│
└── config/
    └── store_config.json    # Vector store configuration
```

## Cost Information

### Gemini API Pricing (as of November 2025)

| Operation | Cost |
|-----------|------|
| **File Search Indexing** | $0.15 per 1M tokens |
| **File Search Storage** | Free |
| **Query Embeddings** | Free |
| **Context Tokens** | $0.075 per 1M tokens* |
| **Output Tokens** | $0.30 per 1M tokens* |

*Varies by model

### Cost Tracking Features

The tool automatically tracks:
- **Indexing costs** when uploading transcripts
- **Query costs** for each chat interaction
- **Historical costs** by day, week, month
- **Token usage** for input and output

All costs are stored in `data/costs.json` and can be queried at any time.

### Estimated Costs Example

For a typical YouTube channel scrape:
- 10 videos × 5,000 words each = ~17,000 tokens per video
- Total indexing: 170,000 tokens = **$0.026**
- Storage: **Free**
- 10 chat queries: ~$0.002

**Total for this workflow**: **~$0.028**

## Data Persistence

### Transcripts
- Saved in `data/transcripts/`
- Format: `{video_id}_{title}.txt`
- Includes video metadata (ID, title, URL)

### Cost Tracking
- File: `data/costs.json`
- Includes: timestamp, transaction type, cost, metadata
- Supports historical queries and reporting

### Chat History
- File: `data/history.json`
- Includes: timestamp, prompt, response, cost, tokens, user, IP
- Searchable and exportable

### Vector Store Config
- File: `config/store_config.json`
- Stores Gemini File Search store IDs
- Enables idempotent operations

## Troubleshooting

### Authentication Issues

**Problem**: "Authentication failed"
```bash
# Solution 1: Use API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Solution 2: Configure gcloud
gcloud auth application-default login
```

### Playwright Issues

**Problem**: "Browser not found"
```bash
# Solution: Install Playwright browsers
playwright install chromium
```

### YouTube Scraping Issues

**Problem**: "No videos found"
- Verify the channel URL format: `https://youtube.com/@channelname`
- Check if the channel has public videos
- Try adding `/videos` to the URL

**Problem**: "No transcript found"
- Not all YouTube videos have transcripts/subtitles
- The tool will skip videos without transcripts
- Try increasing `--numvideos` to get more videos

### Gemini API Issues

**Problem**: "File Search not available"
- Verify you have access to Gemini API File Search feature
- Check if your API key has the necessary permissions
- Ensure you're using a supported model (gemini-2.0-flash-exp, gemini-2.5-pro, etc.)

### General Debugging

Enable verbose output:
```bash
python -u main.py --channel="..." 2>&1 | tee debug.log
```

## Advanced Usage

### Custom Models

Use a different Gemini model:
```bash
python main.py --model="gemini-2.5-pro" --channel="..."
```

### Batch Processing Multiple Channels

Create a script:
```bash
#!/bin/bash
CHANNELS=(
  "https://youtube.com/@channel1"
  "https://youtube.com/@channel2"
  "https://youtube.com/@channel3"
)

for channel in "${CHANNELS[@]}"; do
  python main.py --channel="$channel" --numvideos=10
done
```

### Export Chat History

```python
from src.chat_history import ChatHistory

history = ChatHistory()
history.export_to_file('my_conversations.txt', format='txt')
history.export_to_file('my_conversations.json', format='json')
```

### Programmatic Usage

```python
from src.gemini_client import GeminiClient
from src.rag_manager import RAGManager

# Initialize
client = GeminiClient()
client.authenticate()

rag = RAGManager()

# Query
result = rag.query("What topics are discussed?")
print(result['response'])
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- [Google Gemini API](https://ai.google.dev/gemini-api/docs/file-search) for File Search
- [Playwright](https://playwright.dev/) for web scraping
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction

## Support

For issues, questions, or feature requests, please open an issue on GitHub:
https://github.com/libertyteeth/gemini-api-rag/issues

## Roadmap

- [ ] Support for playlist URLs
- [ ] Parallel video processing
- [ ] Web UI interface
- [ ] Export to different formats (PDF, Markdown)
- [ ] Integration with other LLMs
- [ ] Advanced filtering and search
- [ ] Automatic transcript summarization
- [ ] Multi-language support

## License

MIT License - See LICENSE file for details
