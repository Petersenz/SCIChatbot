import logging
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from backend.error_responses import install_error_handling
class Payload(BaseModel):
    count:int

def fixture():
    app=FastAPI();install_error_handling(app)
    @app.get("/broken")
    def broken():raise RuntimeError("SECRET_SQL_PASSWORD")
    @app.get("/limited")
    def limited():raise HTTPException(429,"กรุณารอสักครู่",headers={"Retry-After":"17"})
    @app.post("/validate")
    def validate(body:Payload):return {"ok":True}
    @app.get("/healthy")
    def healthy():return {"ok":True}
    return TestClient(app)
def test_error_redacts_body_and_correlates_logs(caplog):
    with caplog.at_level(logging.WARNING):r=fixture().get("/broken?token=PRIVATE_QUERY")
    assert r.status_code==500
    assert r.json()["code"]=="internal_error"
    assert r.json()["request_id"]==r.headers["x-request-id"]
    assert r.json()["request_id"] in caplog.text
    assert "SECRET_SQL_PASSWORD" not in r.text+caplog.text
    assert "PRIVATE_QUERY" not in caplog.text
    assert r.headers["cache-control"]=="no-store"
def test_rate_limit_preserves_header():
    r=fixture().get("/limited");assert r.status_code==429
    assert r.headers["retry-after"]=="17" and r.json()["code"]=="rate_limited"
def test_validation_does_not_echo_input():
    r=fixture().post("/validate",json={"count":"SECRET_INPUT"})
    assert r.status_code==422 and "SECRET_INPUT" not in r.text
    assert r.json()["code"]=="validation_error"
def test_success_and_not_found():
    c=fixture();r=c.get("/healthy");assert r.json()=={"ok":True}
    assert len(r.headers["x-request-id"])==12
    assert c.get("/unknown").json()["code"]=="not_found"
