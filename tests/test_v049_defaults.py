"""
test_v049_defaults.py - Verify opinionated defaults work correctly

Tests that defaults are:
1. Deterministic (same DB state = same defaults)
2. Applied consistently
3. Overrideable by user
4. Reduce friction as intended
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock
from marcus_app.services.defaults_service import DefaultsService


class TestTaskDefaults:
    """Task default behavior."""
    
    def test_task_defaults_to_today_if_no_date(self):
        """Task with no due_date defaults to TODAY."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        task_data = {'title': 'Lab Report'}
        result = service.apply_task_defaults(task_data)
        
        assert result['due_date'] == date.today()
    
    def test_task_respects_explicit_date(self):
        """Task with explicit due_date is preserved."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        explicit_date = date(2026, 1, 15)
        task_data = {'title': 'Lab Report', 'due_date': explicit_date}
        result = service.apply_task_defaults(task_data)
        
        assert result['due_date'] == explicit_date
    
    def test_task_defaults_to_last_active_context(self):
        """Task defaults to last active context if none specified."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        # Mock last context
        mock_context = Mock(id=42)
        service._get_last_active_context = Mock(return_value=mock_context)
        
        task_data = {'title': 'Lab Report'}
        result = service.apply_task_defaults(task_data)
        
        assert result['context_id'] == 42
    
    def test_task_defaults_to_normal_priority(self):
        """Task defaults to normal priority if not specified."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        task_data = {'title': 'Lab Report'}
        result = service.apply_task_defaults(task_data)
        
        assert result['priority'] == 'normal'
    
    def test_task_respects_explicit_priority(self):
        """Task with explicit priority is preserved."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        task_data = {'title': 'Lab Report', 'priority': 'high'}
        result = service.apply_task_defaults(task_data)
        
        assert result['priority'] == 'high'


class TestNoteDefaults:
    """Note default behavior."""
    
    def test_note_defaults_to_last_active_context(self):
        """Note defaults to last active context."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        mock_context = Mock(id=42)
        service._get_last_active_context = Mock(return_value=mock_context)
        
        note_data = {'title': 'Meeting notes'}
        result = service.apply_note_defaults(note_data)
        
        assert result['context_id'] == 42
    
    def test_note_respects_explicit_context(self):
        """Note with explicit context is preserved."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        note_data = {'title': 'Meeting notes', 'context_id': 99}
        result = service.apply_note_defaults(note_data)
        
        assert result['context_id'] == 99


class TestFileDefaults:
    """File default behavior."""
    
    def test_file_defaults_to_inbox(self):
        """File defaults to Inbox if no context specified."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        mock_inbox = Mock(id=1)
        service._get_inbox_context = Mock(return_value=mock_inbox)
        
        file_data = {'title': 'Important.pdf'}
        result = service.apply_file_defaults(file_data)
        
        assert result['context_id'] == 1
    
    def test_file_auto_marks_for_filing_on_high_confidence(self):
        """File with ≥90% confidence auto-marked for filing."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        file_data = {
            'title': 'Lab Report.pdf',
            'confidence_score': 0.95
        }
        result = service.apply_file_defaults(file_data)
        
        assert result['auto_file'] == True


class TestMissionDefaults:
    """Mission default behavior."""
    
    def test_mission_defaults_to_last_template(self):
        """Mission defaults to last used template."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        service._get_last_used_template = Mock(return_value=42)
        
        mission_data = {'title': 'New mission'}
        result = service.apply_mission_defaults(mission_data)
        
        assert result['template_id'] == 42
    
    def test_mission_defaults_to_medium_duration(self):
        """Mission defaults to 2 weeks (14 days)."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        mission_data = {'title': 'New mission'}
        result = service.apply_mission_defaults(mission_data)
        
        assert result['duration_days'] == 14


class TestQuickAddDefaults:
    """Quick Add auto-accept behavior."""
    
    def test_should_auto_accept_on_90_percent_confidence(self):
        """Should auto-accept when confidence ≥ 90%."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        item_data = {
            'type': 'task',
            'confidence_score': 0.90,
            'is_mission': False
        }
        
        assert service.should_auto_accept(item_data) == True
    
    def test_should_not_auto_accept_below_threshold(self):
        """Should not auto-accept below 90%."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        item_data = {
            'type': 'task',
            'confidence_score': 0.89,
            'is_mission': False
        }
        
        assert service.should_auto_accept(item_data) == False
    
    def test_should_not_auto_accept_files(self):
        """Should not auto-accept file type."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        item_data = {
            'type': 'file',
            'confidence_score': 0.95,
            'is_mission': False
        }
        
        assert service.should_auto_accept(item_data) == False
    
    def test_should_not_auto_accept_missions(self):
        """Should not auto-accept missions."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        item_data = {
            'type': 'task',
            'confidence_score': 0.95,
            'is_mission': True
        }
        
        assert service.should_auto_accept(item_data) == False


class TestDefaultsDeterminism:
    """Verify defaults are deterministic."""
    
    def test_get_all_defaults_returns_consistent_structure(self):
        """get_all_defaults returns consistent structure."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        # Mock helper methods
        mock_context = Mock(id=42)
        service._get_last_active_context = Mock(return_value=mock_context)
        service._get_inbox_context = Mock(return_value=mock_context)
        service._get_last_used_template = Mock(return_value=10)
        
        defaults = service.get_all_defaults()
        
        # Same structure always
        assert 'task' in defaults
        assert 'note' in defaults
        assert 'file' in defaults
        assert 'mission' in defaults
        assert 'quick_add_auto_accept_threshold' in defaults
        
        # Calling again returns same values
        defaults2 = service.get_all_defaults()
        assert defaults == defaults2


class TestDefaultsConsistency:
    """Verify defaults reduce friction."""
    
    def test_defaults_reduce_required_input(self):
        """Defaults allow minimal input to create item."""
        db = Mock()
        service = DefaultsService(db, user_id=1)
        
        mock_context = Mock(id=42)
        service._get_last_active_context = Mock(return_value=mock_context)
        
        # Minimal input
        task_data = {'title': 'Lab Report'}
        result = service.apply_task_defaults(task_data)
        
        # Should have sensible defaults without user input
        assert result['due_date'] is not None
        assert result['context_id'] is not None
        assert result['priority'] is not None
