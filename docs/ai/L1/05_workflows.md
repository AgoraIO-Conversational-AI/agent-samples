# 05 Workflows

> Step-by-step guides for common development tasks across the sample stack.

## Add a New Profile

1. Choose a profile name (e.g., `THERAPY`)
2. Add `THERAPY_` prefixed variables to `.env` (copy from existing profile section)
3. Minimum required: `THERAPY_APP_ID`, `THERAPY_APP_CERTIFICATE`, `THERAPY_CUSTOMER_ID`, `THERAPY_CUSTOMER_SECRET`
4. Call backend with `?profile=therapy` — config loads automatically
5. No code changes needed; profile system is fully data-driven

## Add a New TTS Vendor

1. Edit `simple-backend/core/agent.py` — find `build_tts_config()`
2. Add a new `elif vendor == "your_vendor":` block
3. Build the vendor-specific config dict following the pattern of existing vendors
4. Add env variables: `<PROFILE>_TTS_VENDOR=your_vendor`, `<PROFILE>_TTS_API_KEY=...`
5. Add defaults to `simple-backend/core/config.py` if needed

## Add a New Backend Route

1. Edit `simple-backend/local_server.py`
2. Add route function with `@app.route('/your-route')`
3. Add CORS headers: set `Access-Control-Allow-Origin` and `Access-Control-Allow-Headers`
4. If the route needs profile config, call `initialize_constants(profile)` first
5. Add a test in `simple-backend/tests/`

## Add a New React Hook

1. Create `hooks/use{Name}.ts` in the relevant client directory
2. Follow the pattern of existing hooks (typed state, explicit deps)
3. Import and use in the main component (`VoiceClient.tsx` or `VideoAvatarClient.tsx`)
4. If the hook needs cleanup, return a cleanup function from `useEffect`

## Add a New UI Component

1. Check if `@agora/agent-ui-kit` already provides the component
2. If not, create in the client's `components/` directory
3. Import Tailwind classes for styling (no external CSS files)
4. For responsive behavior, use `use-is-mobile.ts` hook

## Deploy with PM2

1. Edit `ecosystem.config.js` to add or modify app config
2. Set environment variables in the `env` block
3. For Next.js apps, ensure `NEXT_PUBLIC_BASE_PATH` is set in both build and runtime env
4. Run `pm2 start ecosystem.config.js`
5. Verify with `pm2 status` and `pm2 logs`

## Deploy Backend to AWS Lambda

1. Backend supports Lambda via `lambda_handler.py`
2. Package: `simple-backend/core/` + `lambda_handler.py` + `requirements.txt`
3. Set env vars in Lambda configuration (no `.env` file needed)
4. Entry point: `lambda_handler.handler`

## Run Backend Tests

```bash
cd simple-backend
source venv/bin/activate
pytest                    # all tests
pytest tests/test_agent.py  # specific test file
pytest -v                 # verbose output
```

## Add a New Recipe

1. Create `recipes/your_recipe.md`
2. Document: purpose, architecture, required env vars, setup steps
3. Include a profile template section showing all needed `<PROFILE>_*` variables
4. Run `npx prettier --write recipes/your_recipe.md` before committing

## Debug Agent Creation Failures

1. Start backend with debug: `GET /start-agent?channel=test&profile=voice&debug=1`
2. Check response `debug` field for redacted payload
3. Check `/tmp/agora_curl_*.sh` for full request/response
4. Common issues:
   - `"location": null` → `MLLM_LOCATION` not set
   - 400 error → invalid avatar ID or missing vendor config
   - `-11033 user offline` → agent creation returned 400

## Related Deep Dives

- [Profile Configuration](deep_dives/profile_configuration.md) — Vendor configs, MLLM setup
- [Agent Lifecycle](deep_dives/agent_lifecycle.md) — Payload building, API flow
