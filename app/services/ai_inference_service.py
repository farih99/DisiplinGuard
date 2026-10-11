from app.core.config import settings
from app.core.exceptions import AIUnavailableError
from app.schemas.prediction import PredictionCreateRequest


class AIInferenceService:
    """Adapter inferensi model lokal. Tidak membuat prediksi tiruan."""

    def __init__(self) -> None:
        self.model_path = settings.model_path
        self.scaler_path = settings.scaler_path

    def predict(self, payload: PredictionCreateRequest) -> dict:
        # TODO: [PTM-06] Muat model/scaler hasil training dan implementasikan preprocessing.
        # TODO: [PTM-06] Pastikan urutan fitur identik dengan saat training model di Colab.
        # TODO: [PTM-06] Tetapkan mapping label keluaran model ke tinggi/sedang/rendah.
        # TODO: [PTM-06] Risk score perlu didefinisikan: confidence, 1 - probabilitas kelas tertentu,
        # atau formula lain yang disepakati. Jangan menyamakan confidence dengan risk tanpa validasi.
        raise AIUnavailableError(
            "Model AI belum dikonfigurasi. Prediksi belum dapat dilakukan."
        )
