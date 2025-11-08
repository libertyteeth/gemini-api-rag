"""Cost tracking for Gemini API usage."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class CostTracker:
    """Track and report Gemini API costs."""

    # Pricing as of November 2025
    PRICING = {
        'indexing': 0.15 / 1_000_000,  # $0.15 per 1M tokens
        'storage': 0.0,  # Free for File Search
        'query_embedding': 0.0,  # Free
        'context_1m': 0.075 / 1_000_000,  # Context tokens (varies by model)
        'output_1m': 0.30 / 1_000_000,  # Output tokens (varies by model)
    }

    def __init__(self, data_dir: str = 'data'):
        """
        Initialize cost tracker.

        Args:
            data_dir: Directory to store cost data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.costs_file = self.data_dir / 'costs.json'
        self.costs_data = self._load_costs()

    def _load_costs(self) -> Dict:
        """Load costs from JSON file."""
        if self.costs_file.exists():
            try:
                with open(self.costs_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not load {self.costs_file}, starting fresh")
                return {'transactions': [], 'summary': {}}
        return {'transactions': [], 'summary': {}}

    def _save_costs(self):
        """Save costs to JSON file."""
        with open(self.costs_file, 'w') as f:
            json.dump(self.costs_data, indent=2, fp=f)

    def record_indexing(self, tokens: int, file_name: str, store_name: str):
        """
        Record indexing cost.

        Args:
            tokens: Number of tokens indexed
            file_name: Name of the file indexed
            store_name: Name of the vector store
        """
        cost = tokens * self.PRICING['indexing']
        self._record_transaction(
            transaction_type='indexing',
            cost=cost,
            metadata={
                'tokens': tokens,
                'file_name': file_name,
                'store_name': store_name,
            }
        )

    def record_query(self, input_tokens: int, output_tokens: int, prompt: str):
        """
        Record query cost.

        Args:
            input_tokens: Number of input/context tokens
            output_tokens: Number of output tokens
            prompt: The query prompt
        """
        input_cost = input_tokens * self.PRICING['context_1m']
        output_cost = output_tokens * self.PRICING['output_1m']
        total_cost = input_cost + output_cost

        self._record_transaction(
            transaction_type='query',
            cost=total_cost,
            metadata={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'prompt_preview': prompt[:100],
            }
        )

    def _record_transaction(self, transaction_type: str, cost: float, metadata: Dict):
        """
        Record a transaction.

        Args:
            transaction_type: Type of transaction (indexing, query, etc.)
            cost: Cost in USD
            metadata: Additional metadata
        """
        transaction = {
            'timestamp': datetime.now().isoformat(),
            'type': transaction_type,
            'cost_usd': round(cost, 6),
            'metadata': metadata,
        }

        self.costs_data['transactions'].append(transaction)
        self._update_summary()
        self._save_costs()

    def _update_summary(self):
        """Update cost summary statistics."""
        transactions = self.costs_data['transactions']

        summary = {
            'total_cost': 0,
            'total_transactions': len(transactions),
            'by_type': {},
            'last_updated': datetime.now().isoformat(),
        }

        for transaction in transactions:
            cost = transaction['cost_usd']
            transaction_type = transaction['type']

            summary['total_cost'] += cost

            if transaction_type not in summary['by_type']:
                summary['by_type'][transaction_type] = {
                    'count': 0,
                    'total_cost': 0,
                }

            summary['by_type'][transaction_type]['count'] += 1
            summary['by_type'][transaction_type]['total_cost'] += cost

        summary['total_cost'] = round(summary['total_cost'], 6)
        for t_type in summary['by_type']:
            summary['by_type'][t_type]['total_cost'] = round(
                summary['by_type'][t_type]['total_cost'], 6
            )

        self.costs_data['summary'] = summary

    def get_total_cost(self) -> float:
        """Get total cost across all transactions."""
        return self.costs_data.get('summary', {}).get('total_cost', 0.0)

    def get_cost_by_date_range(self, start_date: datetime, end_date: datetime) -> float:
        """
        Get cost for a specific date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Total cost in the date range
        """
        total = 0.0
        for transaction in self.costs_data['transactions']:
            transaction_date = datetime.fromisoformat(transaction['timestamp'])
            if start_date <= transaction_date <= end_date:
                total += transaction['cost_usd']
        return round(total, 6)

    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """
        Get cost for a specific day.

        Args:
            date: Date to query (defaults to today)

        Returns:
            Total cost for that day
        """
        if date is None:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return self.get_cost_by_date_range(start, end)

    def get_yesterday_cost(self) -> float:
        """Get cost for yesterday."""
        yesterday = datetime.now() - timedelta(days=1)
        return self.get_daily_cost(yesterday)

    def get_this_week_cost(self) -> float:
        """Get cost for this week."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_cost_by_date_range(start_of_week, today)

    def get_this_month_cost(self) -> float:
        """Get cost for this month."""
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.get_cost_by_date_range(start_of_month, today)

    def print_summary(self):
        """Print a cost summary."""
        summary = self.costs_data.get('summary', {})

        print("\n" + "=" * 60)
        print("COST SUMMARY")
        print("=" * 60)
        print(f"Total Cost: ${summary.get('total_cost', 0):.6f} USD")
        print(f"Total Transactions: {summary.get('total_transactions', 0)}")
        print()

        if 'by_type' in summary:
            print("By Transaction Type:")
            for t_type, data in summary['by_type'].items():
                print(f"  {t_type.capitalize()}:")
                print(f"    Count: {data['count']}")
                print(f"    Cost: ${data['total_cost']:.6f} USD")
            print()

        print(f"Today: ${self.get_daily_cost():.6f} USD")
        print(f"Yesterday: ${self.get_yesterday_cost():.6f} USD")
        print(f"This Week: ${self.get_this_week_cost():.6f} USD")
        print(f"This Month: ${self.get_this_month_cost():.6f} USD")
        print("=" * 60 + "\n")

    def estimate_rag_storage_cost(self, total_tokens: int) -> Dict:
        """
        Estimate RAG storage and indexing costs.

        Args:
            total_tokens: Total tokens stored

        Returns:
            Dict with cost breakdown
        """
        indexing_cost = total_tokens * self.PRICING['indexing']
        storage_cost = total_tokens * self.PRICING['storage']  # Currently $0

        return {
            'total_tokens': total_tokens,
            'indexing_cost_usd': round(indexing_cost, 6),
            'storage_cost_usd': round(storage_cost, 6),
            'total_cost_usd': round(indexing_cost + storage_cost, 6),
            'note': 'Storage is currently free for Gemini File Search',
        }
