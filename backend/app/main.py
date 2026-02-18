import logging
import warnings

# resampy 0.4.2 imports pkg_resources which is deprecated in setuptools>=80.
# basic-pitch pins resampy<0.4.3 so we can't upgrade; suppress the noise.
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

# basic-pitch/__init__.py fires root-logger WARNING messages at import time for
# optional backends (CoreML, TFLite) that aren't installed. We use ONNX via
# onnxruntime so these are irrelevant. Filter them before the route imports
# trigger the basic_pitch import chain.
class _BasicPitchImportFilter(logging.Filter):
    _SUPPRESS = ("Coremltools is not installed", "tflite-runtime is not installed")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(s in msg for s in self._SUPPRESS)

logging.getLogger().addFilter(_BasicPitchImportFilter())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import transcription, health
from .config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/py", tags=["health"])
app.include_router(transcription.router, prefix="/api/py", tags=["transcription"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Music Transcription API", "status": "running"}
