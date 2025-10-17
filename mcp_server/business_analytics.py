"""
Business Analytics

Track and analyze business metrics:
- User engagement
- Feature usage
- Conversion funnels
- Retention analysis
- Revenue metrics
- A/B test results

Features:
- Custom events
- Funnel analysis
- Cohort analysis
- Retention curves
- Attribution models
- Dashboards

Use Cases:
- Product analytics
- User behavior tracking
- Feature adoption
- Churn prediction
- Growth metrics
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Analytics event types"""

    PAGE_VIEW = "page_view"
    FEATURE_USED = "feature_used"
    API_CALL = "api_call"
    CONVERSION = "conversion"
    SIGNUP = "signup"
    PAYMENT = "payment"
    ERROR = "error"


@dataclass
class AnalyticsEvent:
    """Single analytics event"""

    event_id: str
    user_id: str
    event_type: EventType
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSegment:
    """User segment definition"""

    name: str
    criteria: Dict[str, Any]
    user_ids: Set[str] = field(default_factory=set)


class EventCollector:
    """Collect and store analytics events"""

    def __init__(self):
        self.events: List[AnalyticsEvent] = []
        self.user_events: Dict[str, List[AnalyticsEvent]] = defaultdict(list)
        self.total_events = 0

    def track(
        self,
        user_id: str,
        event_type: EventType,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AnalyticsEvent:
        """Track an event"""
        event = AnalyticsEvent(
            event_id=f"event_{self.total_events}",
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now(),
            properties=properties or {},
            session_id=session_id,
        )

        self.events.append(event)
        self.user_events[user_id].append(event)
        self.total_events += 1

        logger.debug(f"Tracked event: {event_type.value} for user {user_id}")
        return event

    def get_user_events(
        self,
        user_id: str,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AnalyticsEvent]:
        """Get events for a user"""
        events = self.user_events.get(user_id, [])

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Filter by time range
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_event_count(
        self,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Get count of events"""
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return len(events)


class FunnelAnalyzer:
    """Analyze conversion funnels"""

    def __init__(self, collector: EventCollector):
        self.collector = collector

    def analyze_funnel(
        self,
        steps: List[EventType],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Analyze a conversion funnel"""

        # Get all users who entered the funnel (completed step 1)
        step1_events = [
            e
            for e in self.collector.events
            if e.event_type == steps[0]
            and (not start_time or e.timestamp >= start_time)
            and (not end_time or e.timestamp <= end_time)
        ]

        users_in_funnel = set(e.user_id for e in step1_events)
        step_counts = [len(users_in_funnel)]
        conversion_rates = [100.0]

        # Track users through each step
        current_users = users_in_funnel

        for step in steps[1:]:
            # Find users who completed this step
            completed_users = set()
            for user_id in current_users:
                user_events = self.collector.get_user_events(
                    user_id, event_type=step, start_time=start_time, end_time=end_time
                )
                if user_events:
                    completed_users.add(user_id)

            step_counts.append(len(completed_users))
            conversion_rate = (
                (len(completed_users) / len(users_in_funnel) * 100)
                if users_in_funnel
                else 0
            )
            conversion_rates.append(conversion_rate)

            current_users = completed_users

        # Calculate drop-off
        drop_offs = []
        for i in range(len(step_counts) - 1):
            drop_off = step_counts[i] - step_counts[i + 1]
            drop_off_rate = (
                (drop_off / step_counts[i] * 100) if step_counts[i] > 0 else 0
            )
            drop_offs.append(
                {
                    "from_step": steps[i].value,
                    "to_step": steps[i + 1].value,
                    "users_dropped": drop_off,
                    "drop_off_rate": round(drop_off_rate, 2),
                }
            )

        return {
            "funnel_steps": [s.value for s in steps],
            "users_at_each_step": step_counts,
            "conversion_rates": [round(r, 2) for r in conversion_rates],
            "overall_conversion_rate": round(conversion_rates[-1], 2),
            "drop_offs": drop_offs,
            "total_users_entered": len(users_in_funnel),
            "total_users_converted": step_counts[-1],
        }


class CohortAnalyzer:
    """Analyze user cohorts"""

    def __init__(self, collector: EventCollector):
        self.collector = collector

    def analyze_retention(
        self,
        cohort_event: EventType,
        return_event: EventType,
        period_days: int = 7,
        num_periods: int = 4,
    ) -> Dict[str, Any]:
        """Analyze retention cohorts"""

        # Group users by cohort (when they first did cohort_event)
        cohorts: Dict[str, Set[str]] = defaultdict(set)

        for event in self.collector.events:
            if event.event_type == cohort_event:
                # Group by week
                week_start = event.timestamp - timedelta(days=event.timestamp.weekday())
                cohort_key = week_start.strftime("%Y-%m-%d")
                cohorts[cohort_key].add(event.user_id)

        # Calculate retention for each cohort
        retention_data = {}

        for cohort_date, users in sorted(cohorts.items())[:5]:  # Last 5 cohorts
            cohort_start = datetime.strptime(cohort_date, "%Y-%m-%d")
            retention = [100.0]  # Week 0 is always 100%

            for period in range(1, num_periods + 1):
                period_start = cohort_start + timedelta(days=period * period_days)
                period_end = period_start + timedelta(days=period_days)

                # Count users who returned
                returned_users = 0
                for user_id in users:
                    user_events = self.collector.get_user_events(
                        user_id,
                        event_type=return_event,
                        start_time=period_start,
                        end_time=period_end,
                    )
                    if user_events:
                        returned_users += 1

                retention_rate = (returned_users / len(users) * 100) if users else 0
                retention.append(round(retention_rate, 2))

            retention_data[cohort_date] = {
                "cohort_size": len(users),
                "retention": retention,
            }

        return {
            "period_days": period_days,
            "num_periods": num_periods,
            "cohorts": retention_data,
        }


class FeatureUsageTracker:
    """Track feature usage and adoption"""

    def __init__(self, collector: EventCollector):
        self.collector = collector

    def get_feature_usage(
        self,
        feature_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage stats for a feature"""

        # Get all feature usage events
        feature_events = [
            e
            for e in self.collector.events
            if e.event_type == EventType.FEATURE_USED
            and e.properties.get("feature_name") == feature_name
            and (not start_time or e.timestamp >= start_time)
            and (not end_time or e.timestamp <= end_time)
        ]

        # Count unique users
        unique_users = set(e.user_id for e in feature_events)

        # Count by user
        usage_by_user: Dict[str, int] = defaultdict(int)
        for event in feature_events:
            usage_by_user[event.user_id] += 1

        # Calculate adoption over time
        if feature_events:
            first_use = min(e.timestamp for e in feature_events)
            last_use = max(e.timestamp for e in feature_events)
        else:
            first_use = last_use = None

        return {
            "feature_name": feature_name,
            "total_uses": len(feature_events),
            "unique_users": len(unique_users),
            "avg_uses_per_user": (
                round(len(feature_events) / len(unique_users), 2) if unique_users else 0
            ),
            "first_use": first_use.isoformat() if first_use else None,
            "last_use": last_use.isoformat() if last_use else None,
            "power_users": sorted(
                [
                    {"user_id": uid, "count": count}
                    for uid, count in usage_by_user.items()
                ],
                key=lambda x: x["count"],
                reverse=True,
            )[
                :10
            ],  # Top 10 users
        }

    def get_adoption_rate(
        self, feature_name: str, total_users: int, period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate feature adoption rate"""

        end_time = datetime.now()
        start_time = end_time - timedelta(days=period_days)

        usage = self.get_feature_usage(feature_name, start_time, end_time)

        adoption_rate = (
            (usage["unique_users"] / total_users * 100) if total_users > 0 else 0
        )

        return {
            "feature_name": feature_name,
            "period_days": period_days,
            "unique_users": usage["unique_users"],
            "total_users": total_users,
            "adoption_rate": round(adoption_rate, 2),
            "total_uses": usage["total_uses"],
        }


class BusinessAnalytics:
    """Main business analytics coordinator"""

    def __init__(self):
        self.collector = EventCollector()
        self.funnel_analyzer = FunnelAnalyzer(self.collector)
        self.cohort_analyzer = CohortAnalyzer(self.collector)
        self.feature_tracker = FeatureUsageTracker(self.collector)

    def track(
        self,
        user_id: str,
        event_type: EventType,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an analytics event"""
        self.collector.track(user_id, event_type, properties)

    def get_dashboard_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get key dashboard metrics"""

        end_time = datetime.now()
        start_time = end_time - timedelta(days=period_days)

        # Total events
        total_events = self.collector.get_event_count(start_time=start_time)

        # Unique users
        unique_users = set(
            e.user_id for e in self.collector.events if e.timestamp >= start_time
        )

        # Events by type
        events_by_type = {}
        for event_type in EventType:
            count = self.collector.get_event_count(
                event_type=event_type, start_time=start_time
            )
            if count > 0:
                events_by_type[event_type.value] = count

        # Conversions
        conversions = self.collector.get_event_count(
            event_type=EventType.CONVERSION, start_time=start_time
        )

        return {
            "period_days": period_days,
            "total_events": total_events,
            "unique_users": len(unique_users),
            "events_per_user": (
                round(total_events / len(unique_users), 2) if unique_users else 0
            ),
            "events_by_type": events_by_type,
            "total_conversions": conversions,
            "conversion_rate": (
                round(conversions / len(unique_users) * 100, 2) if unique_users else 0
            ),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Business Analytics Demo ===\n")

    # Create analytics
    analytics = BusinessAnalytics()

    # Simulate user events
    print("--- Simulating User Events ---\n")

    # User journey: signup -> feature_used -> conversion
    users = [f"user_{i}" for i in range(100)]

    for i, user in enumerate(users):
        # All users sign up
        analytics.track(user, EventType.SIGNUP)

        # 80% use feature
        if i < 80:
            analytics.track(
                user, EventType.FEATURE_USED, {"feature_name": "player_stats"}
            )

        # 50% convert
        if i < 50:
            analytics.track(user, EventType.CONVERSION, {"type": "premium"})

    print(f"✓ Tracked events for {len(users)} users")

    # Funnel analysis
    print("\n--- Conversion Funnel ---\n")
    funnel = analytics.funnel_analyzer.analyze_funnel(
        [EventType.SIGNUP, EventType.FEATURE_USED, EventType.CONVERSION]
    )

    print(f"Funnel: {' -> '.join(funnel['funnel_steps'])}")
    print(f"Users at each step: {funnel['users_at_each_step']}")
    print(f"Conversion rates: {funnel['conversion_rates']}%")
    print(f"Overall conversion: {funnel['overall_conversion_rate']}%")

    # Feature usage
    print("\n--- Feature Usage ---\n")
    usage = analytics.feature_tracker.get_feature_usage("player_stats")
    print(f"Feature: {usage['feature_name']}")
    print(f"Total uses: {usage['total_uses']}")
    print(f"Unique users: {usage['unique_users']}")
    print(f"Avg uses per user: {usage['avg_uses_per_user']}")

    # Dashboard
    print("\n--- Dashboard Metrics (Last 30 Days) ---\n")
    metrics = analytics.get_dashboard_metrics(period_days=30)
    print(f"Total events: {metrics['total_events']}")
    print(f"Unique users: {metrics['unique_users']}")
    print(f"Events per user: {metrics['events_per_user']}")
    print(f"Conversion rate: {metrics['conversion_rate']}%")

    print("\nEvents by type:")
    for event_type, count in metrics["events_by_type"].items():
        print(f"  {event_type}: {count}")

    print("\n=== Demo Complete ===")
