import json

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.prediction_history import PredictionHistory

class HistoryService:
    def add(self, prediction):
        normalized_prediction = self._normalize_prediction(prediction)
        with SessionLocal() as db:
            db.add(PredictionHistory(payload=normalized_prediction))
            db.commit()

    def get_all(self, limit: int = 100):
        with SessionLocal() as db:
            rows = db.execute(
                select(PredictionHistory)
                .order_by(PredictionHistory.created_at.desc())
                .limit(limit)
            ).scalars().all()
            return [row.payload for row in rows]

    def _normalize_prediction(self, prediction):
        # Ensure payload can always be serialized into PostgreSQL JSON.
        return json.loads(json.dumps(prediction, default=str))

history_service = HistoryService()