"""Chat history management."""

import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ChatHistory:
    """Manage chat conversation history."""

    def __init__(self, data_dir: str = 'data'):
        """
        Initialize chat history manager.

        Args:
            data_dir: Directory to store history data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / 'history.json'
        self.history_data = self._load_history()

    def _load_history(self) -> Dict:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not load {self.history_file}, starting fresh")
                return {'conversations': []}
        return {'conversations': []}

    def _save_history(self):
        """Save history to JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history_data, indent=2, fp=f)

    def add_interaction(
        self,
        prompt: str,
        response: str,
        cost: float,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        channel: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Add a chat interaction to history.

        Args:
            prompt: User's prompt/question
            response: Model's response
            cost: Cost of the interaction in USD
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            channel: YouTube channel (if applicable)
            metadata: Additional metadata
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'response': response,
            'cost_usd': round(cost, 6),
            'model': model,
            'tokens': {
                'input': input_tokens,
                'output': output_tokens,
                'total': input_tokens + output_tokens,
            },
            'metadata': metadata or {},
        }

        # Add optional fields
        if channel:
            interaction['channel'] = channel

        # Add system metadata
        interaction['metadata']['hostname'] = socket.gethostname()

        try:
            import getpass
            interaction['metadata']['user'] = getpass.getuser()
        except Exception:
            pass

        self.history_data['conversations'].append(interaction)
        self._save_history()

    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversations.

        Args:
            limit: Number of recent conversations to retrieve

        Returns:
            List of conversation dictionaries
        """
        conversations = self.history_data.get('conversations', [])
        return conversations[-limit:]

    def get_conversations_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """
        Get conversations within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of conversations in date range
        """
        conversations = []
        for conv in self.history_data.get('conversations', []):
            conv_date = datetime.fromisoformat(conv['timestamp'])
            if start_date <= conv_date <= end_date:
                conversations.append(conv)
        return conversations

    def get_total_conversations(self) -> int:
        """Get total number of conversations."""
        return len(self.history_data.get('conversations', []))

    def print_recent(self, limit: int = 5):
        """
        Print recent conversations.

        Args:
            limit: Number of recent conversations to print
        """
        conversations = self.get_recent_conversations(limit)

        print("\n" + "=" * 60)
        print(f"RECENT CONVERSATIONS (Last {limit})")
        print("=" * 60)

        if not conversations:
            print("No conversations found.")
            print("=" * 60 + "\n")
            return

        for i, conv in enumerate(conversations, 1):
            timestamp = datetime.fromisoformat(conv['timestamp'])
            print(f"\n[{i}] {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Model: {conv.get('model', 'unknown')}")
            print(f"Cost: ${conv.get('cost_usd', 0):.6f}")
            print(f"Tokens: {conv.get('tokens', {}).get('total', 0)}")
            print(f"\nPrompt: {conv.get('prompt', '')[:100]}...")
            print(f"Response: {conv.get('response', '')[:200]}...")
            print("-" * 60)

        print("=" * 60 + "\n")

    def search_conversations(self, query: str) -> List[Dict]:
        """
        Search conversations by query string.

        Args:
            query: Search query

        Returns:
            List of matching conversations
        """
        query_lower = query.lower()
        matches = []

        for conv in self.history_data.get('conversations', []):
            prompt = conv.get('prompt', '').lower()
            response = conv.get('response', '').lower()

            if query_lower in prompt or query_lower in response:
                matches.append(conv)

        return matches

    def export_to_file(self, output_file: str, format: str = 'json'):
        """
        Export history to a file.

        Args:
            output_file: Output file path
            format: Export format ('json' or 'txt')
        """
        output_path = Path(output_file)

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(self.history_data, f, indent=2)
            print(f"Exported to {output_path}")

        elif format == 'txt':
            with open(output_path, 'w') as f:
                for conv in self.history_data.get('conversations', []):
                    timestamp = conv.get('timestamp', '')
                    f.write(f"{'=' * 60}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Model: {conv.get('model', 'unknown')}\n")
                    f.write(f"Cost: ${conv.get('cost_usd', 0):.6f}\n")
                    f.write(f"\nPrompt:\n{conv.get('prompt', '')}\n")
                    f.write(f"\nResponse:\n{conv.get('response', '')}\n")
                    f.write(f"{'=' * 60}\n\n")
            print(f"Exported to {output_path}")
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_history(self):
        """Clear all conversation history."""
        self.history_data = {'conversations': []}
        self._save_history()
        print("History cleared.")
