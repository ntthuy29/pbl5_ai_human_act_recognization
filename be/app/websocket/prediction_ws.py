from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.app_state import app_state

router = APIRouter()


class PredictionConnectionManager:
	def __init__(self) -> None:
		self.active_connections: set[WebSocket] = set()

	async def connect(self, websocket: WebSocket) -> None:
		await websocket.accept()
		self.active_connections.add(websocket)

	def disconnect(self, websocket: WebSocket) -> None:
		self.active_connections.discard(websocket)

	async def broadcast(self, message: dict[str, Any]) -> None:
		if not self.active_connections:
			return

		stale_connections: list[WebSocket] = []
		for websocket in list(self.active_connections):
			try:
				await websocket.send_json(message)
			except Exception:
				stale_connections.append(websocket)

		for websocket in stale_connections:
			self.disconnect(websocket)


prediction_manager = PredictionConnectionManager()


@router.websocket("/ws/predictions")
async def websocket_predictions(websocket: WebSocket):
	await prediction_manager.connect(websocket)

	try:
		if app_state.latest_prediction:
			await websocket.send_json({
				"type": "latest_prediction",
				"data": {
					**app_state.latest_prediction,
					"is_live": app_state.monitoring,
				},
			})

		while True:
			await websocket.receive_text()
	except WebSocketDisconnect:
		prediction_manager.disconnect(websocket)
	except Exception:
		prediction_manager.disconnect(websocket)


async def broadcast_latest_prediction() -> None:
	if not app_state.latest_prediction:
		return

	await prediction_manager.broadcast({
		"type": "latest_prediction",
		"data": {
			**app_state.latest_prediction,
			"is_live": app_state.monitoring,
		},
	})


def notify_latest_prediction() -> None:
	loop = app_state.event_loop
	if loop is None or loop.is_closed():
		return

	asyncio.run_coroutine_threadsafe(broadcast_latest_prediction(), loop)
