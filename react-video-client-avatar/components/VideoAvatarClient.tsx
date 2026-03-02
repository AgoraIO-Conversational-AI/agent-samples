"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Mic, MicOff, Video, VideoOff, Settings, Phone, PhoneOff, SendHorizontal } from "lucide-react";
import { useAgoraVideoClient } from "@/hooks/useAgoraVideoClient";
import { useAudioVisualization } from "@/hooks/useAudioVisualization";
import { IconButton } from "@agora/agent-ui-kit";
import { Conversation, ConversationContent } from "@agora/agent-ui-kit";
import { Message, MessageContent } from "@agora/agent-ui-kit";
import { Response } from "@agora/agent-ui-kit";
import { AvatarVideoDisplay, LocalVideoPreview } from "@agora/agent-ui-kit";
import { VideoGrid, MobileTabs } from "@agora/agent-ui-kit";
import { AgoraLogo } from "@agora/agent-ui-kit";
import { SettingsDialog, SessionPanel } from "@agora/agent-ui-kit";
import { ThymiaPanel, useThymia } from "@agora/agent-ui-kit";
import type { RTMEventSource } from "@agora/agent-ui-kit";
import { RTMHelper } from "@agora/conversational-ai/helper/rtm";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./ThemeToggle";

const DEFAULT_BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8082";
const DEFAULT_PROFILE = process.env.NEXT_PUBLIC_DEFAULT_PROFILE || "VIDEO";
const THYMIA_ENABLED = process.env.NEXT_PUBLIC_ENABLE_THYMIA === "true";

const SENSITIVE_KEYS = [
  "api_key", "key", "token", "adc_credentials_string",
  "subscriber_token", "rtm_token", "ticket", "anam_api_key",
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function redactSensitiveFields(obj: any): any {
  if (typeof obj !== "object" || obj === null) return obj;
  if (Array.isArray(obj)) return obj.map(redactSensitiveFields);
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (SENSITIVE_KEYS.includes(k) && typeof v === "string" && v.length > 6) {
      out[k] = v.slice(0, 6) + "***";
    } else {
      out[k] = redactSensitiveFields(v);
    }
  }
  return out;
}

export function VideoAvatarClient() {
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL);
  const [agentUID, setAgentUID] = useState<string | undefined>(undefined);
  const [agentId, setAgentId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [enableLocalVideo, setEnableLocalVideo] = useState(true);
  const [enableAvatar, setEnableAvatar] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [enableAivad, setEnableAivad] = useState(true);
  const [language, setLanguage] = useState("en-US");
  const [profile, setProfile] = useState("");
  const [prompt, setPrompt] = useState("");
  const [greeting, setGreeting] = useState("");
  const [activeTab, setActiveTab] = useState("video");
  const _conversationRef = useRef<HTMLDivElement>(null);
  const [autoConnect, setAutoConnect] = useState(false);
  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);
  const [sessionPayload, setSessionPayload] = useState<object | null>(null);

  // Read URL parameters on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlProfile = params.get("profile");
      if (urlProfile) {
        setProfile(urlProfile);
      }
      if (params.get("autoconnect") === "true") {
        setAutoConnect(true);
      }
    }
  }, []);

  const {
    isConnected,
    isMuted,
    micState,
    messageList,
    currentInProgressMessage,
    isAgentSpeaking: _isAgentSpeaking,
    localAudioTrack,
    remoteVideoTrack: avatarVideoTrack,
    joinChannel,
    leaveChannel,
    toggleMute,
    sendMessage,
    rtcHelperRef,
  } = useAgoraVideoClient();

  // Removed verbose logging - see useAgoraVideoClient for agent message logs

  // Get audio visualization data (restart on mute/unmute to fix Web Audio API connection)
  const frequencyData = useAudioVisualization(
    localAudioTrack,
    isConnected && !isMuted,
  );

  // RTM event source adapter for Thymia hooks
  const rtmSource = useMemo<RTMEventSource>(
    () => ({
      on: (e, fn) => RTMHelper.getInstance().on(e, fn),
      off: (e, fn) => RTMHelper.getInstance().off(e, fn),
    }),
    [],
  );

  // Thymia voice biomarker data (opt-in via NEXT_PUBLIC_ENABLE_THYMIA)
  const {
    biomarkers,
    wellness,
    clinical,
    progress: thymiaProgress,
    safety: thymiaSafety,
  } = useThymia(rtmSource, THYMIA_ENABLED && isConnected);

  // Local video state - managed by RTCHelper
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [localVideoTrack, setLocalVideoTrack] = useState<any>(null);
  const [isLocalVideoActive, setIsLocalVideoActive] = useState(false);

  // Sync local video track from RTCHelper
  useEffect(() => {
    const rtcHelper = rtcHelperRef.current;
    if (!rtcHelper) return;

    // Update local state when RTCHelper's video track changes
    const interval = setInterval(() => {
      const currentTrack = rtcHelper.localVideoTrack;
      const currentEnabled = rtcHelper.getVideoEnabled();

      // Check if track object reference changed (new track created)
      if (currentTrack !== localVideoTrack) {
        console.log("[VideoAvatarClient] Track changed, updating state");
        setLocalVideoTrack(currentTrack);
        setIsLocalVideoActive(currentEnabled);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [rtcHelperRef.current, localVideoTrack]);

  const handleStart = async () => {
    setIsLoading(true);
    try {
      // Build query params for backend
      const params = new URLSearchParams();

      // Add profile override if provided, otherwise use default "VIDEO" profile
      if (profile.trim()) {
        params.append("profile", profile.trim());
      } else {
        params.append("profile", DEFAULT_PROFILE);
      }

      // Add agent settings
      params.append("enable_aivad", enableAivad.toString());
      params.append("asr_language", language);

      // Add prompt and greeting if provided
      if (prompt.trim()) {
        params.append("prompt", prompt.trim());
      }
      if (greeting.trim()) {
        params.append("greeting", greeting.trim());
      }

      // Phase 1: Get tokens only (don't start agent yet)
      params.append("connect", "false");
      const tokenUrl = `${backendUrl}/start-agent?${params.toString()}`;
      const tokenResponse = await fetch(tokenUrl);

      if (!tokenResponse.ok) {
        throw new Error(`Backend error: ${tokenResponse.statusText}`);
      }

      const data = await tokenResponse.json();

      if (data.agent?.uid) {
        setAgentUID(data.agent.uid);
      }

      // Phase 2: Join channel first so RTM is ready for greeting
      await joinChannel({
        appId: data.appid,
        channel: data.channel,
        token: data.token || null,
        uid: parseInt(data.uid),
      });

      // Auto-enable local video if checkbox was checked
      if (enableLocalVideo && rtcHelperRef.current) {
        const rtcHelper = rtcHelperRef.current;

        // Create video track using RTCHelper
        await rtcHelper.createVideoTrack({ encoderConfig: "720p_2" });

        // Publish video track
        if (rtcHelper.localVideoTrack && rtcHelper.client) {
          await rtcHelper.client.publish(rtcHelper.localVideoTrack);
        }

        // Update local state
        setLocalVideoTrack(rtcHelper.localVideoTrack);
        setIsLocalVideoActive(true);
      }

      // Phase 3: Now start the agent (client is listening for greeting)
      params.delete("connect");
      params.append("channel", data.channel);
      params.append("debug", "true");
      const agentUrl = `${backendUrl}/start-agent?${params.toString()}`;
      const agentResponse = await fetch(agentUrl);

      if (!agentResponse.ok) {
        throw new Error(`Agent start error: ${agentResponse.statusText}`);
      }

      const agentData = await agentResponse.json();

      // Store agent_id from the actual agent response
      if (agentData.agent_response?.response) {
        try {
          const resp = typeof agentData.agent_response.response === "string"
            ? JSON.parse(agentData.agent_response.response)
            : agentData.agent_response.response;
          if (resp.agent_id) {
            setAgentId(resp.agent_id);
            setSessionAgentId(resp.agent_id);
          }
        } catch {
          // ignore parse errors
        }
      }

      // Store redacted payload for session panel
      if (agentData.debug?.agent_payload) {
        setSessionPayload(redactSensitiveFields(agentData.debug.agent_payload));
      }
    } catch (error) {
      console.error("Failed to start:", error);
      alert(
        `Failed to start: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-connect after state is committed
  useEffect(() => {
    if (autoConnect) {
      setAutoConnect(false);
      handleStart();
    }
  }, [autoConnect]);

  const handleStop = async () => {
    // RTCHelper.leave() will cleanup video track automatically
    await leaveChannel();
    setSessionAgentId(null);
    setSessionPayload(null);
  };

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || !isConnected) return;

    const success = await sendMessage(chatMessage, agentUID || "100");

    if (success) {
      setChatMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleVideo = async () => {
    const rtcHelper = rtcHelperRef.current;
    if (!rtcHelper) return;

    const newState = !isLocalVideoActive;
    await rtcHelper.setVideoEnabled(newState);
    setIsLocalVideoActive(newState);
  };

  // Helper to determine if message is from agent
  // Agent messages have uid: 0 (stream_id: 0)
  const isAgentMessage = (uid: number) => {
    return uid === 0;
  };

  const formatTime = (ts?: number) => {
    if (!ts) return "";
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex h-screen flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 px-4 py-3 md:py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg md:text-xl font-bold flex items-center gap-2">
              <AgoraLogo size={28} />
              Agora Convo AI Video Agent
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground ml-10">
              React with Agora AI UIKit - Video + Avatar
            </p>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className="rounded-full p-2 hover:bg-accent transition-colors"
              aria-label="Toggle settings"
            >
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 px-4 py-1 md:py-6 min-h-0 overflow-hidden min-w-0">
        {!isConnected ? (
          /* Connection Form - Centered (same as original) */
          <div className="flex flex-1 items-center justify-center">
            {(autoConnect || isLoading) ? (
              <p className="text-lg text-muted-foreground animate-pulse">Connecting...</p>
            ) : (
            <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
              <h2 className="mb-4 text-lg font-semibold">Connect to Agent</h2>
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="backend"
                    className="mb-2 block text-sm font-medium"
                  >
                    Backend URL
                  </label>
                  <input
                    id="backend"
                    type="text"
                    value={backendUrl}
                    onChange={(e) => setBackendUrl(e.target.value)}
                    placeholder={DEFAULT_BACKEND_URL}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>

                <div>
                  <label
                    htmlFor="profile"
                    className="mb-2 block text-sm font-medium"
                  >
                    Server Profile
                  </label>
                  <input
                    id="profile"
                    type="text"
                    value={profile}
                    onChange={(e) => setProfile(e.target.value)}
                    placeholder={DEFAULT_PROFILE}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Leave empty for default &ldquo;{DEFAULT_PROFILE}&rdquo; profile
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableLocalVideo}
                      onChange={(e) => setEnableLocalVideo(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="text-sm font-medium">
                      Enable Local Video
                    </span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableAvatar}
                      onChange={(e) => setEnableAvatar(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="text-sm font-medium">Enable Avatar</span>
                  </label>
                </div>

                <button
                  onClick={handleStart}
                  disabled={isLoading}
                  className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {isLoading ? "Connecting..." : "Start Call"}
                </button>
              </div>
            </div>
            )}
          </div>
        ) : (
          /* Connected: Responsive Layout */
          <>
            {/* Desktop Layout - Hidden on mobile */}
            <VideoGrid
              className="hidden md:grid flex-1 min-w-0"
              style={{ gridTemplateColumns: "2fr 3fr", gridTemplateRows: "1fr 1fr", gap: "1rem" }}
              chat={
                <div className="flex flex-col h-full">
                  {/* Conversation Header */}
                  <div className="border-b p-4 flex-shrink-0 flex items-center justify-between">
                    <h2 className="font-semibold">Conversation</h2>
                    <p className="text-sm text-muted-foreground">
                      {messageList.length} message
                      {messageList.length !== 1 ? "s" : ""}
                    </p>
                  </div>

                  {/* Messages */}
                  <Conversation
                    height=""
                    className="flex-1 min-h-0"
                    style={{ overflow: "auto" }}
                  >
                    <ConversationContent className="gap-3">
                      {messageList.map((msg, idx) => {
                        const isAgent = isAgentMessage(msg.uid);
                        const label = isAgent ? "Agent" : "You";
                        const time = formatTime(msg.timestamp);
                        return (
                          <Message
                            key={`${msg.turn_id}-${msg.uid}-${idx}`}
                            from={isAgent ? "assistant" : "user"}
                            name={time ? `${label}  ${time}` : label}
                          >
                            <MessageContent className={isAgent ? "px-3 py-2" : "px-3 py-2 bg-foreground text-background"}>
                              <Response>{msg.text}</Response>
                            </MessageContent>
                          </Message>
                        );
                      })}

                      {/* In-progress message */}
                      {currentInProgressMessage &&
                        (() => {
                          const isAgent = isAgentMessage(
                            currentInProgressMessage.uid,
                          );
                          const label = isAgent ? "Agent" : "You";
                          const time = formatTime(currentInProgressMessage.timestamp);
                          return (
                            <Message
                              from={isAgent ? "assistant" : "user"}
                              name={time ? `${label}  ${time}` : label}
                            >
                              <MessageContent className={`animate-pulse px-3 py-2 ${isAgent ? "" : "bg-foreground text-background"}`}>
                                <Response>
                                  {currentInProgressMessage.text}
                                </Response>
                              </MessageContent>
                            </Message>
                          );
                        })()}
                    </ConversationContent>
                  </Conversation>

                  {/* Input Box */}
                  <div className="border-t p-4 flex-shrink-0">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type a message"
                        disabled={!isConnected}
                        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={!isConnected || !chatMessage.trim()}
                        className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                      >
                        <SendHorizontal className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              }
              avatar={
                <div className="flex flex-col h-full">
                  {/* Avatar Video + optional Thymia tab */}
                  {THYMIA_ENABLED ? (
                    <MobileTabs
                      tabs={[
                        {
                          id: "avatar",
                          label: "Avatar",
                          content: (
                            <div className="flex-1 flex items-center justify-center bg-muted/20 p-2 h-full">
                              <AvatarVideoDisplay
                                videoTrack={avatarVideoTrack}
                                state={
                                  avatarVideoTrack
                                    ? "connected"
                                    : "disconnected"
                                }
                                className="h-full w-full"
                                useMediaStream={true}
                              />
                            </div>
                          ),
                        },
                        {
                          id: "thymia",
                          label: "Thymia",
                          content: (
                            <ThymiaPanel
                              biomarkers={biomarkers}
                              wellness={wellness}
                              clinical={clinical}
                              progress={thymiaProgress}
                              safety={thymiaSafety}
                              isConnected={isConnected}
                            />
                          ),
                        },
                      ]}
                    />
                  ) : (
                    <div className="flex-1 flex items-center justify-center bg-muted/20 p-2">
                      <AvatarVideoDisplay
                        videoTrack={avatarVideoTrack}
                        state={avatarVideoTrack ? "connected" : "disconnected"}
                        className="h-full w-full"
                        useMediaStream={true}
                      />
                    </div>
                  )}

                  {/* Controls below avatar */}
                  <div className="border-t p-4 flex-shrink-0">
                    <div className="flex gap-3 justify-center">
                      <IconButton
                        shape="square"
                        variant={isMuted ? "standard" : "filled"}
                        size="md"
                        onClick={toggleMute}
                        className={isMuted ? "rounded-lg bg-muted text-destructive hover:bg-muted/80" : "rounded-lg"}
                      >
                        {isMuted ? <MicOff className="size-4" /> : <Mic className="size-4" />}
                      </IconButton>
                      <IconButton
                        shape="square"
                        variant={isLocalVideoActive ? "filled" : "standard"}
                        size="md"
                        onClick={toggleVideo}
                        className={!isLocalVideoActive ? "rounded-lg bg-muted text-destructive hover:bg-muted/80" : "rounded-lg"}
                      >
                        {isLocalVideoActive ? <Video className="size-4" /> : <VideoOff className="size-4" />}
                      </IconButton>
                      <button
                        onClick={handleStop}
                        className="flex items-center gap-2 rounded-lg bg-destructive px-5 py-2.5 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
                      >
                        <PhoneOff className="h-4 w-4" />
                        End Call
                      </button>
                    </div>
                  </div>
                </div>
              }
              localVideo={
                <div className="h-full flex items-center justify-center p-2">
                  <LocalVideoPreview
                    videoTrack={isLocalVideoActive ? localVideoTrack : null}
                    className="h-full w-full"
                    useMediaStream={true}
                  />
                </div>
              }
            />

            {/* Mobile Layout - Hidden on desktop */}
            <div className="flex md:hidden flex-1 flex-col min-h-0 overflow-hidden">
              <MobileTabs
                activeTab={activeTab}
                onTabChange={setActiveTab}
                tabs={[
                  {
                    id: "video",
                    label: "Video",
                    content: (
                      <div className="flex flex-col h-full gap-2 p-2">
                        {/* Avatar - 50% */}
                        <div className="flex-1 rounded-lg border bg-card shadow-lg overflow-hidden">
                          <AvatarVideoDisplay
                            videoTrack={avatarVideoTrack}
                            state={
                              avatarVideoTrack ? "connected" : "disconnected"
                            }
                            className="h-full w-full"
                            useMediaStream={true}
                          />
                        </div>

                        {/* Local Video - 50% */}
                        <div className="flex-1 rounded-lg border bg-card shadow-lg overflow-hidden">
                          <LocalVideoPreview
                            videoTrack={
                              isLocalVideoActive ? localVideoTrack : null
                            }
                            className="h-full w-full"
                            useMediaStream={true}
                          />
                        </div>
                      </div>
                    ),
                  },
                  {
                    id: "chat",
                    label: "Chat",
                    content: (
                      <div className="flex flex-col h-full gap-2 p-2">
                        {/* Avatar - 35% */}
                        <div className="flex-[35] rounded-lg border bg-card shadow-lg overflow-hidden">
                          <AvatarVideoDisplay
                            videoTrack={avatarVideoTrack}
                            state={
                              avatarVideoTrack ? "connected" : "disconnected"
                            }
                            className="h-full w-full"
                            useMediaStream={true}
                          />
                        </div>

                        {/* Chat - 65% */}
                        <div className="flex-[65] rounded-lg border bg-card shadow-lg overflow-hidden flex flex-col">
                          {/* Conversation Header */}
                          <div className="border-b p-3 flex-shrink-0 flex items-center justify-between">
                            <h2 className="font-semibold text-sm">
                              Conversation
                            </h2>
                            <p className="text-xs text-muted-foreground">
                              {messageList.length} message
                              {messageList.length !== 1 ? "s" : ""}
                            </p>
                          </div>

                          {/* Messages */}
                          <Conversation
                            height=""
                            className="flex-1 min-h-0"
                            style={{ overflow: "auto" }}
                          >
                            <ConversationContent className="gap-3">
                              {messageList.map((msg, idx) => {
                                const isAgent = isAgentMessage(msg.uid);
                                const label = isAgent ? "Agent" : "You";
                                const time = formatTime(msg.timestamp);
                                return (
                                  <Message
                                    key={`${msg.turn_id}-${msg.uid}-${idx}`}
                                    from={isAgent ? "assistant" : "user"}
                                    name={time ? `${label}  ${time}` : label}
                                  >
                                    <MessageContent className={isAgent ? "px-3 py-2" : "px-3 py-2 bg-foreground text-background"}>
                                      <Response>{msg.text}</Response>
                                    </MessageContent>
                                  </Message>
                                );
                              })}

                              {/* In-progress message */}
                              {currentInProgressMessage &&
                                (() => {
                                  const isAgent = isAgentMessage(
                                    currentInProgressMessage.uid,
                                  );
                                  const label = isAgent ? "Agent" : "You";
                                  const time = formatTime(currentInProgressMessage.timestamp);
                                  return (
                                    <Message
                                      from={isAgent ? "assistant" : "user"}
                                      name={time ? `${label}  ${time}` : label}
                                    >
                                      <MessageContent className={`animate-pulse px-3 py-2 ${isAgent ? "" : "bg-foreground text-background"}`}>
                                        <Response>
                                          {currentInProgressMessage.text}
                                        </Response>
                                      </MessageContent>
                                    </Message>
                                  );
                                })()}
                            </ConversationContent>
                          </Conversation>

                          {/* Input Box */}
                          <div className="border-t p-2 flex-shrink-0">
                            <div className="flex gap-2">
                              <input
                                type="text"
                                value={chatMessage}
                                onChange={(e) => setChatMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Type a message"
                                disabled={!isConnected}
                                className="flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                              />
                              <button
                                onClick={handleSendMessage}
                                disabled={!isConnected || !chatMessage.trim()}
                                className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                              >
                                <SendHorizontal className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ),
                  },
                  ...(THYMIA_ENABLED
                    ? [
                        {
                          id: "thymia",
                          label: "Thymia",
                          content: (
                            <ThymiaPanel
                              biomarkers={biomarkers}
                              wellness={wellness}
                              clinical={clinical}
                              progress={thymiaProgress}
                              safety={thymiaSafety}
                              isConnected={isConnected}
                            />
                          ),
                        },
                      ]
                    : []),
                ]}
              />

              {/* Mobile: Fixed Bottom Controls */}
              <div className="flex gap-3 p-2 border-t bg-card flex-shrink-0 justify-center">
                <IconButton
                  shape="square"
                  variant={isMuted ? "standard" : "filled"}
                  size="md"
                  onClick={toggleMute}
                  className={isMuted ? "rounded-lg bg-muted text-destructive hover:bg-muted/80" : "rounded-lg"}
                >
                  {isMuted ? <MicOff className="size-4" /> : <Mic className="size-4" />}
                </IconButton>
                <IconButton
                  shape="square"
                  variant={isLocalVideoActive ? "filled" : "standard"}
                  size="md"
                  onClick={toggleVideo}
                  className={!isLocalVideoActive ? "rounded-lg bg-muted text-destructive hover:bg-muted/80" : "rounded-lg"}
                >
                  {isLocalVideoActive ? <Video className="size-4" /> : <VideoOff className="size-4" />}
                </IconButton>
                <button
                  onClick={handleStop}
                  className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 min-h-[44px]"
                >
                  <PhoneOff className="h-4 w-4" />
                  End Call
                </button>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Settings Dialog */}
      <SettingsDialog
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
        enableAivad={enableAivad}
        onEnableAivadChange={setEnableAivad}
        language={language}
        onLanguageChange={setLanguage}
        prompt={prompt}
        onPromptChange={setPrompt}
        greeting={greeting}
        onGreetingChange={setGreeting}
        disabled={isConnected}
      >
        {isConnected && (
          <SessionPanel agentId={sessionAgentId} payload={sessionPayload} />
        )}
      </SettingsDialog>
    </div>
  );
}
