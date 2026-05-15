import websocket
import json
import os
from datetime import datetime


class TeracomLoRaWANClient:
    def __init__(self, token: str, host: str = "iotnet.teracom.dk", output_file: str = "received_data.json"):
        self.token = token
        self.server = f"wss://{host}/app?token={token}"
        self.output_file = output_file
        self.ws = None
        self._init_output_file()

    def _init_output_file(self):
        """Create or clear the output JSON file with an empty list."""
        if not os.path.exists(self.output_file):
            with open(self.output_file, "w") as f:
                json.dump([], f)

    def _append_to_file(self, entry: dict):
        """Append a new data entry to the JSON file."""
        try:
            with open(self.output_file, "r") as f:
                records = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            records = []

        records.append(entry)

        with open(self.output_file, "w") as f:
            json.dump(records, f, indent=2)

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever()

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
        self._append_to_file(entry)
        print(f"  └ saved to {self.output_file}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed: {close_status_code} {close_msg}")


if __name__ == "__main__":
    TOKEN = "vnoWpgAAABFpb3RuZXQudGVyYWNvbS5kaySaIG0eQDgMgCTxhShW93s="
    client = TeracomLoRaWANClient(token=TOKEN, output_file="received_data.json")
    client.connect()