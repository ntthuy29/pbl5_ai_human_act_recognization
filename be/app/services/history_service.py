import json

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.prediction_history import PredictionHistory

class HistoryService:
    def add(self, prediction, user_id: int | None = None, session_id: int | None = None):
        normalized_prediction = self._normalize_prediction(prediction)
        with SessionLocal() as db:
            db.add(
                PredictionHistory(
                    payload=normalized_prediction,
                    user_id=user_id,
                    session_id=session_id,
                )
            )
            db.commit()

    def get_all(self, limit: int = 100, user_id: int | None = None):
        with SessionLocal() as db:
            query = select(PredictionHistory).order_by(PredictionHistory.created_at.desc()).limit(limit)
            if user_id is not None:
                query = query.where(PredictionHistory.user_id == user_id)

            rows = db.execute(query).scalars().all()
            return [row.payload for row in rows]

    def _normalize_prediction(self, prediction):
        # Ensure payload can always be serialized into PostgreSQL JSON.
        return json.loads(json.dumps(prediction, default=str))

history_service = HistoryService()