# 02 Architecture

> System design at a glance for the sample stack.

## Main Components

- `simple-backend` generates Agora credentials and starts/stops agents
- React clients join RTC/RTM and render transcripts, chat, and avatar/video
- optional custom LLM server intercepts LLM traffic for tools, RAG, memory, biomarkers

## Core Flow

1. client calls `simple-backend`
2. backend generates tokens and sends Agora agent start request
3. client and agent join the same channel
4. optional custom LLM handles `/chat/completions`

## Sample Modes

- standard AI session
- human meeting mode with dashboard authorization
- therapist/wellness profile with Thymia/Shen/custom-LLM integrations

## Related Deep Dives

- [therapy_profile](L2/therapy_profile.md) — therapy-oriented stack and biomarker flow
