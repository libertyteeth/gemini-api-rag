#!/usr/bin/env python3
"""YouTube RAG Tool - Main entry point."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from src.gemini_client import GeminiClient
from src.youtube_scraper import YouTubeScraper
from src.rag_manager import RAGManager
from src.cost_tracker import CostTracker
from src.chat_history import ChatHistory


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='YouTube RAG Tool - Chat with YouTube channel transcripts using Gemini API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - will prompt for channel and number of videos
  python main.py

  # Non-interactive mode with parameters
  python main.py --channel="https://youtube.com/@channel" --numvideos=10

  # Run specific prompts (non-interactive)
  python main.py --channel="..." --prompt="Summarize the main topics" --prompt="What is discussed about AI?"

  # Cost reporting
  python main.py --cost-report
  python main.py --cost-query="How much did yesterday cost?"
  python main.py --cost-query="Total cost since project began"
  python main.py --cost-query="This week's costs"
        """
    )

    # YouTube scraping parameters
    parser.add_argument(
        '--channel',
        type=str,
        help='YouTube channel URL (e.g., https://youtube.com/@channelname)',
    )

    parser.add_argument(
        '--numvideos',
        type=int,
        default=5,
        help='Number of videos to retrieve from newest to older (default: 5)',
    )

    # Query parameters
    parser.add_argument(
        '--prompt',
        action='append',
        help='Prompt to ask (can be specified multiple times for non-interactive mode)',
    )

    # Cost reporting
    parser.add_argument(
        '--cost-report',
        action='store_true',
        help='Show detailed cost report',
    )

    parser.add_argument(
        '--cost-query',
        type=str,
        help='Query costs (e.g., "yesterday", "this week", "total", "this month")',
    )

    # Other options
    parser.add_argument(
        '--model',
        type=str,
        default='gemini-2.0-flash-exp',
        help='Gemini model to use (default: gemini-2.0-flash-exp)',
    )

    parser.add_argument(
        '--skip-scraping',
        action='store_true',
        help='Skip scraping and use existing transcripts',
    )

    return parser.parse_args()


def handle_cost_report(cost_tracker: CostTracker):
    """Handle cost report display."""
    cost_tracker.print_summary()


def handle_cost_query(cost_tracker: CostTracker, query: str):
    """Handle cost query."""
    query_lower = query.lower()

    print(f"\nCost Query: {query}")
    print("=" * 60)

    if 'yesterday' in query_lower:
        cost = cost_tracker.get_yesterday_cost()
        print(f"Yesterday's cost: ${cost:.6f} USD")

    elif 'week' in query_lower:
        cost = cost_tracker.get_this_week_cost()
        print(f"This week's cost: ${cost:.6f} USD")

    elif 'month' in query_lower:
        cost = cost_tracker.get_this_month_cost()
        print(f"This month's cost: ${cost:.6f} USD")

    elif 'total' in query_lower or 'all' in query_lower or 'began' in query_lower:
        cost = cost_tracker.get_total_cost()
        print(f"Total cost since project began: ${cost:.6f} USD")

    elif 'today' in query_lower:
        cost = cost_tracker.get_daily_cost()
        print(f"Today's cost: ${cost:.6f} USD")

    else:
        print(f"Unknown cost query: {query}")
        print("\nSupported queries:")
        print("  - 'yesterday' or 'How much did yesterday cost?'")
        print("  - 'today' or 'What is today's cost?'")
        print("  - 'this week' or 'This week's costs'")
        print("  - 'this month' or 'This month's costs'")
        print("  - 'total' or 'Total cost since project began'")

    print("=" * 60 + "\n")


def interactive_mode(
    gemini_client: GeminiClient,
    scraper: YouTubeScraper,
    rag_manager: RAGManager,
    cost_tracker: CostTracker,
    chat_history: ChatHistory,
    args,
):
    """Run in interactive mode."""
    print("\n" + "=" * 80)
    print("YOUTUBE RAG TOOL - Interactive Mode")
    print("=" * 80 + "\n")

    # Get channel URL if not provided
    channel_url = args.channel
    if not channel_url:
        channel_url = input("Enter YouTube channel URL: ").strip()
        if not channel_url:
            print("Error: Channel URL is required")
            return

    # Get number of videos if not provided
    num_videos = args.numvideos
    if not args.channel:  # Only prompt if we also prompted for channel
        try:
            num_input = input(f"Number of videos to process (default {args.numvideos}): ").strip()
            if num_input:
                num_videos = int(num_input)
        except ValueError:
            print(f"Invalid number, using default: {args.numvideos}")

    # Scrape channel
    if not args.skip_scraping:
        scrape_result = scraper.scrape_channel(channel_url, num_videos)

        if not scrape_result['success'] or scrape_result['transcripts_saved'] == 0:
            print("Error: No transcripts were saved. Cannot proceed.")
            return

        # Upload to RAG
        transcript_files = [Path(f['filepath']) for f in scrape_result['files']]
        upload_result = rag_manager.upload_files(transcript_files)

        # Track indexing cost
        total_tokens = upload_result['total_tokens']
        for file_info in upload_result['files']:
            cost_tracker.record_indexing(
                tokens=file_info['estimated_tokens'],
                file_name=file_info['filename'],
                store_name='youtube_transcripts',
            )

        # Show estimated costs
        cost_estimate = cost_tracker.estimate_rag_storage_cost(total_tokens)
        print(f"\nEstimated indexing cost: ${cost_estimate['indexing_cost_usd']:.6f} USD")
        print(f"Storage cost: ${cost_estimate['storage_cost_usd']:.6f} USD (Free)\n")
    else:
        print("Skipping scraping, using existing transcripts...")

    # Interactive chat loop
    print("\n" + "=" * 80)
    print("CHAT MODE - Ask questions about the video transcripts")
    print("Type 'quit', 'exit', or 'q' to exit")
    print("Type 'cost' to see cost summary")
    print("Type 'history' to see recent chat history")
    print("=" * 80 + "\n")

    while True:
        try:
            prompt = input("\nYou: ").strip()

            if not prompt:
                continue

            if prompt.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if prompt.lower() == 'cost':
                cost_tracker.print_summary()
                continue

            if prompt.lower() == 'history':
                chat_history.print_recent(5)
                continue

            # Query RAG
            result = rag_manager.query(prompt, model_name=args.model)

            # Print response
            print(f"\nAssistant: {result['response']}\n")
            print(f"[Tokens - Input: {result['input_tokens']}, Output: {result['output_tokens']}]")

            # Calculate and track cost
            input_tokens = result['input_tokens']
            output_tokens = result['output_tokens']
            cost_tracker.record_query(input_tokens, output_tokens, prompt)

            # Track in history
            input_cost = input_tokens * cost_tracker.PRICING['context_1m']
            output_cost = output_tokens * cost_tracker.PRICING['output_1m']
            total_cost = input_cost + output_cost

            chat_history.add_interaction(
                prompt=prompt,
                response=result['response'],
                cost=total_cost,
                model=args.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                channel=channel_url,
            )

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


def non_interactive_mode(
    gemini_client: GeminiClient,
    scraper: YouTubeScraper,
    rag_manager: RAGManager,
    cost_tracker: CostTracker,
    chat_history: ChatHistory,
    args,
):
    """Run in non-interactive mode with prompts."""
    print("\n" + "=" * 80)
    print("YOUTUBE RAG TOOL - Non-Interactive Mode")
    print("=" * 80 + "\n")

    if not args.channel:
        print("Error: --channel is required for non-interactive mode")
        return

    # Scrape channel
    if not args.skip_scraping:
        scrape_result = scraper.scrape_channel(args.channel, args.numvideos)

        if not scrape_result['success'] or scrape_result['transcripts_saved'] == 0:
            print("Error: No transcripts were saved. Cannot proceed.")
            return

        # Upload to RAG
        transcript_files = [Path(f['filepath']) for f in scrape_result['files']]
        upload_result = rag_manager.upload_files(transcript_files)

        # Track indexing cost
        for file_info in upload_result['files']:
            cost_tracker.record_indexing(
                tokens=file_info['estimated_tokens'],
                file_name=file_info['filename'],
                store_name='youtube_transcripts',
            )
    else:
        print("Skipping scraping, using existing transcripts...")

    # Execute prompts
    print("\n" + "=" * 80)
    print(f"EXECUTING {len(args.prompt)} PROMPTS")
    print("=" * 80 + "\n")

    for i, prompt in enumerate(args.prompt, 1):
        print(f"\n[{i}/{len(args.prompt)}] Prompt: {prompt}")
        print("-" * 80)

        try:
            # Query RAG
            result = rag_manager.query(prompt, model_name=args.model)

            # Print response
            print(f"Response: {result['response']}")
            print(f"Tokens - Input: {result['input_tokens']}, Output: {result['output_tokens']}")

            # Calculate and track cost
            input_tokens = result['input_tokens']
            output_tokens = result['output_tokens']
            cost_tracker.record_query(input_tokens, output_tokens, prompt)

            # Track in history
            input_cost = input_tokens * cost_tracker.PRICING['context_1m']
            output_cost = output_tokens * cost_tracker.PRICING['output_1m']
            total_cost = input_cost + output_cost

            chat_history.add_interaction(
                prompt=prompt,
                response=result['response'],
                cost=total_cost,
                model=args.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                channel=args.channel,
            )

            print("-" * 80)

        except Exception as e:
            print(f"Error executing prompt: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ALL PROMPTS COMPLETED")
    print("=" * 80 + "\n")

    # Show final cost summary
    cost_tracker.print_summary()


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_arguments()

    # Initialize components
    cost_tracker = CostTracker()
    chat_history = ChatHistory()

    # Handle cost-only queries
    if args.cost_report:
        handle_cost_report(cost_tracker)
        return

    if args.cost_query:
        handle_cost_query(cost_tracker, args.cost_query)
        return

    # Initialize Gemini client
    gemini_client = GeminiClient()
    try:
        gemini_client.authenticate()
    except RuntimeError as e:
        print(f"\nAuthentication Error: {e}")
        sys.exit(1)

    # Initialize other components
    scraper = YouTubeScraper()
    rag_manager = RAGManager()

    # Determine mode
    is_non_interactive = args.prompt is not None

    if is_non_interactive:
        non_interactive_mode(
            gemini_client, scraper, rag_manager, cost_tracker, chat_history, args
        )
    else:
        interactive_mode(
            gemini_client, scraper, rag_manager, cost_tracker, chat_history, args
        )


if __name__ == '__main__':
    main()
