import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="IndexTTS batch inference runner")
    parser.add_argument("--jobs", required=True, help="Path to jobs json file")
    parser.add_argument("--config", required=True, help="IndexTTS config path")
    parser.add_argument("--model_dir", required=True, help="IndexTTS model directory")
    parser.add_argument("--device", default=None, help="cpu/cuda")
    parser.add_argument("--fp16", action="store_true", default=False)
    args = parser.parse_args()

    jobs_path = Path(args.jobs)
    if not jobs_path.exists():
        print(f"ERROR: jobs file not found: {jobs_path}")
        return 1

    with open(jobs_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    jobs = payload.get("jobs", [])
    if not jobs:
        print("No jobs provided.")
        return 0

    try:
        import torch
    except Exception as e:
        print(f"ERROR: torch import failed: {e}")
        return 2

    device = args.device
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    if device == "cpu":
        args.fp16 = False

    # Ensure all HF loaders resolve to local cache under checkpoints/hf_cache
    hf_cache_root = str(Path(args.model_dir) / "hf_cache")
    os.environ.setdefault("HF_HOME", hf_cache_root)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", hf_cache_root)
    os.environ.setdefault("TRANSFORMERS_CACHE", hf_cache_root)
    os.environ.setdefault("HF_HUB_CACHE", hf_cache_root)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    from indextts.infer_v2 import IndexTTS2

    tts = IndexTTS2(
        cfg_path=args.config,
        model_dir=args.model_dir,
        use_fp16=args.fp16,
        device=device,
    )

    results = []
    success = 0

    for job in jobs:
        idx = job.get("index")
        text = (job.get("text") or "").strip()
        voice = job.get("voice")
        output_path = job.get("output_path")

        ok = False
        error = None

        try:
            if not text:
                raise ValueError("empty text")
            if not voice or not Path(voice).exists():
                raise FileNotFoundError(f"voice not found: {voice}")
            if not output_path:
                raise ValueError("missing output_path")

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                out.unlink()

            tts.infer(spk_audio_prompt=voice, text=text, output_path=str(out))

            ok = out.exists() and out.stat().st_size > 0
            if not ok:
                error = "output file missing or empty"
            else:
                success += 1
        except Exception as e:
            error = str(e)

        results.append({
            "index": idx,
            "ok": ok,
            "output_path": output_path,
            "error": error,
        })

    summary = {
        "success": success,
        "total": len(jobs),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False))

    return 0 if success > 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
