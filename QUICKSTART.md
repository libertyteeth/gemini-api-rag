# Quick Start Guide

Get up and running with the YouTube RAG Tool in 5 minutes!

## 1. Install (One-Time Setup)

```bash
# Clone the repository
git clone https://github.com/libertyteeth/gemini-api-rag.git
cd gemini-api-rag

# Run setup script (Linux/Mac)
chmod +x setup.sh
./setup.sh

# OR install manually
pip install -r requirements.txt
playwright install chromium
```

## 2. Configure Authentication (Choose One)

### Option A: API Key (Recommended for most users)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://aistudio.google.com/apikey

### Option B: Google Cloud CLI

```bash
# Install gcloud CLI (if not already installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login
```

## 3. Run Your First Chat

```bash
# Interactive mode
python main.py

# You'll be prompted for:
# - YouTube channel URL (e.g., https://youtube.com/@channelname)
# - Number of videos to process (default: 5)
```

## 4. Try Non-Interactive Mode

```bash
# Process a channel and ask a question
python main.py \
  --channel="https://youtube.com/@lexfridman" \
  --numvideos=3 \
  --prompt="What are the main topics discussed?"
```

## 5. Check Costs

```bash
# View cost summary
python main.py --cost-report

# Query specific costs
python main.py --cost-query="Total cost since project began"
```

## Common Commands

```bash
# Interactive chat
python main.py

# Process specific channel
python main.py --channel="URL" --numvideos=5

# Run multiple prompts
python main.py --channel="URL" \
  --prompt="Question 1" \
  --prompt="Question 2"

# Use existing transcripts (skip scraping)
python main.py --skip-scraping

# View cost report
python main.py --cost-report

# Get help
python main.py --help
```

## Troubleshooting

### "Authentication failed"
- Check that your `.env` file has a valid `GEMINI_API_KEY`, OR
- Run `gcloud auth application-default login`

### "Browser not found"
- Run `playwright install chromium`

### "No transcripts found"
- Not all YouTube videos have transcripts
- Try a different channel or increase `--numvideos`

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Explore command-line options: `python main.py --help`
- Check out the [examples](README.md#examples) in the README

## Cost Expectations

Typical costs for a small project:
- **10 videos**: ~$0.02-0.03 for indexing
- **10 queries**: ~$0.002-0.005
- **Storage**: Free

The tool tracks all costs automatically!

## Support

Questions? Issues? Visit: https://github.com/libertyteeth/gemini-api-rag/issues
