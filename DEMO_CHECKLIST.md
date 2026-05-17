# Pre-Demo Checklist

## 30 Minutes Before

- [ ] Start server: `uvicorn main:app --port 8000 --reload`
- [ ] Run `GET /health` → verify all checks show "set" or "loaded"
- [ ] Run `GET /warmup` → wait for `"sentence_transformers": "loaded"`
- [ ] Run `GET /validate/stage3` → confirm recall ≥ 0.6
- [ ] Open UI in a **fresh** browser tab (no cached state)
- [ ] Test with `psf/requests` → Stage 1 should return gaps in < 30 seconds
- [ ] Test Stage 2 with idea "Add rate limiting to HTTP client" → status CLEAR
- [ ] Confirm `bob-sessions/` directory has all 5 session files committed

## During the Demo

- [ ] Start with `https://github.com/Tracer-Cloud/opensre` (validated repo)
- [ ] Use the pre-written idea: `"Decouple node config from LangChain RunnableConfig"`
- [ ] Show the Auto-Pilot tab running all 4 stages
- [ ] When Stage 3 completes, show the dependency traces
- [ ] Hit `GET /validate/stage3` to show precision/recall live
- [ ] Show the contribution readiness score breakdown

## Fallback If API Fails

- [ ] Have a pre-recorded screen capture ready (30 seconds, no audio needed)
- [ ] Have the JSON output from a successful run saved in `examples/`
- [ ] Know the keyboard shortcut to switch tabs quickly

## Known Failure Modes

| Issue | Likely cause | Fix |
|-------|-------------|-----|
| Stage 2 takes 30+ seconds | Model not warmed up | Hit `/warmup` first |
| Stage 3 returns empty files | GitHub rate limit | Wait 60s, retry |
| Stage 4 shows no issues | Diff is clean | Use `examples/sample.diff` |
| UI shows "Running…" forever | OpenAI API key invalid | Check `/health` |
| Server freezes on Stage 3 | Old code not reloaded | Restart uvicorn |
