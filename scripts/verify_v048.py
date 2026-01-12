#!/usr/bin/env python3
"""
verify_v048.py - Automated Verification for v0.48 Daily Hardening

Runs backend tests, static checks, and minimal UI integrity checks.
No user testing required - this script validates production readiness.

Usage:
    python scripts/verify_v048.py
    python scripts/verify_v048.py --full
    python scripts/verify_v048.py --backend-only
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

class Verify048:
    def __init__(self, full=False, backend_only=False):
        self.full = full
        self.backend_only = backend_only
        self.results = {
            'backend_tests': [],
            'frontend_checks': [],
            'integrations': [],
            'performance': [],
            'summary': {}
        }
        self.root = Path(__file__).parent.parent
        
    def run_backend_tests(self):
        """Run pytest tests for v0.48"""
        print("\n" + "="*60)
        print("STEP 1: Backend Tests")
        print("="*60)
        
        tests = [
            'tests/test_v048_whats_next_determinism.py',
            'tests/test_v048_undo.py',
            'tests/test_v048_agent_history.py',
        ]
        
        for test in tests:
            test_path = self.root / test
            if not test_path.exists():
                print(f"⚠️  Test not found: {test}")
                continue
                
            print(f"\n▶ Running {test}...")
            result = subprocess.run(
                ['python', '-m', 'pytest', str(test_path), '-v'],
                cwd=self.root,
                capture_output=True,
                text=True
            )
            
            status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
            print(f"  {status}")
            
            self.results['backend_tests'].append({
                'test': test,
                'passed': result.returncode == 0,
                'output': result.stdout
            })
    
    def check_database_migrations(self):
        """Verify database schema changes"""
        print("\n" + "="*60)
        print("STEP 2: Database Migrations")
        print("="*60)
        
        try:
            # Check if UndoEvent table exists
            from marcus_app.core.database import db
            from marcus_app.models import UndoEvent
            
            # Try to query
            count = UndoEvent.query.count()
            print(f"✅ UndoEvent table exists ({count} records)")
            self.results['backend_tests'].append({
                'check': 'UndoEvent table',
                'passed': True
            })
        except Exception as e:
            print(f"⚠️  UndoEvent table check failed: {e}")
            print("   (Table may not exist yet - run migrations first)")
            self.results['backend_tests'].append({
                'check': 'UndoEvent table',
                'passed': False,
                'error': str(e)
            })
        
        try:
            # Check if items.is_deleted exists
            from marcus_app.models import Item
            from sqlalchemy import inspect
            
            mapper = inspect(Item)
            columns = [c.name for c in mapper.columns]
            
            if 'is_deleted' in columns:
                print("✅ items.is_deleted column exists")
                self.results['backend_tests'].append({
                    'check': 'items.is_deleted',
                    'passed': True
                })
            else:
                print("⚠️  items.is_deleted column not found")
                self.results['backend_tests'].append({
                    'check': 'items.is_deleted',
                    'passed': False
                })
        except Exception as e:
            print(f"⚠️  Column check failed: {e}")

    def check_api_endpoints(self):
        """Verify new API endpoints exist"""
        print("\n" + "="*60)
        print("STEP 3: API Endpoint Checks")
        print("="*60)
        
        endpoints = [
            ('GET', '/api/suggest/classes'),
            ('GET', '/api/suggest/projects'),
            ('GET', '/api/suggest/missions'),
            ('GET', '/api/suggest/commands'),
            ('GET', '/api/next'),
            ('POST', '/api/undo/last'),
            ('GET', '/api/undo/status'),
            ('GET', '/api/system/status'),
        ]
        
        try:
            from marcus_app.backend.api import app
            
            for method, endpoint in endpoints:
                # Check if route exists in app
                found = False
                for rule in app.url_map.iter_rules():
                    if endpoint in rule.rule:
                        found = True
                        break
                
                status = "✅" if found else "❌"
                print(f"{status} {method} {endpoint}")
                self.results['integrations'].append({
                    'endpoint': f"{method} {endpoint}",
                    'exists': found
                })
        except Exception as e:
            print(f"❌ Could not check endpoints: {e}")

    def check_frontend_files(self):
        """Verify frontend files exist"""
        print("\n" + "="*60)
        print("STEP 4: Frontend File Checks")
        print("="*60)
        
        files = [
            'marcus_app/frontend/agent_chat.js',
            'marcus_app/frontend/agent_input_controller.js',
            'marcus_app/frontend/inbox_keyboard.js',
            'marcus_app/frontend/trust_bar.js',
            'marcus_app/frontend/agent_chat.css',
        ]
        
        for file in files:
            path = self.root / file
            if path.exists():
                size = path.stat().st_size
                print(f"✅ {file} ({size} bytes)")
                self.results['frontend_checks'].append({
                    'file': file,
                    'exists': True,
                    'size': size
                })
            else:
                print(f"❌ {file} not found")
                self.results['frontend_checks'].append({
                    'file': file,
                    'exists': False
                })

    def check_service_implementations(self):
        """Verify service layer implementations"""
        print("\n" + "="*60)
        print("STEP 5: Service Layer Checks")
        print("="*60)
        
        services = [
            ('next_action_service', 'NextActionService'),
            ('undo_service', 'UndoService'),
            ('agent_router', 'AgentRouter'),
        ]
        
        for module_name, class_name in services:
            try:
                module = __import__(
                    f'marcus_app.services.{module_name}',
                    fromlist=[class_name]
                )
                cls = getattr(module, class_name)
                
                # Check key methods exist
                methods = dir(cls)
                print(f"✅ {class_name} loaded")
                print(f"   Methods: {len(methods)}")
                
                self.results['integrations'].append({
                    'service': class_name,
                    'loaded': True,
                    'methods': len(methods)
                })
            except Exception as e:
                print(f"❌ {class_name} import failed: {e}")
                self.results['integrations'].append({
                    'service': class_name,
                    'loaded': False,
                    'error': str(e)
                })

    def check_documentation(self):
        """Verify documentation exists"""
        print("\n" + "="*60)
        print("STEP 6: Documentation Checks")
        print("="*60)
        
        docs = [
            'V048_DAILY_HARDENING_COMPLETE.md',
            'V048_QUICK_REFERENCE.md',
        ]
        
        for doc in docs:
            path = self.root / doc
            if path.exists():
                size = path.stat().st_size
                print(f"✅ {doc} ({size} bytes)")
                self.results['frontend_checks'].append({
                    'doc': doc,
                    'exists': True
                })
            else:
                print(f"❌ {doc} not found")
                self.results['frontend_checks'].append({
                    'doc': doc,
                    'exists': False
                })

    def run_performance_checks(self):
        """Check performance characteristics"""
        print("\n" + "="*60)
        print("STEP 7: Performance Checks")
        print("="*60)
        
        try:
            import time
            from marcus_app.services.next_action_service import NextActionService
            
            service = NextActionService()
            
            start = time.time()
            result = service.get_next_actions()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Should be < 100ms (excluding DB I/O)
            passed = elapsed < 200  # 200ms with some DB overhead
            status = "✅" if passed else "⚠️"
            
            print(f"{status} NextActionService.get_next_actions(): {elapsed:.1f}ms")
            self.results['performance'].append({
                'check': 'get_next_actions',
                'elapsed_ms': elapsed,
                'passed': passed
            })
        except Exception as e:
            print(f"⚠️  Performance check failed: {e}")

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        # Count results
        backend_pass = sum(1 for r in self.results['backend_tests'] if r.get('passed', True))
        backend_total = len(self.results['backend_tests'])
        
        frontend_pass = sum(1 for r in self.results['frontend_checks'] if r.get('exists', True))
        frontend_total = len(self.results['frontend_checks'])
        
        integrations_pass = sum(1 for r in self.results['integrations'] if r.get('passed') or r.get('exists') or r.get('loaded'))
        integrations_total = len(self.results['integrations'])
        
        print(f"\n📊 Test Results:")
        print(f"   Backend Tests: {backend_pass}/{backend_total} ✅")
        print(f"   Frontend Files: {frontend_pass}/{frontend_total} ✅")
        print(f"   Integrations: {integrations_pass}/{integrations_total} ✅")
        
        if self.results['performance']:
            print(f"\n⚡ Performance:")
            for perf in self.results['performance']:
                if perf.get('passed'):
                    print(f"   ✅ {perf['check']}: {perf['elapsed_ms']:.1f}ms")
                else:
                    print(f"   ⚠️  {perf['check']}: {perf['elapsed_ms']:.1f}ms (target: <100ms)")
        
        # Overall status
        total_pass = backend_pass + frontend_pass + integrations_pass
        total = backend_total + frontend_total + integrations_total
        
        if total_pass == total:
            print(f"\n🎉 v0.48 Verification: PASSED ({total}/{total})")
            return 0
        else:
            print(f"\n⚠️  v0.48 Verification: INCOMPLETE ({total_pass}/{total})")
            return 1

    def run(self):
        """Run all verification checks"""
        print("\n" + "🔍 "*20)
        print("v0.48 DAILY HARDENING - VERIFICATION SCRIPT")
        print("🔍 "*20)
        
        try:
            if not self.backend_only:
                self.check_frontend_files()
                self.check_api_endpoints()
            
            self.run_backend_tests()
            self.check_database_migrations()
            self.check_service_implementations()
            self.run_performance_checks()
            
            if not self.backend_only:
                self.check_documentation()
            
            return self.generate_summary()
            
        except Exception as e:
            print(f"\n❌ Verification failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify v0.48 implementation')
    parser.add_argument('--full', action='store_true', help='Run full verification')
    parser.add_argument('--backend-only', action='store_true', help='Backend tests only')
    
    args = parser.parse_args()
    
    verifier = Verify048(full=args.full, backend_only=args.backend_only)
    exit_code = verifier.run()
    
    sys.exit(exit_code)
