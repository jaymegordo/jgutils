import os
import sys
from pathlib import Path

# duplicates of jambot/config.py
AZURE_LOCAL = 'AZURE_FUNCTIONS_ENVIRONMENT' in os.environ
AZURE_WEB = 'WEBSITE_SITE_NAME' in os.environ
AZURE = AZURE_LOCAL or AZURE_WEB
IS_QT_APP = 'IS_QT_APP' in os.environ
SYS_FROZEN = getattr(sys, 'frozen', False)
IS_LINUX = sys.platform.startswith('linux')
IS_LAMBDA = 'AWS_EXECUTION_ENV' in os.environ
IS_GITHUB = 'GITHUB_ENV' in os.environ
IS_REMOTE = IS_LAMBDA or IS_GITHUB or IS_LINUX

p_proj = Path(__file__).parent  # jambot (python module)
p_root = p_proj.parent  # root folter
