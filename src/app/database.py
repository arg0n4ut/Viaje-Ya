import os
from typing import Optional
from threading import Lock
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_client: Optional[MongoClient] = None
_client_lock = Lock()

def _build_connection_uri() -> str:
	return os.getenv("MONGODB_URI", "mongodb://localhost:27017")

def _resolve_db_name() -> str:
	return os.getenv("MONGODB_DB", "viaje_ya")

def get_client() -> MongoClient:
	global _client
	if _client is None:
		with _client_lock:
			if _client is None:
				_client = MongoClient(_build_connection_uri(), uuidRepresentation="standard")
	return _client

def set_client(client: Optional[MongoClient]) -> None:
	# override active Mongo client, used by tests
	global _client
	with _client_lock:
		if _client is not None and _client is not client:
			_client.close()
		_client = client

def get_database() -> Database:
	return get_client()[_resolve_db_name()]

def get_trip_collection() -> Collection:
	return get_database()["trips"]

def get_participant_collection() -> Collection:
	return get_database()["participants"]

def clear_database() -> None:
	#  helper for tests to reset all collection
	db = get_database()
	db.drop_collection("trips")
	db.drop_collection("participants")


