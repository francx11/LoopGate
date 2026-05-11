import json

import pytest
from starlette.websockets import WebSocketDisconnect


def _recv_json(ws):
    return json.loads(ws.receive_text())


def test_ws_open_mode_no_auth_required(client, without_token):
    with client.websocket_connect("/ws") as ws:
        msg = _recv_json(ws)
        assert msg["type"] == "init"
        assert msg["tasks"] == []


def test_ws_first_message_auth_succeeds(client, with_token):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "auth", "token": with_token}))
        msg = _recv_json(ws)
        assert msg["type"] == "init"


def test_ws_first_message_auth_invalid_token(client, with_token):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "auth", "token": "wrong"}))
        err = _recv_json(ws)
        assert err["type"] == "auth_error"
        assert err["reason"] == "invalid_token"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
        assert exc.value.code == 4001


def test_ws_query_param_auth_backward_compat(client, with_token):
    with client.websocket_connect(f"/ws?token={with_token}") as ws:
        msg = _recv_json(ws)
        assert msg["type"] == "init"


def test_ws_first_message_not_auth_rejects(client, with_token):
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        err = _recv_json(ws)
        assert err["type"] == "auth_error"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
        assert exc.value.code == 4001


def test_ws_handshake_never_returns_403(client, with_token):
    # The WS handshake must succeed even when auth will later fail —
    # rejecting pre-accept used to surface as HTTP 403 at proxies.
    with client.websocket_connect("/ws") as ws:
        # We are connected; that alone proves the handshake was accepted.
        ws.send_text(json.dumps({"type": "auth", "token": "nope"}))
        _recv_json(ws)  # auth_error
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()
