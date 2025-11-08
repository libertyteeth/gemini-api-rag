"""YouTube video scraping and transcript extraction."""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


class YouTubeScraper:
    """Scrape YouTube channels for video transcripts."""

    def __init__(self, data_dir: str = 'data/transcripts'):
        """
        Initialize YouTube scraper.

        Args:
            data_dir: Directory to store transcript files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.

        Args:
            url: YouTube video URL

        Returns:
            Video ID or None
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)',
            r'youtube\.com\/embed\/([\w-]+)',
            r'youtube\.com\/v\/([\w-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_channel_id(self, channel_url: str) -> Optional[str]:
        """
        Extract channel ID or username from URL.

        Args:
            channel_url: YouTube channel URL

        Returns:
            Channel identifier
        """
        # Handle different channel URL formats
        patterns = [
            r'youtube\.com\/channel\/([\w-]+)',
            r'youtube\.com\/@([\w-]+)',
            r'youtube\.com\/c\/([\w-]+)',
            r'youtube\.com\/user\/([\w-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                return match.group(1)

        # If it's just a name, return it
        if '/' not in channel_url:
            return channel_url

        return None

    def get_channel_videos(
        self, channel_url: str, max_videos: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get videos from a YouTube channel using Playwright.

        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to retrieve

        Returns:
            List of video dictionaries with 'video_id', 'title', 'url'
        """
        print(f"Fetching videos from channel: {channel_url}")
        videos = []

        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Navigate to channel videos page
                if '/videos' not in channel_url:
                    if channel_url.endswith('/'):
                        channel_url = channel_url + 'videos'
                    else:
                        channel_url = channel_url + '/videos'

                print(f"Loading: {channel_url}")
                page.goto(channel_url, timeout=30000)

                # Wait for videos to load
                page.wait_for_selector('ytd-rich-item-renderer', timeout=15000)

                # Scroll to load more videos
                for _ in range(3):
                    page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
                    time.sleep(1)

                # Extract video links
                video_elements = page.query_selector_all(
                    'ytd-rich-item-renderer a#video-title-link'
                )

                for element in video_elements[:max_videos]:
                    try:
                        title = element.get_attribute('title')
                        href = element.get_attribute('href')

                        if title and href:
                            # Construct full URL
                            video_url = f"https://www.youtube.com{href}"
                            video_id = self.extract_video_id(video_url)

                            if video_id:
                                videos.append({
                                    'video_id': video_id,
                                    'title': title,
                                    'url': video_url,
                                })

                                if len(videos) >= max_videos:
                                    break
                    except Exception as e:
                        print(f"Error extracting video: {e}")
                        continue

            except PlaywrightTimeout:
                print("Timeout loading channel page")
            except Exception as e:
                print(f"Error fetching channel videos: {e}")
            finally:
                browser.close()

        print(f"Found {len(videos)} videos")
        return videos

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if not available
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([item['text'] for item in transcript_list])
            return transcript_text
        except TranscriptsDisabled:
            print(f"  ✗ Transcripts disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            print(f"  ✗ No transcript found for video {video_id}")
            return None
        except VideoUnavailable:
            print(f"  ✗ Video {video_id} is unavailable")
            return None
        except Exception as e:
            print(f"  ✗ Error getting transcript for {video_id}: {e}")
            return None

    def save_transcript(
        self, video_id: str, title: str, transcript: str, url: str
    ) -> Path:
        """
        Save transcript to a file.

        Args:
            video_id: YouTube video ID
            title: Video title
            transcript: Transcript text
            url: Video URL

        Returns:
            Path to saved file
        """
        # Sanitize filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        filename = f"{video_id}_{safe_title[:50]}.txt"
        filepath = self.data_dir / filename

        # Write transcript with metadata
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Title: {title}\n")
            f.write(f"URL: {url}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(transcript)

        return filepath

    def scrape_channel(
        self, channel_url: str, max_videos: int = 5
    ) -> Dict[str, any]:
        """
        Scrape a YouTube channel for video transcripts.

        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to scrape

        Returns:
            Dictionary with scraping results
        """
        print(f"\n{'=' * 80}")
        print(f"SCRAPING YOUTUBE CHANNEL")
        print(f"{'=' * 80}")

        # Get channel videos
        videos = self.get_channel_videos(channel_url, max_videos)

        if not videos:
            print("No videos found!")
            return {
                'success': False,
                'channel_url': channel_url,
                'videos_found': 0,
                'transcripts_saved': 0,
                'files': [],
            }

        # Download transcripts
        saved_files = []
        total_tokens = 0

        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] Processing: {video['title']}")
            print(f"  URL: {video['url']}")

            # Get transcript
            transcript = self.get_transcript(video['video_id'])

            if transcript:
                # Save to file
                filepath = self.save_transcript(
                    video['video_id'],
                    video['title'],
                    transcript,
                    video['url'],
                )

                # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
                estimated_tokens = len(transcript) // 4

                saved_files.append({
                    'video_id': video['video_id'],
                    'title': video['title'],
                    'url': video['url'],
                    'filepath': str(filepath),
                    'transcript_length': len(transcript),
                    'estimated_tokens': estimated_tokens,
                })

                total_tokens += estimated_tokens
                print(f"  ✓ Saved to: {filepath}")
                print(f"  ✓ Estimated tokens: {estimated_tokens:,}")
            else:
                print(f"  ✗ Could not get transcript")

        print(f"\n{'=' * 80}")
        print(f"SCRAPING COMPLETE")
        print(f"{'=' * 80}")
        print(f"Videos found: {len(videos)}")
        print(f"Transcripts saved: {len(saved_files)}")
        print(f"Total estimated tokens: {total_tokens:,}")
        print(f"{'=' * 80}\n")

        return {
            'success': True,
            'channel_url': channel_url,
            'videos_found': len(videos),
            'transcripts_saved': len(saved_files),
            'total_estimated_tokens': total_tokens,
            'files': saved_files,
        }

    def get_saved_transcripts(self) -> List[Path]:
        """
        Get list of saved transcript files.

        Returns:
            List of transcript file paths
        """
        return list(self.data_dir.glob('*.txt'))
