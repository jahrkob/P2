import websocket  # pip install websocket-client
import json

TOKEN  = 'vnoWpgAAABFpb3RuZXQudGVyYWNvbS5kaySaIG0eQDgMgCTxhShW93s='
SERVER = f'wss://iotnet.teracom.dk/app?token={TOKEN}'

def on_open(ws):
    print("Connected to Cibicom/Teracom LoRaWAN server")

def on_message(ws, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print(f"Non-JSON message received: {message}")
        return

    cmd = data.get('cmd')

    if cmd == 'rx':
        eui     = data.get('EUI', '?')
        fcnt    = data.get('fcnt', '?')
        port    = data.get('port', '?')
        payload = data.get('data', data.get('encdata', '(no plaintext)'))

        print(f"[{eui}] fcnt={fcnt} port={port} payload={payload}")

        # Decode hex payload to string if possible
        try:
            decoded = bytes.fromhex(payload).decode('utf-8')
            print(f"  └ decoded: {decoded}")
        except Exception:
            pass  # payload may not be valid UTF-8

    elif cmd == 'gw':
        # Gateway status update — ignore or log as needed
        pass

    else:
        print(f"Other message (cmd={cmd}): {data}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: {close_status_code} {close_msg}")

ws = websocket.WebSocketApp(
    SERVER,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

ws.run_forever()