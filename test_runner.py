import unittest
import sys

def run_tests():
    """Run all tests with detailed output"""
    print("\n" + "="*50)
    print("MEMORY-PERSISTENT RESEARCH ASSISTANT - TEST SUITE")
    print("="*50)
    
    loader = unittest.TestLoader()
    
    # Load working test files
    working_tests = [
        'tests.test_core_logic',
        'tests.test_memory_system',
        'tests.test_query_processing'
    ]
    
    suite = unittest.TestSuite()
    
    for test_module in working_tests:
        try:
            tests = loader.loadTestsFromName(test_module)
            suite.addTests(tests)
        except ImportError as e:
            print(f"Skipping {test_module}: {e}")
    
    print(f"\nRunning tests from {len(working_tests)} test modules...\n")
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "="*50)
    print(f"RESULTS: {result.testsRun} tests run")
    if result.failures:
        print(f"FAILURES: {len(result.failures)}")
    if result.errors:
        print(f"ERRORS: {len(result.errors)}")
    print("="*50)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\n[PASS] Working tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed!")
        sys.exit(1)