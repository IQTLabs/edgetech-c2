"""This file includes a command and control module to direct and coordinate
different services using MQTT.
"""
import os
import json
from time import sleep
from typing import Any

import schedule

from base_mqtt_pub_sub import BaseMQTTPubSub


class C2PubSub(BaseMQTTPubSub):
    """The C2PubSub is a class that wraps command and control functionalities. Currently,
    this is limited to broadcasting to nodes to write to a new file.

    Args:
        BaseMQTTPubSub (BaseMQTTPubSub): parent class written in the EdgeTech Core module
    """

    FILE_INTERVAL = 10  # minutes
    S3_INTERVAL = 15  # minutes

    def __init__(
        self: Any,
        c2_topic: str,
        file_interval: int = FILE_INTERVAL,
        s3_interval: int = S3_INTERVAL,
        debug: bool = False,
        **kwargs: Any
    ) -> None:
        """The constructor of the C2PubSub class takes a topic name to broadcast
        to and an interval to broadcast to that topic at.

        Args:
            next_file_topic (str): The MQTT topic to broadcast a payload that changes
            the file at a given interval.
            file_interval (int): The number of minutes before C2 broadcasts a message
            to write to a new file.Defaults to FILE_INTERVAL.
        """
        super().__init__(**kwargs)
        # initialize attributes
        self.c2_topic = c2_topic
        self.file_interval = file_interval
        self.s3_interval = s3_interval
        self.debug = debug

        # create MQTT client connection
        self.connect_client()
        sleep(1)
        self.publish_registration("C2 Registration")

    def main(self: Any) -> None:
        """Main loop and function that setup the heartbeat to keep the TCP/IP
        connection alive and publishes the data to the MQTT broker every 10 minutes
        and keeps the main thread alive.
        """
        # publish heartbeat to keep the TCP/IP connection alive
        schedule.every(10).seconds.do(self.publish_heartbeat, payload="C2 Heartbeat")

        # every file interval, publish a message to broadcast to file
        # saving nodes to change files
        schedule.every(self.file_interval).minutes.do(
            self.publish_to_topic,
            topic_name=self.c2_topic,
            publish_payload=json.dumps({"msg": "NEW FILE"}),
        )

        # every s3 interval trigger a push of files up to the S3 bucket
        schedule.every(self.s3_interval).minutes.do(
            self.publish_to_topic,
            topic_name=self.c2_topic,
            publish_payload=json.dumps({"msg": "S3 SYNC"}),
        )

        while True:
            try:
                # flush pending scheduled tasks
                schedule.run_pending()
                # sleep to avoid running at CPU time
                sleep(0.001)
            except KeyboardInterrupt as exception:
                if self.debug:
                    print(exception)


if __name__ == "__main__":
    c2 = C2PubSub(
        c2_topic=str(os.environ.get("C2_TOPIC")),
        mqtt_ip=str(os.environ.get("MQTT_IP")),
    )
    c2.main()
