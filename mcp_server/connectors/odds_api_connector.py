import requests
from typing import List, Dict, Any


class OddsAPIConnector:
    """A connector for fetching data from the Odds API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/",
    ):
        self.api_key = api_key
        self.base_url = base_url

    def get_odds(self) -> List[Dict[str, Any]]:
        """Fetches the latest odds for NBA games."""
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads",
            "oddsFormat": "decimal",
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds: {e}")
            return []
