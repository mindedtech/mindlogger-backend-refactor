import logging
import sys
import uuid

from bson import ObjectId


def mongoid_to_uuid(id_):
    if isinstance(id_, str) and "/" in id_:
        id_ = id_.split("/").pop()
    return uuid.UUID(str(id_) + "00000000")


def uuid_to_mongoid(uid: uuid.UUID) -> None | ObjectId:
    return ObjectId(uid.hex[:-8]) if uid.hex[-8:] == "0" * 8 else None


def get_logger(name) -> logging.Logger:
    formatter = logging.Formatter(f"[{name}] %(levelname)s - %(message)s")
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    log = logging.getLogger()
    log.addHandler(handler)
    return log
