"""Test environment defaults, loaded before any application module import.

`INVOICE_ENVIRONMENT=development` opts the test app into the known development
token; the production fail-closed guard is exercised explicitly in
`test_service.py`. Direct assignment keeps the suite independent of the
developer's shell environment.
"""

import os

os.environ["INVOICE_ENVIRONMENT"] = "development"
os.environ["INVOICE_DATABASE_URL"] = "sqlite:///:memory:"
