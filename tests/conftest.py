import pytest


@pytest.fixture(autouse=True)
def offline_demo(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("APPROVED_NAMESPACE", "mlops-demo")
