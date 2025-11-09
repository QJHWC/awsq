import os
import json
import uuid
import time
import sqlite3
import importlib.util
import random
from pathlib import Path
from typing import Dict, Optional, List, Any, Generator, Tuple

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# ------------------------------------------------------------------------------
# Bootstrap
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.sqlite3"

load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="v2 OpenAI-compatible Server (Amazon Q Backend)")

# CORS for simple testing in browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Dynamic import of replicate.py to avoid package __init__ needs
# ------------------------------------------------------------------------------

def _load_replicate_module():
    mod_path = BASE_DIR / "replicate.py"
    spec = importlib.util.spec_from_file_location("v2_replicate", str(mod_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module

_replicate = _load_replicate_module()
send_chat_request = _replicate.send_chat_request

# ------------------------------------------------------------------------------
# SQLite helpers
# ------------------------------------------------------------------------------

def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                label TEXT,
                clientId TEXT,
                clientSecret TEXT,
                refreshToken TEXT,
                accessToken TEXT,
                other TEXT,
                last_refresh_time TEXT,
                last_refresh_status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        # add enabled column if missing
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()]
            if "enabled" not in cols:
                conn.execute("ALTER TABLE accounts ADD COLUMN enabled INTEGER DEFAULT 1")
        except Exception:
            # best-effort; ignore if cannot alter (should not happen for SQLite)
            pass
        conn.commit()

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_dict(r: sqlite3.Row) -> Dict[str, Any]:
    d = dict(r)
    if d.get("other"):
        try:
            d["other"] = json.loads(d["other"])
        except Exception:
            pass
    # normalize enabled to bool
    if "enabled" in d and d["enabled"] is not None:
        try:
            d["enabled"] = bool(int(d["enabled"]))
        except Exception:
            d["enabled"] = bool(d["enabled"])
    return d

_ensure_db()

# ------------------------------------------------------------------------------
# Env and API Key authorization (keys are independent of AWS accounts)
# ------------------------------------------------------------------------------
def _parse_allowed_keys_env() -> List[str]:
    """
    OPENAI_KEYS is a comma-separated whitelist of API keys for authorization only.
    Example: OPENAI_KEYS="key1,key2,key3"
    - When the list is non-empty, incoming Authorization: Bearer {key} must be one of them.
    - When empty or unset, authorization is effectively disabled (dev mode).
    """
    s = os.getenv("OPENAI_KEYS", "") or ""
    keys: List[str] = []
    for k in [x.strip() for x in s.split(",") if x.strip()]:
        keys.append(k)
    return keys

ALLOWED_API_KEYS: List[str] = _parse_allowed_keys_env()

def _extract_bearer(token_header: Optional[str]) -> Optional[str]:
    if not token_header:
        return None
    if token_header.startswith("Bearer "):
        return token_header.split(" ", 1)[1].strip()
    return token_header.strip()

def _list_enabled_accounts(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute("SELECT * FROM accounts WHERE enabled=1 ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]

def resolve_account_for_key(bearer_key: Optional[str]) -> Dict[str, Any]:
    """
    Authorize request by OPENAI_KEYS (if configured), then select an AWS account.
    Selection strategy: random among all enabled accounts. Authorization key does NOT map to any account.
    """
    # Authorization
    if ALLOWED_API_KEYS:
        if not bearer_key or bearer_key not in ALLOWED_API_KEYS:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Selection: random among enabled accounts
    with _conn() as conn:
        candidates = _list_enabled_accounts(conn)
        if not candidates:
            raise HTTPException(status_code=401, detail="No enabled account available")
        return random.choice(candidates)

# ------------------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------------------

class AccountCreate(BaseModel):
    label: Optional[str] = None
    clientId: str
    clientSecret: str
    refreshToken: Optional[str] = None
    accessToken: Optional[str] = None
    other: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = True

class AccountUpdate(BaseModel):
    label: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None
    refreshToken: Optional[str] = None
    accessToken: Optional[str] = None
    other: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

class ChatMessage(BaseModel):
    role: str
    content: Any

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    stream: Optional[bool] = False

# ------------------------------------------------------------------------------
# Token refresh (OIDC)
# ------------------------------------------------------------------------------

OIDC_BASE = "https://oidc.us-east-1.amazonaws.com"
TOKEN_URL = f"{OIDC_BASE}/token"

def _oidc_headers() -> Dict[str, str]:
    return {
        "content-type": "application/json",
        "user-agent": "aws-sdk-rust/1.3.9 os/windows lang/rust/1.87.0",
        "x-amz-user-agent": "aws-sdk-rust/1.3.9 ua/2.1 api/ssooidc/1.88.0 os/windows lang/rust/1.87.0 m/E app/AmazonQ-For-CLI",
        "amz-sdk-request": "attempt=1; max=3",
        "amz-sdk-invocation-id": str(uuid.uuid4()),
    }

def refresh_access_token_in_db(account_id: str) -> Dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        acc = _row_to_dict(row)

        if not acc.get("clientId") or not acc.get("clientSecret") or not acc.get("refreshToken"):
            raise HTTPException(status_code=400, detail="Account missing clientId/clientSecret/refreshToken for refresh")

        payload = {
            "grantType": "refresh_token",
            "clientId": acc["clientId"],
            "clientSecret": acc["clientSecret"],
            "refreshToken": acc["refreshToken"],
        }

        try:
            r = requests.post(TOKEN_URL, headers=_oidc_headers(), json=payload, timeout=(15, 60))
            r.raise_for_status()
            data = r.json()
            new_access = data.get("accessToken")
            new_refresh = data.get("refreshToken", acc.get("refreshToken"))
            now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            status = "success"
        except requests.RequestException as e:
            now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            status = "failed"
            conn.execute(
                """
                UPDATE accounts
                SET last_refresh_time=?, last_refresh_status=?, updated_at=?
                WHERE id=?
                """,
                (now, status, now, account_id),
            )
            conn.commit()
            raise HTTPException(status_code=502, detail=f"Token refresh failed: {str(e)}")

        conn.execute(
            """
            UPDATE accounts
            SET accessToken=?, refreshToken=?, last_refresh_time=?, last_refresh_status=?, updated_at=?
            WHERE id=?
            """,
            (new_access, new_refresh, now, status, now, account_id),
        )
        conn.commit()

        row2 = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        return _row_to_dict(row2)

def get_account(account_id: str) -> Dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return _row_to_dict(row)

# ------------------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------------------

def require_account(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    bearer = _extract_bearer(authorization)
    return resolve_account_for_key(bearer)

# ------------------------------------------------------------------------------
# OpenAI-compatible Chat endpoint
# ------------------------------------------------------------------------------

def _openai_non_streaming_response(text: str, model: Optional[str]) -> Dict[str, Any]:
    created = int(time.time())
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": created,
        "model": model or "unknown",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
    }

def _sse_format(obj: Dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest, account: Dict[str, Any] = Depends(require_account)):
    """
    OpenAI-compatible chat endpoint.
    - stream default False
    - messages will be converted into "{role}:\n{content}" and injected into template
    - account is chosen randomly among enabled accounts (API key is for authorization only)
    """
    model = req.model
    do_stream = bool(req.stream)

    def _send_upstream(stream: bool) -> Tuple[Optional[str], Optional[Generator[str, None, None]]]:
        access = account.get("accessToken")
        if not access:
            refreshed = refresh_access_token_in_db(account["id"])
            access = refreshed.get("accessToken")
            if not access:
                raise HTTPException(status_code=502, detail="Access token unavailable after refresh")
        try:
            return send_chat_request(access, [m.model_dump() for m in req.messages], model=model, stream=stream)
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403):
                refreshed = refresh_access_token_in_db(account["id"])
                access2 = refreshed.get("accessToken")
                if not access2:
                    raise HTTPException(status_code=502, detail="Token refresh failed")
                return send_chat_request(access2, [m.model_dump() for m in req.messages], model=model, stream=stream)
            raise

    if not do_stream:
        text, _ = _send_upstream(stream=False)
        return JSONResponse(content=_openai_non_streaming_response(text or "", model))
    else:
        created = int(time.time())
        stream_id = f"chatcmpl-{uuid.uuid4()}"
        model_used = model or "unknown"

        def event_gen() -> Generator[str, None, None]:
            yield _sse_format({
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_used,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            })
            _, it = _send_upstream(stream=True)
            assert it is not None
            for piece in it:
                if not piece:
                    continue
                yield _sse_format({
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_used,
                    "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
                })
            yield _sse_format({
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_used,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            })
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_gen(), media_type="text/event-stream")

# ------------------------------------------------------------------------------
# Device Authorization (URL Login, 5-minute timeout)
# ------------------------------------------------------------------------------

# Dynamic import of auth_flow.py (device-code login helpers)
def _load_auth_flow_module():
    mod_path = BASE_DIR / "auth_flow.py"
    spec = importlib.util.spec_from_file_location("v2_auth_flow", str(mod_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module

_auth_flow = _load_auth_flow_module()
register_client_min = _auth_flow.register_client_min
device_authorize = _auth_flow.device_authorize
poll_token_device_code = _auth_flow.poll_token_device_code

# In-memory auth sessions (ephemeral)
AUTH_SESSIONS: Dict[str, Dict[str, Any]] = {}

class AuthStartBody(BaseModel):
    label: Optional[str] = None
    enabled: Optional[bool] = True

def _create_account_from_tokens(
    client_id: str,
    client_secret: str,
    access_token: str,
    refresh_token: Optional[str],
    label: Optional[str],
    enabled: bool,
) -> Dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    acc_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO accounts (id, label, clientId, clientSecret, refreshToken, accessToken, other, last_refresh_time, last_refresh_status, created_at, updated_at, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acc_id,
                label,
                client_id,
                client_secret,
                refresh_token,
                access_token,
                None,
                now,
                "success",
                now,
                now,
                1 if enabled else 0,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (acc_id,)).fetchone()
        return _row_to_dict(row)

@app.post("/v2/auth/start")
def auth_start(body: AuthStartBody):
    """
    Start device authorization and return verification URL for user login.
    Session lifetime capped at 5 minutes on claim.
    """
    try:
        cid, csec = register_client_min()
        dev = device_authorize(cid, csec)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"OIDC error: {str(e)}")

    auth_id = str(uuid.uuid4())
    sess = {
        "clientId": cid,
        "clientSecret": csec,
        "deviceCode": dev.get("deviceCode"),
        "interval": int(dev.get("interval", 1)),
        "expiresIn": int(dev.get("expiresIn", 600)),
        "verificationUriComplete": dev.get("verificationUriComplete"),
        "userCode": dev.get("userCode"),
        "startTime": int(time.time()),
        "label": body.label,
        "enabled": True if body.enabled is None else bool(body.enabled),
        "status": "pending",
        "error": None,
        "accountId": None,
    }
    AUTH_SESSIONS[auth_id] = sess
    return {
        "authId": auth_id,
        "verificationUriComplete": sess["verificationUriComplete"],
        "userCode": sess["userCode"],
        "expiresIn": sess["expiresIn"],
        "interval": sess["interval"],
    }

@app.get("/v2/auth/status/{auth_id}")
def auth_status(auth_id: str):
    sess = AUTH_SESSIONS.get(auth_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Auth session not found")
    now_ts = int(time.time())
    deadline = sess["startTime"] + min(int(sess.get("expiresIn", 600)), 300)
    remaining = max(0, deadline - now_ts)
    return {
        "status": sess.get("status"),
        "remaining": remaining,
        "error": sess.get("error"),
        "accountId": sess.get("accountId"),
    }

@app.post("/v2/auth/claim/{auth_id}")
def auth_claim(auth_id: str):
    """
    Block up to 5 minutes to exchange the device code for tokens after user completed login.
    On success, creates an enabled account and returns it.
    """
    sess = AUTH_SESSIONS.get(auth_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Auth session not found")
    if sess.get("status") in ("completed", "timeout", "error"):
        return {
            "status": sess["status"],
            "accountId": sess.get("accountId"),
            "error": sess.get("error"),
        }
    try:
        toks = poll_token_device_code(
            sess["clientId"],
            sess["clientSecret"],
            sess["deviceCode"],
            sess["interval"],
            sess["expiresIn"],
            max_timeout_sec=300,  # 5 minutes
        )
        access_token = toks.get("accessToken")
        refresh_token = toks.get("refreshToken")
        if not access_token:
            raise HTTPException(status_code=502, detail="No accessToken returned from OIDC")

        acc = _create_account_from_tokens(
            sess["clientId"],
            sess["clientSecret"],
            access_token,
            refresh_token,
            sess.get("label"),
            sess.get("enabled", True),
        )
        sess["status"] = "completed"
        sess["accountId"] = acc["id"]
        return {
            "status": "completed",
            "account": acc,
        }
    except TimeoutError:
        sess["status"] = "timeout"
        raise HTTPException(status_code=408, detail="Authorization timeout (5 minutes)")
    except requests.RequestException as e:
        sess["status"] = "error"
        sess["error"] = str(e)
        raise HTTPException(status_code=502, detail=f"OIDC error: {str(e)}")

# ------------------------------------------------------------------------------
# Accounts Management API
# ------------------------------------------------------------------------------

@app.post("/v2/accounts")
def create_account(body: AccountCreate):
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    acc_id = str(uuid.uuid4())
    other_str = json.dumps(body.other, ensure_ascii=False) if body.other is not None else None
    enabled_val = 1 if (body.enabled is None or body.enabled) else 0
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO accounts (id, label, clientId, clientSecret, refreshToken, accessToken, other, last_refresh_time, last_refresh_status, created_at, updated_at, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acc_id,
                body.label,
                body.clientId,
                body.clientSecret,
                body.refreshToken,
                body.accessToken,
                other_str,
                None,
                "never",
                now,
                now,
                enabled_val,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (acc_id,)).fetchone()
        return _row_to_dict(row)

@app.get("/v2/accounts")
def list_accounts():
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]

@app.get("/v2/accounts/{account_id}")
def get_account_detail(account_id: str):
    return get_account(account_id)

@app.delete("/v2/accounts/{account_id}")
def delete_account(account_id: str):
    with _conn() as conn:
        cur = conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"deleted": account_id}

@app.patch("/v2/accounts/{account_id}")
def update_account(account_id: str, body: AccountUpdate):
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    fields = []
    values: List[Any] = []

    if body.label is not None:
        fields.append("label=?"); values.append(body.label)
    if body.clientId is not None:
        fields.append("clientId=?"); values.append(body.clientId)
    if body.clientSecret is not None:
        fields.append("clientSecret=?"); values.append(body.clientSecret)
    if body.refreshToken is not None:
        fields.append("refreshToken=?"); values.append(body.refreshToken)
    if body.accessToken is not None:
        fields.append("accessToken=?"); values.append(body.accessToken)
    if body.other is not None:
        fields.append("other=?"); values.append(json.dumps(body.other, ensure_ascii=False))
    if body.enabled is not None:
        fields.append("enabled=?"); values.append(1 if body.enabled else 0)

    if not fields:
        return get_account(account_id)

    fields.append("updated_at=?"); values.append(now)
    values.append(account_id)

    with _conn() as conn:
        cur = conn.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        return _row_to_dict(row)

@app.post("/v2/accounts/{account_id}/refresh")
def manual_refresh(account_id: str):
    return refresh_access_token_in_db(account_id)

# ------------------------------------------------------------------------------
# Simple Frontend (minimal dev test page; full UI in v2/frontend/index.html)
# ------------------------------------------------------------------------------

# Frontend inline HTML removed; serving ./frontend/index.html instead (see route below)

@app.get("/", response_class=FileResponse)
def index():
    path = BASE_DIR / "frontend" / "index.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="frontend/index.html not found")
    return FileResponse(str(path))

# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------

@app.get("/healthz")
def health():
    return {"status": "ok"}

# ------------------------------------------------------------------------------
# Auto Register (全自动注册)
# ------------------------------------------------------------------------------

@app.post("/v2/auto-register/start")
def auto_register_start():
    """
    启动全自动注册流程
    调用 Python 自动注册脚本
    """
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        # 获取脚本路径
        script_path = BASE_DIR / "amazonq_auto_register.py"
        
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="自动注册脚本未找到")
        
        # 启动 Python 脚本（后台运行）
        # 注意：这会阻塞 API 请求，实际应该使用异步任务队列
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
            input="\n"  # 自动按回车
        )
        
        # 简单检查是否成功（通过输出判断）
        output = result.stdout + result.stderr
        
        if "注册成功" in output or "Registration successful" in output:
            # 尝试从输出中提取邮箱和账号ID
            import re
            email_match = re.search(r'邮箱[:：]\s*([^\s]+@[^\s]+)', output)
            id_match = re.search(r'账号ID[:：]\s*([a-f0-9-]+)', output)
            
            return {
                "success": True,
                "email": email_match.group(1) if email_match else "unknown",
                "account_id": id_match.group(1) if id_match else "unknown",
                "message": "自动注册成功"
            }
        else:
            return {
                "success": False,
                "error": "注册过程未完成或失败",
                "output": output[-500:]  # 最后500字符
            }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="自动注册超时（10分钟）")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动自动注册失败: {str(e)}")