"""
Marcus v0.50: Ollama LLM Adapter

Graceful offline-first LLM integration.
- Detects local Ollama availability
- Fails closed (no network calls)
- Structured JSON outputs
- Audit logged
- Completely optional (intake still works without it)
"""

import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class OllamaAdapter:
    """
    Connects to local Ollama instance if available.
    Strictly offline-first. No fallback to cloud.
    """
    
    # Configuration
    OLLAMA_HOST = "http://localhost:11434"
    MODEL = "mistral"  # fast, good extraction
    TIMEOUT = 30  # seconds
    
    def __init__(self, enabled: bool = True, audit_log: Optional[List] = None):
        """
        Initialize Ollama adapter.
        
        Args:
            enabled: allow LLM usage if available
            audit_log: reference to audit trail (for logging LLM calls)
        """
        self.enabled = enabled
        self.available = False
        self.audit_log = audit_log or []
        self.is_online_mode = False  # must be explicitly enabled
        
        # Auto-detect on init
        self._detect_availability()
    
    def _detect_availability(self) -> bool:
        """
        Check if Ollama is running locally.
        Does NOT attempt network fallback.
        """
        if not self.enabled:
            self.available = False
            return False
        
        try:
            resp = requests.get(f"{self.OLLAMA_HOST}/api/tags", timeout=2)
            self.available = (resp.status_code == 200)
            if self.available:
                self._log_audit("ollama_detected", {"status": "available"})
            return self.available
        except (requests.ConnectionError, requests.Timeout):
            self.available = False
            return False
    
    def is_available(self) -> bool:
        """True if local Ollama is running."""
        return self.available
    
    def set_online_mode(self, enabled: bool) -> None:
        """
        Explicitly enable/disable online mode.
        Only affects behavior if is_online_mode changes.
        """
        was_online = self.is_online_mode
        self.is_online_mode = enabled
        
        if enabled and not was_online:
            self._log_audit("online_mode_enabled", {"reason": "user_enabled"})
        elif not enabled and was_online:
            self._log_audit("online_mode_disabled", {"reason": "user_disabled"})
    
    def classify_syllabus(self, filename: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to classify syllabus if available.
        Falls back to None (caller uses heuristic).
        
        Args:
            filename: original filename
            content: full text content
        
        Returns:
            classification dict if successful, None if unavailable
        """
        
        if not self.available:
            return None
        
        if not self.is_online_mode and self.available:
            # Ollama is local, OK to use
            pass
        
        # Structured prompt for JSON extraction
        prompt = f"""
Analyze this syllabus and extract structured data.
Return ONLY valid JSON, no markdown, no explanation.

Syllabus filename: {filename}
Content:
{content[:3000]}  # Limit to avoid token overrun

Return this exact JSON structure:
{{
  "class_code": "string or null",
  "class_name": "string or null", 
  "confidence": 0.0-1.0,
  "deadlines": [
    {{"description": "string", "date": "string", "confidence": 0.0-1.0}}
  ],
  "meeting_times": ["string"],
  "instructor": "string or null",
  "grading_breakdown": {{"category": "percentage"}} or null
}}
"""
        
        try:
            resp = requests.post(
                f"{self.OLLAMA_HOST}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3  # deterministic
                },
                timeout=self.TIMEOUT
            )
            
            if resp.status_code != 200:
                self._log_audit("llm_classify_failed", {"status": resp.status_code})
                return None
            
            # Extract JSON from response
            response_text = resp.json().get("response", "")
            
            # Try to parse JSON (may be wrapped in text)
            try:
                # Find JSON in response
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response_text[start:end]
                    result = json.loads(json_str)
                    
                    # Ensure required fields
                    result["method"] = "llm"
                    result["filename"] = filename
                    
                    self._log_audit("llm_classify_success", {
                        "filename": filename,
                        "confidence": result.get("confidence", 0)
                    })
                    
                    return result
            except json.JSONDecodeError:
                self._log_audit("llm_classify_json_error", {"filename": filename})
                return None
        
        except requests.Timeout:
            self._log_audit("llm_timeout", {"filename": filename})
            return None
        except Exception as e:
            self._log_audit("llm_error", {"filename": filename, "error": str(e)})
            return None
    
    def extract_deadlines(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """
        Use LLM to extract deadline items from text.
        Falls back to None if unavailable.
        """
        
        if not self.available:
            return None
        
        prompt = f"""
Extract all assignment/exam deadlines from this text.
Return ONLY valid JSON array, no markdown.

Text:
{content[:2000]}

Return this exact JSON array:
[
  {{"description": "string", "date": "string", "confidence": 0.0-1.0}}
]

If no deadlines found, return [].
"""
        
        try:
            resp = requests.post(
                f"{self.OLLAMA_HOST}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2
                },
                timeout=self.TIMEOUT
            )
            
            if resp.status_code == 200:
                response_text = resp.json().get("response", "")
                try:
                    start = response_text.find("[")
                    end = response_text.rfind("]") + 1
                    if start >= 0 and end > start:
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            self._log_audit("llm_extract_deadlines_error", {"error": str(e)})
        
        return None
    
    def _log_audit(self, action: str, data: Dict[str, Any]) -> None:
        """Log LLM usage to audit trail."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "actor": "llm_adapter",
            "action": action,
            "data": data,
            "online_mode": self.is_online_mode
        }
        self.audit_log.append(entry)
    
    def get_status(self) -> Dict[str, Any]:
        """Status dict for Diagnostics panel."""
        return {
            "llm_available": self.available,
            "online_mode_enabled": self.is_online_mode,
            "model": self.MODEL if self.available else None,
            "host": self.OLLAMA_HOST if self.available else None,
            "api_calls_logged": len([e for e in self.audit_log if e["actor"] == "llm_adapter"])
        }
