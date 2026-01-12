"""
Test v0.48: What's Next Determinism

Ensures "what's next?" returns deterministic, ranked results.
"""

import pytest
from datetime import datetime, timedelta
from marcus_app.core.database import db
from marcus_app.services.next_action_service import NextActionService
from marcus_app.models import Item, Mission, MissionBox

class TestWhatsNextDeterminism:
    
    def setup_method(self):
        """Set up test data"""
        self.service = NextActionService()
        # Create test items with various states
        
    def test_overdue_deadline_priority(self):
        """Overdue deadlines should rank first"""
        # Create overdue item
        overdue = Item(
            title="Past Due Task",
            due_date=datetime.now() - timedelta(days=1),
            status="todo"
        )
        db.session.add(overdue)
        
        # Create future item
        future = Item(
            title="Future Task",
            due_date=datetime.now() + timedelta(days=5),
            status="todo"
        )
        db.session.add(future)
        db.session.commit()
        
        result = self.service.get_next_actions()
        
        assert result[0]['item']['id'] == overdue.id
        assert result[0]['reason'] == 'overdue'

    def test_due_48h_priority(self):
        """Items due in next 48h should rank second"""
        now = datetime.now()
        
        # Create item due in 24h
        soon = Item(
            title="Due Soon",
            due_date=now + timedelta(hours=24),
            status="todo"
        )
        db.session.add(soon)
        
        # Create item due in 5 days
        later = Item(
            title="Due Later",
            due_date=now + timedelta(days=5),
            status="todo"
        )
        db.session.add(later)
        db.session.commit()
        
        result = self.service.get_next_actions(limit=2)
        
        assert result[0]['item']['id'] == soon.id
        assert result[0]['reason'] == 'due_soon'

    def test_pinned_items_rank_high(self):
        """Pinned inbox items should be in top 3"""
        pinned = Item(
            title="Pinned Item",
            context="inbox",
            pinned=True,
            status="inbox"
        )
        db.session.add(pinned)
        db.session.commit()
        
        result = self.service.get_next_actions()
        pinned_ids = [r['item']['id'] for r in result]
        
        assert pinned.id in pinned_ids

    def test_blocked_mission_with_runnable_box(self):
        """Blocked mission with runnable next box should be actionable"""
        mission = Mission(
            title="Test Mission",
            status="blocked"
        )
        db.session.add(mission)
        db.session.commit()
        
        # Create runnable box
        box = MissionBox(
            mission_id=mission.id,
            title="Next Step",
            status="todo",
            is_blocking=False
        )
        db.session.add(box)
        db.session.commit()
        
        result = self.service.get_next_actions()
        
        mission_results = [r for r in result if r['type'] == 'mission']
        assert len(mission_results) > 0

    def test_deterministic_order_same_db_state(self):
        """Same DB state should always produce same ranking"""
        # Set up state
        item1 = Item(
            title="Task 1",
            due_date=datetime.now() + timedelta(hours=12),
            status="todo"
        )
        item2 = Item(
            title="Task 2",
            due_date=datetime.now() + timedelta(hours=24),
            status="todo"
        )
        db.session.add(item1)
        db.session.add(item2)
        db.session.commit()
        
        # Get results twice
        result1 = self.service.get_next_actions()
        result2 = self.service.get_next_actions()
        
        # Should be identical
        assert [r['item']['id'] for r in result1] == [r['item']['id'] for r in result2]
        assert [r['reason'] for r in result1] == [r['reason'] for r in result2]

    def test_recommended_action_button(self):
        """Top action should have action button suggestions"""
        item = Item(
            title="Do This",
            due_date=datetime.now() + timedelta(hours=2),
            status="todo"
        )
        db.session.add(item)
        db.session.commit()
        
        result = self.service.get_next_actions()
        
        assert 'buttons' in result[0]
        assert len(result[0]['buttons']) > 0
        assert any(b['action'] == 'open' for b in result[0]['buttons'])

    def test_no_future_items_only(self):
        """If only future items exist, return top 3 by due date"""
        dates = [
            datetime.now() + timedelta(days=i) 
            for i in range(1, 6)
        ]
        
        for date in dates:
            item = Item(
                title=f"Item {date.day}",
                due_date=date,
                status="todo"
            )
            db.session.add(item)
        db.session.commit()
        
        result = self.service.get_next_actions(limit=3)
        
        # Should return 3 items in due date order
        assert len(result) == 3
        for i in range(len(result) - 1):
            current_date = result[i]['item']['due_date']
            next_date = result[i+1]['item']['due_date']
            assert current_date <= next_date
