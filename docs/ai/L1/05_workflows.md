# 05 Workflows

> Step-by-step guides for common changes in the sample stack.

## Add a New Backend Profile

1. add prefixed env vars in `simple-backend/.env`
2. verify profile-specific defaults in backend config resolution
3. run backend and client with `?profile=<name>`

## Point a Profile at a Custom LLM

1. set `<PROFILE>_LLM_URL`
2. set `<PROFILE>_LLM_VENDOR=custom`
3. set `<PROFILE>_LLM_STYLE=openai`
4. verify latest `/tmp/agora_curl_*.sh` shows the public custom-LLM URL

## Run Human Meeting Mode

1. ensure dashboard integration env vars are set
2. use `/join-meeting` flow from the client
3. verify meeting authorization and service-registration paths

## Related Deep Dives

- [therapy_profile](L2/therapy_profile.md) — full therapy / biomarker / dashboard-backed workflow
