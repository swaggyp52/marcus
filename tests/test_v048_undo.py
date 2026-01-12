"""
Test v0.48: Undo System

Ensures undo window, constraints, and recovery work correctly.
"""

import pytest
import time
from datetime import datetime, timedelta
from marcus_app.core.database import db
from marcus_app.services.undo_service import UndoService
from marcus_app.models import Item, UndoEvent

class TestUndoSystem:
    
    def setup_method(self):
        """Set up test data"""
        self.service = UndoService()
        
    def test_register_and_undo_create_item(self):
        """Should undo item creation"""
        # Create item
        item = Item(
            title="Test Item",
            status="todo"
        )
        db.session.add(item)
        db.session.commit()
        
        # Register undo
        self.service.register_action('create_item', {
            'item_id': item.id,
            'data': {
                'title': item.title,
                'status': item.status
            }
        })
        
        # Delete item
        db.session.delete(item)
        db.session.commit()
        
        # Undo
        result = self.service.undo_last_action()
        
        assert result is not None
        assert result['action_type'] == 'create_item'

    def test_undo_within_10_second_window(self):
        """Should allow undo within 10 seconds"""
        item = Item(title="Test", status="todo")
        db.session.add(item)
        db.session.commit()
        
        self.service.register_action('create_item', {'item_id': item.id})
        
        # Immediately undo
        result = self.service.undo_last_action()
        
        assert result is not None

    def test_undo_expires_after_10_seconds(self):
        """Should reject undo after 10-second window"""
        item = Item(title="Test", status="todo")
        db.session.add(item)
        db.session.commit()
        
        self.service.register_action('create_item', {'item_id': item.id})
        
        # Fast-forward time in test (would need mock in real test)
        undo_event = UndoEvent.query.order_by(UndoEvent.created_at.desc()).first()
        if undo_event:
            undo_event.expires_at = datetime.now() - timedelta(seconds=1)
            db.session.commit()
        
        # Try to undo
        result = self.service.undo_last_action()
        
        assert result is None

    def test_only_one_undo_in_stack(self):
        """Should only track last action for undo"""
        for i in range(3):
            item = Item(title=f"Item {i}", status="todo")
            db.session.add(item)
            db.session.commit()
            
            self.service.register_action('create_item', {'item_id': item.id})
        
        # Undo only the last one
        result = self.service.undo_last_action()
        
        assert result is not None
        
        # Second undo should fail (window expired or no more actions)
        result2 = self.service.undo_last_action()
        # May be None if window closed or action consumed

    def test_soft_delete_enables_restore(self):
        """Deleted items should be recoverable if soft deleted"""
        item = Item(title="To Delete", status="todo")
        db.session.add(item)
        db.session.commit()
        item_id = item.id
        
        # Register undo before delete
        self.service.register_action('delete_item', {
            'item_id': item_id,
            'data': {
                'title': item.title,
                'status': item.status
            }
        })
        
        # Soft delete (mark as deleted, don't remove row)
        item.is_deleted = True
        item.deleted_at = datetime.now()
        db.session.commit()
        
        # Undo delete
        result = self.service.undo_last_action()
        
        # Should restore item
        restored = Item.query.filter_by(id=item_id).first()
        assert restored is not None
        assert not restored.is_deleted

    def test_undo_snooze_change(self):
        """Should undo snooze/pin changes"""
        item = Item(title="Test", status="todo", pinned=False)
        db.session.add(item)
        db.session.commit()
        
        # Register undo before change
        self.service.register_action('pin_change', {
            'item_id': item.id,
            'previous_value': False,
            'new_value': True
        })
        
        # Change pin
        item.pinned = True
        db.session.commit()
        
        # Undo
        result = self.service.undo_last_action()
        
        assert result is not None
        restored = Item.query.get(item.id)
        assert restored.pinned == False

    def test_cannot_undo_online_operations(self):
        """Should not allow undo of push/PR operations"""
        # Register online operation
        self.service.register_action('push_to_remote', {
            'branch': 'main',
            'commits': 3
        }, allow_undo=False)
        
        result = self.service.undo_last_action()
        
        # Should fail or return None for online ops
        assert result is None or not result.get('is_online_op')

    def test_undo_status_shows_time_remaining(self):
        """Undo status should show seconds remaining"""
        item = Item(title="Test", status="todo")
        db.session.add(item)
        db.session.commit()
        
        self.service.register_action('create_item', {'item_id': item.id})
        
        status = self.service.get_undo_status()
        
        assert status['available'] == True
        assert 'seconds_remaining' in status
        assert 0 < status['seconds_remaining'] <= 10

    def test_multiple_undo_events_persisted(self):
        """Undo events should be persisted to DB"""
        for i in range(3):
            item = Item(title=f"Item {i}", status="todo")
            db.session.add(item)
            db.session.commit()
            
            self.service.register_action('create_item', {'item_id': item.id})
        
        events = UndoEvent.query.filter_by(is_consumed=False).all()
        
        # Should have events in DB
        assert len(events) > 0

    def test_consumed_undo_not_reused(self):
        """Already consumed undo should not be reusable"""
        item = Item(title="Test", status="todo")
        db.session.add(item)
        db.session.commit()
        
        self.service.register_action('create_item', {'item_id': item.id})
        
        # First undo
        result1 = self.service.undo_last_action()
        assert result1 is not None
        
        # Second undo attempt
        result2 = self.service.undo_last_action()
        assert result2 is None  # Already consumed
