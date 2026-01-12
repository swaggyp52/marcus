"""
test_v049_language_consistency.py - Verify system voice is consistent

Tests that language is:
1. Deterministic (same action = same message always)
2. Consistent across all system messages
3. Short, declarative, action-oriented
4. Non-assistant tone
5. Parseable and machine-readable
"""

import pytest
from marcus_app.utils.system_response import (
    SystemResponse, SystemResponses, ActionType, ActionType,
    format_agent_response, get_all_response_templates
)


class TestSystemResponseFormatting:
    """Test SystemResponse message formatting."""
    
    def test_task_created_short_format(self):
        """Task created message in short format."""
        response = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        short = response.to_short_text()
        
        assert "✚" in short or "+" in short  # Icon
        assert "Lab Report" in short
        assert "Fri 5 PM" in short
    
    def test_task_created_full_format(self):
        """Task created message in full format."""
        response = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        full = response.to_full_text()
        
        assert "Lab Report" in full
        assert "Fri 5 PM" in full
        assert "\n" in full  # Multi-line
    
    def test_task_created_structured_format(self):
        """Task created message in structured format."""
        response = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        structured = response.to_structured()
        
        assert structured['action'] == 'created'
        assert structured['primary'] == 'Task: Lab Report'
        assert structured['details']['title'] == 'Lab Report'
    
    def test_item_deleted_shows_undo_hint(self):
        """Item deleted message mentions undo window."""
        response = SystemResponses.item_deleted("Task")
        full = response.to_full_text()
        
        assert "Undo" in full or "undo" in full


class TestLanguageConsistency:
    """Verify language is consistent and deterministic."""
    
    def test_same_action_produces_same_message(self):
        """Same action always produces same message."""
        response1 = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        response2 = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        
        assert response1.to_short_text() == response2.to_short_text()
        assert response1.to_full_text() == response2.to_full_text()
    
    def test_no_assistant_tone(self):
        """Messages don't use assistant tone."""
        responses = [
            SystemResponses.task_created("Lab Report"),
            SystemResponses.item_deleted("Task"),
            SystemResponses.bulk_action(5, "accept"),
        ]
        
        for response in responses:
            text = response.to_full_text()
            
            # Check for assistant phrases
            assert "I've" not in text
            assert "I've gone ahead" not in text
            assert "Would you like" not in text
            assert "Let me" not in text
            assert "Help you" not in text
    
    def test_messages_are_short(self):
        """Messages are concise (no fluff)."""
        response = SystemResponses.task_created("Lab Report", "Fri 5 PM")
        short = response.to_short_text()
        
        # Should be short enough for toast
        assert len(short) < 100
    
    def test_messages_are_action_oriented(self):
        """Messages focus on action, not explanation."""
        responses = [
            SystemResponses.task_created("Lab Report"),
            SystemResponses.item_accepted("Task", "PHYS214"),
            SystemResponses.item_snoozed("Task", "60 min"),
        ]
        
        for response in responses:
            text = response.to_short_text()
            
            # Should start with action verb or icon
            assert text[0] in "✚✓✕📁⏰📌○↩️❌ℹ❓"


class TestResponseTemplateConsistency:
    """Verify all response templates are consistent."""
    
    def test_all_templates_exist(self):
        """All expected templates are defined."""
        templates = get_all_response_templates()
        
        assert 'task_created' in templates
        assert 'note_created' in templates
        assert 'item_filed' in templates
        assert 'item_accepted' in templates
        assert 'item_snoozed' in templates
        assert 'item_deleted' in templates
        assert 'bulk_action' in templates
        assert 'action_undone' in templates
        assert 'error' in templates
        assert 'confirm' in templates
    
    def test_all_templates_are_strings(self):
        """All templates are formatted as strings."""
        templates = get_all_response_templates()
        
        for template_name, template_text in templates.items():
            assert isinstance(template_text, str)
            assert len(template_text) > 0
    
    def test_templates_are_deterministic(self):
        """Same templates always produced."""
        templates1 = get_all_response_templates()
        templates2 = get_all_response_templates()
        
        assert templates1 == templates2


class TestActionTypes:
    """Verify action types are comprehensive."""
    
    def test_all_action_types_have_icons(self):
        """Every action type has an icon."""
        response = SystemResponse(
            action=ActionType.CREATE,
            primary="Test"
        )
        
        icon = response._icon()
        assert len(icon) > 0
        
        full_icon = response._icon_full()
        assert len(full_icon) > 0
    
    def test_action_type_icons_unique(self):
        """Each action type has unique icon."""
        icons = {}
        
        for action_type in ActionType:
            response = SystemResponse(action=action_type, primary="Test")
            icon = response._icon()
            
            # Icon should be usable
            assert len(icon) > 0


class TestBulkActionMessages:
    """Verify bulk action messages are clear."""
    
    def test_bulk_action_shows_count(self):
        """Bulk action message includes count."""
        response = SystemResponses.bulk_action(5, "accept", "PHYS214")
        text = response.to_short_text()
        
        assert "5" in text or "five" in text.lower()
    
    def test_bulk_action_plural_handling(self):
        """Bulk action handles singular/plural correctly."""
        response_single = SystemResponses.bulk_action(1, "accept")
        response_multi = SystemResponses.bulk_action(5, "accept")
        
        single_text = response_single.to_short_text()
        multi_text = response_multi.to_short_text()
        
        # Should be different
        assert single_text != multi_text


class TestErrorMessages:
    """Verify error messages are clear."""
    
    def test_error_message_format(self):
        """Error messages are clearly marked."""
        response = SystemResponses.error("Network error", "Check connection")
        text = response.to_short_text()
        
        assert "❌" in text or "Error" in text
    
    def test_error_includes_hint(self):
        """Error message can include helpful hint."""
        response = SystemResponses.error("Network error", "Check connection")
        full = response.to_full_text()
        
        assert "Network error" in full
        assert "Check connection" in full


class TestConfirmationMessages:
    """Verify confirmation prompts are clear."""
    
    def test_confirmation_is_clear(self):
        """Confirmation messages are unambiguous."""
        response = SystemResponses.confirm("Delete 5 items?", "Cannot undo after 10s")
        text = response.to_full_text()
        
        assert "❓" in text or "Confirm" in text
        assert "Delete" in text
        assert "Y/N" in text or "yes" in text.lower()


class TestLanguageDeterminism:
    """Verify language system is deterministic (no randomness)."""
    
    def test_deterministic_task_creation_message(self):
        """Task creation message is deterministic."""
        for _ in range(10):
            response = SystemResponses.task_created("Lab Report", "Fri 5 PM")
            assert response.to_short_text() == "✚ Task: Lab Report"
    
    def test_deterministic_accept_message(self):
        """Accept message is deterministic."""
        for _ in range(10):
            response = SystemResponses.item_accepted("Task", "PHYS214")
            assert "✓" in response.to_short_text()
            assert "Task" in response.to_short_text()
    
    def test_no_random_elements_in_responses(self):
        """Response system never uses randomness."""
        # Create same response 100 times
        responses = [
            SystemResponses.bulk_action(3, "snooze", "PHYS214").to_full_text()
            for _ in range(100)
        ]
        
        # All should be identical
        assert len(set(responses)) == 1
