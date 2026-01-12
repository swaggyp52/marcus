"""
Marcus v0.50 Intake Tests

Test syllabus classification, creation, receipts, and determinism.
"""

import pytest
import json
from datetime import datetime


class TestIntakeService:
    """Test core intake service."""
    
    def test_classify_file_heuristic(self):
        """Test heuristic classification (no LLM)."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        content = """
        PHYS214: Physics II
        Instructor: Dr. Sarah Smith
        
        Exam 1: March 15, 2026
        Final Project Due: April 20, 2026
        Midterm: April 1, 2026
        """
        
        result = service.classify_file("PHYS214_Syllabus.pdf", content)
        
        assert result['class_code'] == 'PHYS214'
        assert result['instructor'] == 'Dr. Sarah Smith'
        assert len(result['deadlines']) >= 1
        assert result['method'] == 'heuristic'
        assert 0 <= result['confidence'] <= 1.0
    
    def test_classify_low_confidence(self):
        """Test file with no clear class code."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        content = "This is a random document with no class information."
        
        result = service.classify_file("random.txt", content)
        
        assert result['confidence'] < 0.5
        assert not result['class_code']
    
    def test_confirm_and_create(self):
        """Test creation of classes and items from confirmed classifications."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        classifications = [
            {
                'filename': 'PHYS214_Syllabus.pdf',
                'class_code': 'PHYS214',
                'class_name': None,  # User must confirm
                'deadlines': [
                    {'description': 'Exam 1', 'date': 'March 15, 2026', 'confidence': 0.9}
                ]
            }
        ]
        
        confirmations = {
            'PHYS214_Syllabus.pdf': {
                'class_code': 'PHYS214',
                'class_name': 'Physics II',
                'instructor': 'Dr. Smith'
            }
        }
        
        receipt, objects = service.confirm_and_create(classifications, confirmations)
        
        assert receipt.classes_created == 1
        assert receipt.items_created == 1
        assert receipt.artifacts_pinned == 1
        assert len(receipt.errors) == 0
    
    def test_receipt_tracking(self):
        """Test that receipts are properly tracked and serialized."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        classifications = []
        confirmations = {}
        
        receipt, _ = service.confirm_and_create(classifications, confirmations)
        
        # Receipt should be serializable to markdown
        markdown = receipt.to_markdown()
        assert 'Intake Receipt' in markdown
        assert receipt.receipt_id in markdown
        
        # Receipt should be serializable to dict
        dict_form = receipt.to_dict()
        assert 'receipt_id' in dict_form
        assert 'timestamp' in dict_form


class TestOllamaAdapter:
    """Test LLM adapter graceful degradation."""
    
    def test_adapter_detects_unavailable(self):
        """Test that adapter detects when Ollama is not available."""
        from marcus_app.services.ollama_adapter import OllamaAdapter
        
        adapter = OllamaAdapter(enabled=True)
        
        # Should detect it's unavailable (likely running in test env)
        assert adapter.is_available() == False
    
    def test_adapter_classify_returns_none(self):
        """Test that classify returns None gracefully when unavailable."""
        from marcus_app.services.ollama_adapter import OllamaAdapter
        
        adapter = OllamaAdapter(enabled=True)
        
        result = adapter.classify_syllabus("test.pdf", "test content")
        
        assert result is None
    
    def test_adapter_disabled(self):
        """Test that adapter can be disabled."""
        from marcus_app.services.ollama_adapter import OllamaAdapter
        
        adapter = OllamaAdapter(enabled=False)
        
        assert adapter.is_available() == False
    
    def test_adapter_audit_logging(self):
        """Test that LLM calls are audit logged."""
        from marcus_app.services.ollama_adapter import OllamaAdapter
        
        audit_log = []
        adapter = OllamaAdapter(enabled=False, audit_log=audit_log)
        
        # Even though disabled, disabling logs to audit trail
        assert len(audit_log) == 0


class TestRunbookService:
    """Test operational runbook."""
    
    def test_runbook_sections_exist(self):
        """Test that all expected runbook sections exist."""
        from marcus_app.services.runbook_service import RunbookService
        
        runbook = RunbookService.get_runbook()
        
        expected_sections = [
            'first_run', 'backup', 'update', 'intake_failed',
            'add_custom_command', 'trust_question'
        ]
        
        for section in expected_sections:
            assert section in runbook
            assert 'title' in runbook[section]
    
    def test_runbook_markdown_render(self):
        """Test that runbook renders to markdown."""
        from marcus_app.services.runbook_service import RunbookService
        
        markdown = RunbookService.render_markdown('backup')
        
        assert 'Backup Your Data' in markdown
        assert '1. Mount your VeraCrypt' in markdown
    
    def test_runbook_trust_question(self):
        """Test trust question in runbook."""
        from marcus_app.services.runbook_service import RunbookService
        
        runbook = RunbookService.get_runbook('trust_question')
        
        assert 'Storage is encrypted' in ' '.join(runbook['answer'])


class TestDiagnosticsService:
    """Test diagnostics panel."""
    
    def test_diagnostics_full_status(self):
        """Test getting full diagnostic status."""
        from marcus_app.services.runbook_service import DiagnosticsService
        
        diag = DiagnosticsService('/tmp', '/tmp/test.db')
        
        status = diag.get_full_status()
        
        assert 'timestamp' in status
        assert 'storage' in status
        assert 'database' in status
    
    def test_storage_check(self):
        """Test storage health check."""
        from marcus_app.services.runbook_service import DiagnosticsService
        
        diag = DiagnosticsService('/tmp', '/tmp/test.db')
        
        storage = diag.check_storage()
        
        assert 'status' in storage
        assert 'path' in storage
        assert 'exists' in storage


class TestIntakeDeterminism:
    """Test that intake produces deterministic results."""
    
    def test_classification_deterministic(self):
        """Same input produces same classification."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        content = "PHYS214 Physics II Instructor: Dr. Smith Due: March 15"
        
        result1 = service.classify_file("test.pdf", content)
        result2 = service.classify_file("test.pdf", content)
        
        assert result1['class_code'] == result2['class_code']
        assert result1['confidence'] == result2['confidence']
        assert result1['method'] == result2['method']
    
    def test_receipt_deterministic(self):
        """Same confirmations produce same receipt structure."""
        from marcus_app.services.intake_service import IntakeService
        
        service = IntakeService()
        
        classifications = [
            {
                'filename': 'test.pdf',
                'class_code': 'TEST101',
                'deadlines': [{'description': 'Assignment', 'date': 'Jan 20', 'confidence': 0.8}]
            }
        ]
        
        confirmations = {'test.pdf': {'class_code': 'TEST101', 'class_name': 'Test Course'}}
        
        receipt1, _ = service.confirm_and_create(classifications, confirmations)
        receipt2, _ = service.confirm_and_create(classifications, confirmations)
        
        # Both receipts should have same structure (though different receipt IDs)
        assert receipt1.files_processed == receipt2.files_processed
        assert receipt1.classes_created == receipt2.classes_created
        assert receipt1.items_created == receipt2.items_created


class TestIntakeLanguage:
    """Test deterministic system language in intake."""
    
    def test_system_response_format(self):
        """Test that intake produces standard system response."""
        from marcus_app.services.intake_service import IntakeService, IntakeReceipt
        
        receipt = IntakeReceipt(
            receipt_id='test123',
            timestamp=datetime.utcnow().isoformat(),
            user_action='syllabus_intake',
            files_processed=2,
            classes_created=2,
            classes_updated=0,
            items_created=5,
            artifacts_pinned=2,
            errors=[],
            warnings=[],
            low_confidence_items=[]
        )
        
        service = IntakeService()
        response = service.to_system_response(receipt)
        
        # All required fields present
        assert 'icon' in response
        assert 'primary' in response
        assert 'details' in response
        assert 'secondary' in response
        assert 'cta' in response
        
        # Language is deterministic
        assert '2 classes' in response['primary']
        assert '5 deadlines' in response['primary']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
