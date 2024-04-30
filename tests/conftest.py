import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def change_test_dir(request):
    """Change current working directory to project root."""
    os.chdir(request.config.rootdir)