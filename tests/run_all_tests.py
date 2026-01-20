# run_all_tests.py
import os
import sys
import pytest


def setup_environment():
    """Setup Python path for testing."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, 'src')
    sys.path.insert(0, project_root)
    sys.path.insert(0, src_path)

    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")


def main():
    """Run all tests."""
    setup_environment()

    # Run tests
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    print(f"Running tests from: {test_dir}")

    result = pytest.main([
        test_dir,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-W', 'ignore::DeprecationWarning',  # Ignore warnings
    ])

    return result


if __name__ == "__main__":
    sys.exit(main())