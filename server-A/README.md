# ROOKIE-APP

Real-time camera preprocessing and streaming pipeline built with Python, OpenCV, and ZeroMQ.

## What It Does

- Captures frames from a camera source.
- Detects motion to avoid processing idle scenes.
- Applies preprocessing (exposure/noise pipeline).
- Runs blur checks and optional deblurring.
- Streams processed JPEG frames over ZeroMQ PUSH.
- Displays live frames in a local preview window.

## Project Structure

- `main.py`: App entrypoint and worker-thread orchestration.
- `config/`: Runtime settings.
- `streams/`: Camera capture, motion detector, adaptive frame skipping.
- `preprocessing/`: Frame enhancement and quality filters.
- `zmq/`: Compression and ZeroMQ sender utilities.
- `utils/`: Logging, FPS meter, queue helpers.

## Requirements

- Python 3.10+
- Camera device (or supported video source)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Press `q` in the preview window to stop the app.

## Default Runtime Settings

Configured in `config/settings.py`:

- Camera: 1280x720 at 30 FPS
- Motion gate: area threshold 1500
- ZMQ PUSH address: `tcp://*:5555`
- JPEG quality: 70

## Notes

- This repository includes a local folder named `zmq/` for project code.
- The sender implementation uses `pyzmq`; keep imports as implemented in the current source layout.