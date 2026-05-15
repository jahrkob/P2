import websocket
import json
from datetime import datetime


class TeracomLoRaWANClient:
    def __init__(self, token: str, host: str = "iotnet.teracom.dk"):
        self.token = token
        self.server = f"wss://{host}/app?token={token}"
        self.ws = None
        self.records: dict = {}  # Keyed by EUI, value is list of entries

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever()

    def get_records(self) -> dict:
        """Return all received records."""
        return self.records

    def _on_open(self, ws):
        print("Connected to Cibicom/Teracom LoRaWAN server")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print(f"Non-JSON message received: {message}")
            return

        cmd = data.get("cmd")
        if cmd == "rx":
            self._handle_rx(data)
        elif cmd == "gw":
            pass  # Gateway status update — ignore or log as needed
        else:
            print(f"Other message (cmd={cmd}): {data}")

    def _handle_rx(self, data: dict):
        eui     = data.get("EUI", "?")
        fcnt    = data.get("fcnt", "?")
        port    = data.get("port", "?")
        payload = data.get("data", data.get("encdata", "(no plaintext)"))

        print(f"[{eui}] fcnt={fcnt} port={port} payload={payload}")

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "EUI":       eui,
            "fcnt":      fcnt,
            "port":      port,
            "payload":   payload,
        }

        if eui not in self.records:
            self.records[eui] = []
        self.records[eui].append(entry)

        print(f"  └ stored in memory (EUI={eui}, total={len(self.records[eui])})")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed: {close_status_code} {close_msg}")


if __name__ == "__main__":
    TOKEN = "vnoWpgAAABFpb3RuZXQudGVyYWNvbS5kaySaIG0eQDgMgCTxhShW93s="
    client = TeracomLoRaWANClient(token=TOKEN)
    client.connect()

    # Access the collected data after connection closes
    print(client.get_records())