#!/usr/bin/env python3
import json
import time
from collections import defaultdict
from html import escape
from uuid import uuid4

from flask import Flask, Request, request
from flask_socketio import SocketIO, join_room, leave_room
from loguru import logger

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])
subscribed_topics = defaultdict(set)


def get_sid(request: Request) -> str:
    return getattr(request, "sid")


@app.route("/")
def index():
    json_dict = {
        sid: list(topics)
        for (sid, topics) in subscribed_topics.items()
    }
    return f"<pre>{escape(json.dumps(json_dict, indent=2))}</pre>"


@socketio.on("connect")
def on_connect():
    sid = get_sid(request)
    logger.success(f"{sid} - Connected successfully")


@socketio.on("disconnect")
def on_disconnect():
    sid = get_sid(request)
    for topic_id in subscribed_topics[sid]:
        leave_room(topic_id)
    subscribed_topics.pop(sid, None)
    logger.info(f"{sid} - Disconnected")


@socketio.on("subscribe")
def on_subscribe(topic_id):
    sid = get_sid(request)
    subscribed_topics[sid].add(topic_id)
    join_room(topic_id)
    logger.info(f"{sid} - Subscribed to {topic_id}")


@socketio.on("unsubscribe")
def on_unsubscribe(topic_id):
    sid = get_sid(request)
    subscribed_topics[sid].remove(topic_id)
    leave_room(topic_id)
    logger.info(f"{sid} - Unsubscribed from {topic_id}")


def send_messages():
    while True:
        all_topics = set(
            topic_id for topics in subscribed_topics.values() for topic_id in topics
        )
        for topic_id in all_topics:
            payload = {"topicId": topic_id, "message": uuid4().hex}
            socketio.emit("message", payload, room=topic_id)
        time.sleep(1)


if __name__ == "__main__":
    socketio.start_background_task(send_messages)
    socketio.run(app, port=5001)
