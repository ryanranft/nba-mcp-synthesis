"""
Cost tracking and budget management for API calls
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

class CostTracker:
    """Track API costs across analysis runs"""

    def __init__(self, budget: float = 50.0, log_file: str = "logs/cost_tracking.json"):
        self.budget = budget
        self.total_spent = 0.0
        self.costs_by_model = {
            "google": 0.0,
            "deepseek": 0.0,
            "claude": 0.0,
            "gpt4": 0.0
        }
        self.log_file = log_file
        self.session_start = datetime.now()

        # Load existing costs if log file exists
        self._load_existing_costs()

    def _load_existing_costs(self):
        """Load existing costs from log file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.total_spent = data.get('total_spent', 0.0)
                    self.costs_by_model = data.get('costs_by_model', self.costs_by_model)
            except Exception as e:
                print(f"Warning: Could not load existing costs: {e}")

    def add_cost(self, model: str, cost: float, operation: str = "analysis"):
        """Add cost for a model"""
        self.total_spent += cost
        self.costs_by_model[model] += cost

        # Log the cost
        self._log_cost(model, cost, operation)

        # Check budget
        if self.total_spent > self.budget:
            raise ValueError(f"Budget exceeded: ${self.total_spent:.2f} > ${self.budget:.2f}")

        # Warn if approaching budget
        remaining = self.budget - self.total_spent
        if remaining < 5.0:
            print(f"⚠️ Warning: Only ${remaining:.2f} remaining in budget")

    def _log_cost(self, model: str, cost: float, operation: str):
        """Log cost to file"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "cost": cost,
            "operation": operation,
            "total_spent": self.total_spent
        }

        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Warning: Could not log cost: {e}")

    def get_summary(self) -> str:
        """Get cost summary"""
        remaining = self.budget - self.total_spent
        percentage = (self.total_spent / self.budget) * 100 if self.budget > 0 else 0

        return f"""
💰 Cost Summary:
  Total: ${self.total_spent:.4f} / ${self.budget:.2f} ({percentage:.1f}%)
  Google: ${self.costs_by_model['google']:.4f}
  DeepSeek: ${self.costs_by_model['deepseek']:.4f}
  Claude: ${self.costs_by_model['claude']:.4f}
  GPT-4: ${self.costs_by_model['gpt4']:.4f}
  Remaining: ${remaining:.2f}
  Session Duration: {datetime.now() - self.session_start}
"""

    def get_budget_status(self) -> str:
        """Get budget status with recommendations"""
        remaining = self.budget - self.total_spent
        percentage = (self.total_spent / self.budget) * 100 if self.budget > 0 else 0

        if percentage < 25:
            status = "🟢 Budget healthy"
        elif percentage < 75:
            status = "🟡 Budget moderate"
        elif percentage < 95:
            status = "🟠 Budget low"
        else:
            status = "🔴 Budget critical"

        return f"{status} - {percentage:.1f}% used, ${remaining:.2f} remaining"

    def estimate_remaining_books(self, avg_cost_per_book: float = 0.15) -> int:
        """Estimate how many more books can be analyzed"""
        remaining = self.budget - self.total_spent
        return int(remaining / avg_cost_per_book) if avg_cost_per_book > 0 else 0




