import sys
import types

stub = types.ModuleType("weasyprint")
class _HTML:
    def __init__(self, *a, **k): pass
    def write_pdf(self, *a, **k): raise RuntimeError("weasyprint stubbed for prototype run")
stub.HTML = _HTML
sys.modules["weasyprint"] = stub

import uvicorn
uvicorn.run("app.main:create_app", factory=True, host="127.0.0.1", port=8001)
