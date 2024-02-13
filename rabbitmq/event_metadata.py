import uuid
from datetime import datetime, timezone

ISO8601_FORMAT = r"%Y-%m-%dT%H:%M:%S.%f%z"


class EventMetadata:
    event_type: str
    event_timestamp: datetime
    event_id: str

    @classmethod
    def from_amqp_message(cls, method_frame, properties):
        # Populate metadata
        metadata = cls()
        metadata.event_type = method_frame.exchange

        # Read event_id
        try:
            metadata.event_id = properties.headers["event_id"]
        except Exception:
            raise Exception("Unable to read event_id on event, ignoring event")

        # Read event_timestamp
        try:
            metadata.event_timestamp = datetime.strptime(
                properties.headers["event_timestamp"], ISO8601_FORMAT
            )
        except Exception:
            raise Exception(
                f"Invalid event_timestamp {properties.headers.get('event_timestamp')} on message, ignoring"
            )

        return metadata

    @classmethod
    def from_event_type_enum(cls, event_type):
        metadata = cls()
        metadata.event_type = event_type.value
        metadata.event_id = str(uuid.uuid4())
        metadata.event_timestamp = datetime.now(tz=timezone.utc)

        return metadata

    def __repr__(self):
        metadata_dict = {**self.get_amqp_headers()}
        metadata_dict["event_type"] = self.event_type

        key_value_list = [f"{key}={value}" for key, value in metadata_dict.items()]
        return f"EventMetadata<{', '.join(key_value_list)}>"

    def get_amqp_headers(self):
        return {
            "event_id": self.event_id,
            "event_timestamp": self.event_timestamp.strftime(ISO8601_FORMAT),
        }
