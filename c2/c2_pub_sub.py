"""This file includes a command and control module to direct and coordinate
differnt services using MQTT.
"""
import os
import json
from time import sleep
from typing import Any

import schedule

from base_mqtt_pub_sub import BaseMQTTPubSub


class C2PubSub(BaseMQTTPubSub):
    """The C2PubSub is a class that wraps command and control functionalities. Currently,
    this is limitied to broadcasting to nodes to write to a new file.

    Args:
        BaseMQTTPubSub (BaseMQTTPubSub): parent class written in the EdgeTech Core module
    """

    FILE_INTERVAL = 10  # minutes
    S3_INTERVAL = 15 # minutes

    def __init__(
        self: Any,
        c2_topic: str,
        file_interval: int = FILE_INTERVAL,
        s3_interval: int = S3_INTERVAL,
        **kwargs: Any
    ) -> None:
        """The constructor of the C2PubSub class takes a topic name to broadcast
        to and an interval to broadcast to that topic at.

        Args:
            next_file_topic (str): The MQTT topic to broadcast a paylod that changes
            the file at a given interval.
            file_interval (int): The number of minutes before C2 broadcasts a message
            to write to a new file.Defaults to FILE_INTERVAL.
        """
        super().__init__(**kwargs)
        self.c2_topic = c2_topic
        self.file_interval = file_interval
        self.s3_interval = s3_interval

        self.connect_client()
        sleep(1)
        self.publish_registration("C2 Registration")

    def main(self: Any) -> None:
        """Main loop and function that setup the heartbeat to keep the TCP/IP
        connection alive and publishes the data to the MQTT broker every 10 minutes
        and keeps the main thread alive.
        """
        schedule.every(10).seconds.do(self.publish_heartbeat, payload="C2 Heartbeat")

        schedule.every(self.file_interval).minutes.do(
            self.publish_to_topic,
            topic_name=self.c2_topic,
            publish_payload=json.dumps({"msg": "NEW FILE"}),
        )

        schedule.every(self.s3_interval).minutes.do(
            self.publish_to_topic,
            topic_name=self.c2_topic,
            publish_payload=json.dumps({"msg": "S3 SYNC"}),
        )

        while True:
            try:
                schedule.run_pending()
                sleep(0.001)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    c2 = C2PubSub(
        c2_topic=str(os.environ.get("C2_TOPIC")),
        mqtt_ip=str(os.environ.get("MQTT_IP")),
    )
    c2.main()
