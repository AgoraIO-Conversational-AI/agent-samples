# Blog Update — Build Agora Voice & Video AI Agents

**Status**: Draft for review
**Last Updated**: 2026-03-10

This document contains the updated blog post. Key changes from the original:

1. **Pipeline mode** — added as the simplest getting-started path (3 env vars, no LLM/TTS keys)
2. **APP_CERTIFICATE now required** — replaces AGENT_AUTH_HEADER as the primary auth method
3. **Vibe coding platforms** — new section covering Lovable, v0, and how they differ from Claude Code
4. **Thymia recipe** — new section showing the Custom LLM extensibility pattern
5. **Restructured "Getting Your API Keys"** — two paths (pipeline vs inline) instead of one flat list

---

## Blog Post

---

# Build Agora Voice & Video AI Agents with Vibe Coding — No Coding Experience Required

**How I used Claude Code to clone, configure, and run Agora's Conversational AI samples on my Mac — and you can too.**

If you've been curious about building real-time voice and video AI agents but felt intimidated by the setup, this post is for you. In the accompanying video demo, I walk through the entire process of using Claude Code to build and run the Agora Conversational AI agent samples — from cloning the repo to having a live conversation with an AI agent, all running locally on my Mac.

This blog post serves as a companion guide. It covers the prerequisites, explains how the system architecture works, and walks through the API keys you'll need before you can follow along with the video.

## Watch the Video

The companion video walks through every step live, including the moments where Claude Code asks clarifying questions, handles errors, and gets both servers running. If you're a visual learner or want to see exactly what to expect, start here.

take1_safekeys.mov

## What Are We Building?

The [Agora Conversational AI Agent Samples](https://github.com/AgoraIO-Conversational-AI/agent-samples) repo contains everything you need to run voice and video AI agents locally. The samples use Agora's real-time network (SD-RTN) to handle the audio and video streaming, while connecting to your choice of LLM and text-to-speech providers for the actual AI conversation.

By the end of the video demo, you'll have a working voice AI agent you can talk to in your browser and, if you choose, a video avatar agent that gives your AI a face.

The best part? Claude Code does the heavy lifting. You give it a prompt, point it at the repo, and it handles the cloning, dependency installation, configuration, and running of both the backend and frontend.

## Prerequisites

Before following the video, you'll need two things set up: Claude Code and a basic comfort level with the terminal.

### Installing Claude Code

Claude Code is Anthropic's command-line AI coding assistant. It runs in your terminal and can read, write, and execute code on your behalf. You'll need an Anthropic account with either a Claude Pro/Max subscription or API credits.

On Mac, open Terminal and run:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

That's it — no Node.js required. The native installer handles everything. After it finishes, verify the installation:

```bash
claude --version
```

On Windows, you have two options. The simplest is to open PowerShell and run:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Alternatively, if you prefer working inside WSL (Windows Subsystem for Linux), install WSL first, then use the same curl command as Mac inside your Ubuntu terminal.

After installation, launch Claude Code by typing `claude` in your terminal. The first time you run it, you'll complete a one-time authentication flow — either signing in with your Claude Pro/Max account or providing an API key from the Anthropic Console.

### A Quick Terminal Primer

If you're new to the terminal, here are the only commands you need to know to follow along. Everything else, Claude Code handles for you.

**pwd** (Print Working Directory) — Shows you where you currently are in the file system. Think of it as "Where am I right now?"

```bash
$ pwd
/Users/yourname
```

**ls** (List) — Shows the files and folders in your current directory. It's like opening a folder in Finder to see what's inside.

```bash
$ ls
Desktop    Documents    Downloads    Projects
```

**cd** (Change Directory) — Moves you into a different folder. This is how you navigate around.

```bash
$ cd Projects
$ pwd
/Users/yourname/Projects
```

**mkdir** (Make Directory) — Creates a new folder.

```bash
$ mkdir my-ai-project
$ cd my-ai-project
```

That's the extent of the terminal knowledge you need. Once you're in the right folder and launch Claude Code, you're communicating in plain English from that point forward.

## System Architecture: The Four Components

The Agora Conversational AI system has four main components. Two run on your local machine and two are cloud services managed by Agora.

[Insert system architecture SVG]

**Your Backend Server (local)** — A Python server (simple-backend) that serves the client app, generates Agora authentication tokens, and calls the Agora REST API to start/stop AI agent instances. When you click "Join," it spins up an agent and connects it to a channel with your LLM and TTS configuration.

**The Client Application (local)** — A React web app running in your browser that captures your microphone audio and plays back the AI agent's responses. The repo includes a polished React Voice Client (recommended starting point), a React Video Client with Avatar for face-to-face-style AI conversations, and simpler HTML/JavaScript versions for quick testing.

**Agora SD-RTN (cloud)** — Agora's Software-Defined Real-Time Network, the global low-latency infrastructure that routes audio, video, and data between participants. Both client and agent join the same channel — audio flows bidirectionally through SD-RTN without you having to manage any WebRTC complexity.

**The AI Agent Instance (cloud)** — A managed agent that Agora spins up on your backend's request. It joins the channel like a real participant and runs the conversation pipeline: your speech is transcribed (STT), sent to your chosen LLM, and the response is converted to natural-sounding speech (TTS) and streamed back in real-time. It even handles interruption detection — if you start talking, the agent stops and listens.

## Getting Your API Keys

Before Claude Code can configure and run the samples, you'll need API keys. The good news: there are now two paths, and the simpler one needs just two credentials from Agora.

### Agora Credentials (Always Required)

Both paths start here. You need an **App ID** and **App Certificate** from Agora:

- Sign up for a free account at the [Agora Console](https://console.agora.io)
- Create a new project under [Project Management](https://console.agora.io/project-management)
- Enable the **App Certificate** under your project's Security settings
- See [Manage Agora Account](https://docs.agora.io/en/conversational-ai/get-started/manage-agora-account) for details

```bash
APP_ID=your_agora_app_id
APP_CERTIFICATE=your_agora_app_certificate
```

The App Certificate enables token-based authentication, which is the recommended approach. You do **not** need a separate `AGENT_AUTH_HEADER` (REST API key) — the backend generates secure v007 tokens automatically from your App Certificate.

### Path A: Pipeline Mode (Simplest — 3 Values Total)

If you've created a pipeline in [Agora Agent Builder](https://console.agora.io), you can skip all LLM and TTS configuration. The pipeline already has your LLM provider, TTS voice, and ASR settings baked in — the backend just references it by ID.

```bash
APP_ID=your_agora_app_id
APP_CERTIFICATE=your_agora_app_certificate
PIPELINE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx    # 32-char hex from Agent Builder
```

That's it. No OpenAI key, no TTS vendor, no voice ID. The pipeline owns all of that. This is the fastest way to get a working agent.

### Path B: Inline Config (Full Control)

If you want to configure every provider yourself — choose your own LLM, TTS vendor, and voice — you'll need a few more keys:

**LLM Provider:**

You'll need an API key from your chosen LLM provider. The samples default to OpenAI, so the fastest path is to grab an API key from [OpenAI's Platform](https://platform.openai.com/settings/organization/api-keys). Any OpenAI-compatible endpoint will work if you prefer a different provider.

**Text-to-Speech (TTS) Provider:**

The backend supports several TTS vendors. Pick one and get your API key:

- **[Rime](https://rime.ai/)** — Fast, high-quality voices
- **[ElevenLabs](https://elevenlabs.io/)** — Realistic, customizable voices with a wide voice library
- **[OpenAI](https://platform.openai.com/)** — Uses the same API key as your LLM if you go with OpenAI for both
- **[Cartesia](https://cartesia.ai/)** — Low-latency voice synthesis

You'll also need a Voice ID from your chosen provider. Each vendor's documentation or voice library has a catalog you can browse to find the voice you like.

**Avatar Provider (Video Client Only):**

If you want to run the video avatar client, you'll need credentials from an avatar provider as well. Agora's documentation on [AI Avatar Overview](https://docs.agora.io/en/conversational-ai/overview/product-overview) covers the supported vendors and configuration details.

### Keep Your Keys Handy

Once you have your keys, keep them in a note or text file. When you follow along with the video and Claude Code asks for configuration, you'll paste them into the `.env` file that Claude Code creates. Here's a preview of what you'll need:

**Pipeline mode (simplest):**

```bash
# Agora (all you need)
APP_ID=your_agora_app_id
APP_CERTIFICATE=your_agora_app_certificate
PIPELINE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Inline config (full control):**

```bash
# Agora
APP_ID=your_agora_app_id
APP_CERTIFICATE=your_agora_app_certificate

# LLM
LLM_API_KEY=your_openai_api_key

# TTS
TTS_VENDOR=elevenlabs          # or: rime, openai, cartesia
TTS_KEY=your_tts_api_key
TTS_VOICE_ID=your_chosen_voice_id
```

## Let Claude Code Do the Work

With your prerequisites set up and API keys ready, you're all set to follow along with the video. Here's the prompt I use to kick things off:

**For Voice:**

```
Clone https://github.com/AgoraIO-Conversational-AI/agent-samples
and then I want to run the React Voice AI Agent here on my laptop.
Be sure to read the AGENT.md before you begin building.
```

**For Video with Avatar:**

```
Clone https://github.com/AgoraIO-Conversational-AI/agent-samples
and then I want to run the Video AI Agent with Avatar Sample here
on my laptop. Be sure to read the AGENT.md before you begin building.
```

Claude Code reads the repo's `AGENT.md` file (a comprehensive guide written specifically for AI coding assistants), clones the repository, installs all dependencies, prompts you for your API keys, configures the environment files, and starts both the backend and frontend servers.

Within minutes, you'll have a working AI voice agent running in your browser that you can talk to in real-time.

## Beyond Claude Code: Vibe Coding on Other Platforms

Claude Code isn't the only way to vibe-code with these samples. If you prefer a browser-based AI coding experience, Agora maintains dedicated starter repos for two popular platforms:

### Lovable

[Lovable](https://lovable.dev) is a browser-based AI coding platform that generates full-stack React apps from natural language descriptions. It uses Vite + React with Supabase Edge Functions for the backend.

To get started, paste this prompt into Lovable:

```
Import https://github.com/AgoraIO-Conversational-AI/vibe-coding-lovable and
read AGENT.md then set it up
```

Lovable will import the repo, read the AI instructions, and generate a working voice agent app. The backend runs as Supabase Edge Functions (Deno) — no local server needed.

**Repo:** [AgoraIO-Conversational-AI/vibe-coding-lovable](https://github.com/AgoraIO-Conversational-AI/vibe-coding-lovable)

### v0 (Vercel)

[v0](https://v0.dev) is Vercel's AI coding platform that generates Next.js applications. It uses the App Router pattern with API routes for the backend.

To get started, paste this prompt into v0:

```
Import https://github.com/AgoraIO-Conversational-AI/vibe-coding-v0 and
read AGENT.md then set it up
```

v0 imports the repo, reads the instructions, and scaffolds a working voice agent with Next.js API routes handling the backend.

**Repo:** [AgoraIO-Conversational-AI/vibe-coding-v0](https://github.com/AgoraIO-Conversational-AI/vibe-coding-v0)

### Why Separate Repos?

The vibe-coding repos are self-contained single-repo versions of agent-samples, purpose-built for AI platform constraints. v0 and Lovable can't install packages from GitHub (only npm), can't read into `node_modules` to debug, and work best when they own all the source code. So the vibe-coding repos inline the RTC/RTM logic and UI components that agent-samples imports from packages.

Claude Code doesn't have these limitations — it works directly with agent-samples' three-package architecture, can read into `node_modules`, and can install GitHub packages. This makes Claude Code the most capable AI coding approach, but v0 and Lovable offer the convenience of zero local setup.

For the full architectural comparison, see the [Vibe Coding Design doc](https://github.com/AgoraIO-Conversational-AI/agent-samples/blob/main/design/VIBE_CODING_DESIGN.md).

## Going Further: The Thymia Voice Biomarker Demo

Once you have a basic voice agent running, the sample architecture supports powerful extensions through Agora's [Custom LLM server](https://github.com/AgoraIO-Conversational-AI/server-custom-llm). One example is the Thymia voice biomarker wellness demo.

### What Is It?

[Thymia](https://thymia.ai/) provides real-time voice biomarker analysis — stress, burnout, fatigue, and emotion scores computed from vocal patterns during a live conversation. The demo connects a Custom LLM server (sitting between Agora ConvoAI and OpenAI) to the Thymia Sentinel API. As the user speaks, audio is analyzed in real-time and biomarker scores are:

- **Injected into the LLM system prompt** so the AI therapist (Bella) can reference them in conversation
- **Displayed in the client UI** via a dedicated Thymia tab showing wellness, clinical, and emotion scores
- **Used for safety analysis** — if concerns are detected, guidance appears for the operator

### How It Works

```
react-video-client-avatar → simple-backend → Agora ConvoAI → server-custom-llm/node
                                                                  ├── go-audio-subscriber (RTC)
                                                                  ├── Thymia module → Thymia Sentinel API
                                                                  └── RTM → Client (biomarkers)
```

The Custom LLM server intercepts LLM requests, spawns a Go binary that subscribes to the RTC channel audio, pipes it to Thymia for analysis, and pushes the resulting biomarker scores back to both the LLM (via system prompt injection) and the client (via RTM messages). The existing `simple-backend` and `react-video-client-avatar` from agent-samples work unchanged — Thymia is enabled purely through environment variables.

This pattern — using a Custom LLM server to add capabilities without modifying the backend or client — is how you extend the agent samples for your own use cases: RAG, tool calling, conversation memory, or any custom processing pipeline.

For full setup instructions, see the [Thymia recipe](https://github.com/AgoraIO-Conversational-AI/agent-samples/blob/main/recipes/thymia.md).

## Wrapping Up

What used to require deep knowledge of WebRTC, server configuration, and multiple API integrations can now be accomplished with a single prompt. Whether you use Claude Code on your local machine, Lovable in the browser, or v0 on Vercel, the path from zero to a working voice AI agent has never been shorter.

And with pipeline mode, the barrier is even lower — just an Agora App ID, App Certificate, and a pipeline ID. No LLM key, no TTS key, no vendor configuration. Build your pipeline in Agent Builder, point the backend at it, and go.

If you build something interesting with these samples, I'd love to hear about it. Drop a comment or reach out — and happy building.

## References

- [Agora Conversational AI Agent Samples (MIT)](https://github.com/AgoraIO-Conversational-AI/agent-samples) — github.com/AgoraIO-Conversational-AI/agent-samples
- [Agora Conversational AI Documentation](https://docs.agora.io/en/conversational-ai/overview/product-overview) — docs.agora.io
- [Claude Code Setup Guide](https://code.claude.com/docs/en/setup) — code.claude.com
- [Agora Console](https://console.agora.io) — console.agora.io
- [OpenAI API Keys](https://platform.openai.com/settings/organization/api-keys) — platform.openai.com
- TTS Providers — [Rime](https://rime.ai/) | [ElevenLabs](https://elevenlabs.io/) | [OpenAI TTS](https://platform.openai.com/) | [Cartesia](https://cartesia.ai/)
- Vibe Coding Repos — [Lovable](https://github.com/AgoraIO-Conversational-AI/vibe-coding-lovable) | [v0](https://github.com/AgoraIO-Conversational-AI/vibe-coding-v0)
- [Custom LLM Server](https://github.com/AgoraIO-Conversational-AI/server-custom-llm) — server-custom-llm
- [Thymia Voice Biomarker Recipe](https://github.com/AgoraIO-Conversational-AI/agent-samples/blob/main/recipes/thymia.md) — recipes/thymia.md
- [Vibe Coding Design Doc](https://github.com/AgoraIO-Conversational-AI/agent-samples/blob/main/design/VIBE_CODING_DESIGN.md) — design rationale for platform-specific repos
