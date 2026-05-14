import json
import time
from typing import Optional, TypedDict

import paho.mqtt.client as mqtt

from implementation.internet_device import InternetDevice


class SignalData(TypedDict):
    rssi: float
    quality: float
    noise: Optional[float]


class LorawanClient(InternetDevice):
    def __init__(
        self,
        device_name: str,
        ip: str,
        port: int = 1883,
        topic: str = "#",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__(ip=ip, device_name=device_name)

        self.port = port
        self.topic = topic
        self.username = username
        self.password = password

        self.__latest_signal_data: Optional[SignalData] = None
        self.__message_received = False

        self.__client = mqtt.Client()

        if self.username is not None:
            self.__client.username_pw_set(self.username, self.password)

        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message

    def get_signal_metrics(self, timeout: int = 10) -> SignalData:
        """
        Connects to the LoRaWAN MQTT broker, waits for one uplink message,
        extracts rssi, quality and noise, and returns them.

        Returns:
            SignalData:
                rssi: RSSI value
                quality: Link quality, SNR or quality value depending on payload
                noise: Noise value, if available or calculated
        """

        self.__latest_signal_data = None
        self.__message_received = False

        print(f"{self}: connecting to MQTT broker {self.ip}:{self.port}")
        self.__client.connect(self.ip, self.port, keepalive=60)
        self.__client.loop_start()

        start_time = time.time()

        while not self.__message_received:
            if time.time() - start_time > timeout:
                self.__client.loop_stop()
                self.__client.disconnect()
                raise TimeoutError(
                    f"No LoRaWAN MQTT message received on topic '{self.topic}' within {timeout} seconds"
                )

            time.sleep(0.1)

        self.__client.loop_stop()
        self.__client.disconnect()

        if self.__latest_signal_data is None:
            raise ValueError("MQTT message was received, but no signal metrics could be extracted")

        return self.__latest_signal_data

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"{self}: connected to MQTT broker")
            print(f"{self}: subscribing to topic {self.topic}")
            client.subscribe(self.topic)
        else:
            print(f"{self}: failed to connect, return code {rc}")

    def __on_message(self, client, userdata, msg):
        print(f"{self}: received MQTT message on topic {msg.topic}")

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            print(f"{self}: message was not valid JSON")
            return

        signal_data = self.__extract_signal_data(payload)

        if signal_data is not None:
            self.__latest_signal_data = signal_data
            self.__message_received = True
        else:
            print(f"{self}: no rssi/quality/noise found in MQTT payload")

    def __extract_signal_data(self, payload: dict) -> Optional[SignalData]:
        """
        Supports different payload formats:

        1. Direct payload:
            {
                "rssi": -80,
                "quality": 7.5,
                "noise": -100
            }

        2. Decoded payload:
            {
                "object": {
                    "rssi": -80,
                    "quality": 7.5,
                    "noise": -100
                }
            }

        3. ChirpStack-like payload:
            {
                "rxInfo": [
                    {
                        "rssi": -80,
                        "snr": 7.5
                    }
                ]
            }

        4. The Things Stack-like payload:
            {
                "uplink_message": {
                    "rx_metadata": [
                        {
                            "rssi": -80,
                            "snr": 7.5
                        }
                    ]
                }
            }
        """

        # Case 1: values are directly in payload
        rssi = payload.get("rssi")
        quality = payload.get("quality")
        noise = payload.get("noise")

        if rssi is not None and quality is not None:
            return {
                "rssi": float(rssi),
                "quality": float(quality),
                "noise": float(noise) if noise is not None else None,
            }

        # Case 2: values are inside decoded object
        decoded_object = payload.get("object")

        if isinstance(decoded_object, dict):
            rssi = decoded_object.get("rssi")
            quality = decoded_object.get("quality")
            noise = decoded_object.get("noise")

            if rssi is not None and quality is not None:
                return {
                    "rssi": float(rssi),
                    "quality": float(quality),
                    "noise": float(noise) if noise is not None else None,
                }

        # Case 3: ChirpStack rxInfo
        rx_info = payload.get("rxInfo")

        if isinstance(rx_info, list) and len(rx_info) > 0:
            first_rx = rx_info[0]

            rssi = first_rx.get("rssi")
            snr = first_rx.get("snr")

            if rssi is not None and snr is not None:
                return {
                    "rssi": float(rssi),
                    "quality": float(snr),
                    "noise": float(rssi) - float(snr),
                }

        # Case 4: The Things Stack / TTN rx_metadata
        uplink_message = payload.get("uplink_message")

        if isinstance(uplink_message, dict):
            rx_metadata = uplink_message.get("rx_metadata")

            if isinstance(rx_metadata, list) and len(rx_metadata) > 0:
                first_rx = rx_metadata[0]

                rssi = first_rx.get("rssi")
                snr = first_rx.get("snr")

                if rssi is not None and snr is not None:
                    return {
                        "rssi": float(rssi),
                        "quality": float(snr),
                        "noise": float(rssi) - float(snr),
                    }

        return None