"""Benchmark Visualizer Web Service.

A standalone web service for visualizing benchmark results.
Supports LoComo and LongMemEval benchmark visualization.
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Benchmark Visualizer")

# Get the benchmarks directory
BENCHMARKS_DIR = Path(__file__).parent.parent


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main benchmark visualizer page."""
    html_path = Path(__file__).parent / "static" / "index.html"
    with open(html_path) as f:
        return f.read()


@app.get("/api/locomo")
async def get_locomo_results(mode: str = "search") -> dict[str, Any]:
    """Get LoComo benchmark results.

    Returns pre-computed benchmark results from the locomo directory.

    Args:
        mode: Either "search" (default) or "think" to select which results to load
    """
    try:
        # Determine filename based on mode
        if mode == "think":
            filename = "benchmark_results_think.json"
        else:
            filename = "benchmark_results.json"

        results_path = BENCHMARKS_DIR / "locomo" / "results" / filename

        if not results_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark results not found for mode '{mode}'. Please run the benchmark first with {'--use-think' if mode == 'think' else 'default settings'}."
            )

        with open(results_path) as f:
            results = json.load(f)

        return results
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse benchmark results: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/longmemeval")
async def get_longmemeval_results() -> dict[str, Any]:
    """Get LongMemEval benchmark results.

    Returns pre-computed benchmark results from the longmemeval directory.
    """
    try:
        results_path = BENCHMARKS_DIR / "longmemeval" / "results" / "benchmark_results.json"
        print(f"chcking path {results_path}")
        logging.info(f"chcking path {results_path}")

        if not results_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Benchmark results not found. Please run the benchmark first."
            )

        with open(results_path) as f:
            results = json.load(f)

        return results
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse benchmark results: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="127.0.0.1", port=8001)
