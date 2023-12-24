try:
    from .database_test import *
except Exception:
    print('Tests for _database.py failed')
try:
    from .portal_test import *
except Exception:
    print('Tests for _portal.py failed')