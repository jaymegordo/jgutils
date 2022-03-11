import os
import sys

# dont think these are used
AZURE_LOCAL = not os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') is None
AZURE_WEB = not os.getenv('WEBSITE_SITE_NAME') is None
AZURE = AZURE_LOCAL or AZURE_WEB
IS_QT_APP = not os.getenv('IS_QT_APP') is None
SYS_FROZEN = getattr(sys, 'frozen', False)
