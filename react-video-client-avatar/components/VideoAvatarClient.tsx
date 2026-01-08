"use client"

import { useState, useRef, useEffect } from "react"
import { Mic, MicOff, Video, VideoOff } from "lucide-react"
import { useAgoraVoiceClient } from "@/hooks/useAgoraVoiceClient"
import { useAudioVisualization } from "@/hooks/useAudioVisualization"
import { useLocalVideo, useRemoteVideo } from "@agora/conversational-ai-react"
import { MicButton } from "@agora/agent-ui-kit"
import { Conversation, ConversationContent } from "@agora/agent-ui-kit"
import { Message, MessageContent } from "@agora/agent-ui-kit"
import { Response } from "@agora/agent-ui-kit"
import { AvatarVideoDisplay, LocalVideoPreview } from "@agora/agent-ui-kit"
import { VideoGrid, MobileTabs } from "@agora/agent-ui-kit"
import { AgoraLogo } from "@agora/agent-ui-kit"
import { cn } from "@/lib/utils"

const DEFAULT_BACKEND_URL = "http://localhost:8082"

export function VideoAvatarClient() {
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL)
  const [agentUID, setAgentUID] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [chatMessage, setChatMessage] = useState("")
  const [enableLocalVideo, setEnableLocalVideo] = useState(true)
  const [enableAvatar, setEnableAvatar] = useState(true)
  const [activeTab, setActiveTab] = useState("video")
  const _conversationRef = useRef<HTMLDivElement>(null)

  const {
    isConnected,
    isMuted,
    micState,
    messageList,
    currentInProgressMessage,
    isAgentSpeaking: _isAgentSpeaking,
    localAudioTrack,
    joinChannel,
    leaveChannel,
    toggleMute,
    sendMessage,
    rtcHelperRef,
  } = useAgoraVoiceClient()

  // Get audio visualization data (restart on mute/unmute to fix Web Audio API connection)
  const frequencyData = useAudioVisualization(localAudioTrack, isConnected && !isMuted)

  // Video hooks
  const {
    videoTrack: localVideoTrack,
    isVideoEnabled: isLocalVideoActive,
    enableVideo,
    disableVideo,
  } = useLocalVideo()

  const { remoteVideoUsersArray } = useRemoteVideo({
    client: rtcHelperRef.current?.client,
  })

  // Get avatar video track (first remote user with video)
  const avatarVideoTrack =
    remoteVideoUsersArray.length > 0 ? remoteVideoUsersArray[0].videoTrack : null

  // Publish local video track to channel when it becomes available
  useEffect(() => {
    const publishVideo = async () => {
      const client = rtcHelperRef.current?.client
      if (!client || !localVideoTrack || !isConnected || !isLocalVideoActive) return

      try {
        await client.publish(localVideoTrack)
        console.log("[VideoAvatarClient] Published local video track")
      } catch (error) {
        console.error("[VideoAvatarClient] Failed to publish video:", error)
      }
    }

    publishVideo()

    // Unpublish on cleanup (if still connected)
    return () => {
      const client = rtcHelperRef.current?.client
      if (client && localVideoTrack && isConnected) {
        client.unpublish(localVideoTrack).catch((err) => {
          // Ignore error if already disconnected
          if (!err.message?.includes("haven't joined")) {
            console.error("[VideoAvatarClient] Failed to unpublish video:", err)
          }
        })
      }
    }
  }, [localVideoTrack, isConnected, isLocalVideoActive])

  const handleStart = async () => {
    setIsLoading(true)
    try {
      // Build query params for backend
      const params = new URLSearchParams()

      // Use avatar profile for separate avatar config
      params.append("profile", "avatar")

      if (enableAvatar) {
        params.append("avatar_enabled", "true")
        params.append("avatar_vendor", "anam")
      }

      const url = params.toString()
        ? `${backendUrl}/start-agent?${params.toString()}`
        : `${backendUrl}/start-agent`

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.agent?.uid) {
        setAgentUID(data.agent.uid)
      }

      await joinChannel({
        appId: data.appid,
        channel: data.channel,
        token: data.token || null,
        uid: parseInt(data.uid),
      })

      // Auto-enable local video if checkbox was checked
      if (enableLocalVideo) {
        console.log("[VideoAvatarClient] Auto-enabling local video after channel join")
        await enableVideo()
        console.log("[VideoAvatarClient] enableVideo() completed")
      }
    } catch (error) {
      console.error("Failed to start:", error)
      alert(`Failed to start: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStop = async () => {
    if (isLocalVideoActive) {
      await disableVideo()
    }
    await leaveChannel()
  }

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || !isConnected) return

    const success = await sendMessage(chatMessage, agentUID || "100")
    if (success) {
      setChatMessage("")
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleVideo = async () => {
    if (isLocalVideoActive) {
      await disableVideo()
    } else {
      await enableVideo()
    }
  }

  // Helper to determine if message is from agent
  // Agent messages have uid: 0 (stream_id: 0)
  const isAgentMessage = (uid: number) => {
    return uid === 0
  }

  return (
    <div className="flex h-screen flex-col bg-gradient-to-b from-background to-muted overflow-hidden">
      {/* Header - Responsive */}
      <header className="border-b bg-card/50 backdrop-blur-sm flex-shrink-0">
        <div className="container mx-auto px-4 py-3 md:py-4">
          <h1 className="text-lg md:text-2xl font-bold flex items-center gap-2">
            <AgoraLogo size={24} />
            Video Avatar AI Client
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground hidden md:block">
            React with Agora AI UIKit - Video + Avatar
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto flex flex-1 px-4 py-1 md:py-6 min-h-0 overflow-hidden">
        {!isConnected ? (
          /* Connection Form - Centered */
          <div className="flex flex-1 items-center justify-center">
            <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
              <h2 className="mb-4 text-lg font-semibold">Connect to Agent</h2>
              <div className="space-y-4">
                <div>
                  <label htmlFor="backend" className="mb-2 block text-sm font-medium">
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

                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableLocalVideo}
                      onChange={(e) => setEnableLocalVideo(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="text-sm font-medium">Enable Local Video</span>
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
                  {isLoading ? "Connecting..." : "Start Conversation"}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Responsive Layout: Desktop (VideoGrid) / Mobile (Tabs) */
          <>
            {/* Desktop Layout - Hidden on mobile */}
            <VideoGrid
              className="hidden md:grid flex-1"
              chat={
                <div className="flex flex-col h-full">
                  {/* Conversation Header */}
                  <div className="border-b p-4 flex-shrink-0 flex items-center justify-between">
                    <h2 className="font-semibold">Conversation</h2>
                    <p className="text-sm text-muted-foreground">
                      {messageList.length} message{messageList.length !== 1 ? "s" : ""}
                    </p>
                  </div>

                  {/* Messages */}
                  <Conversation height="" className="flex-1 min-h-0" style={{ overflow: "scroll" }}>
                    <ConversationContent>
                      {messageList.map((msg, idx) => {
                        const isAgent = isAgentMessage(msg.uid)
                        return (
                          <Message
                            key={`${msg.turn_id}-${msg.uid}-${idx}`}
                            from={isAgent ? "assistant" : "user"}
                            name={isAgent ? "Agent" : "User"}
                          >
                            <MessageContent>
                              <Response>{msg.text}</Response>
                            </MessageContent>
                          </Message>
                        )
                      })}

                      {/* In-progress message */}
                      {currentInProgressMessage &&
                        (() => {
                          const isAgent = isAgentMessage(currentInProgressMessage.uid)
                          return (
                            <Message
                              from={isAgent ? "assistant" : "user"}
                              name={isAgent ? "Agent" : "User"}
                            >
                              <MessageContent className="animate-pulse">
                                <Response>{currentInProgressMessage.text}</Response>
                              </MessageContent>
                            </Message>
                          )
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
                        placeholder="Type a message..."
                        disabled={!isConnected}
                        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={!isConnected || !chatMessage.trim()}
                        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                      >
                        Send
                      </button>
                    </div>
                  </div>
                </div>
              }
              avatar={
                <div className="flex flex-col h-full">
                  {/* Avatar Video */}
                  <div className="flex-1 flex items-center justify-center bg-muted/20 p-2">
                    <AvatarVideoDisplay
                      videoTrack={avatarVideoTrack}
                      state={avatarVideoTrack ? "connected" : "disconnected"}
                      className="h-full w-full"
                      useMediaStream={true}
                    />
                  </div>

                  {/* Controls below avatar */}
                  <div className="border-t p-4 flex-shrink-0">
                    <div className="flex gap-3">
                      <MicButton
                        state={micState}
                        icon={
                          isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />
                        }
                        audioData={frequencyData}
                        onClick={toggleMute}
                        className="flex-1"
                      />
                      <button
                        onClick={toggleVideo}
                        className={cn(
                          "flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
                          isLocalVideoActive
                            ? "border-primary bg-primary text-primary-foreground hover:bg-primary/90"
                            : "border-input bg-background hover:bg-accent hover:text-accent-foreground"
                        )}
                      >
                        {isLocalVideoActive ? (
                          <Video className="h-4 w-4 inline mr-2" />
                        ) : (
                          <VideoOff className="h-4 w-4 inline mr-2" />
                        )}
                        Camera
                      </button>
                      <button
                        onClick={handleStop}
                        className="flex-1 rounded-lg border border-destructive bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/20"
                      >
                        End Call
                      </button>
                    </div>
                  </div>
                </div>
              }
              localVideo={
                <div className="h-full flex items-center justify-center p-2">
                  <LocalVideoPreview
                    videoTrack={localVideoTrack}
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
                            state={avatarVideoTrack ? "connected" : "disconnected"}
                            className="h-full w-full"
                            useMediaStream={true}
                          />
                        </div>

                        {/* Local Video - 50% */}
                        <div className="flex-1 rounded-lg border bg-card shadow-lg overflow-hidden">
                          <LocalVideoPreview
                            videoTrack={localVideoTrack}
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
                            state={avatarVideoTrack ? "connected" : "disconnected"}
                            className="h-full w-full"
                            useMediaStream={true}
                          />
                        </div>

                        {/* Chat - 65% */}
                        <div className="flex-[65] rounded-lg border bg-card shadow-lg overflow-hidden flex flex-col">
                          {/* Conversation Header */}
                          <div className="border-b p-3 flex-shrink-0 flex items-center justify-between">
                            <h2 className="font-semibold text-sm">Conversation</h2>
                            <p className="text-xs text-muted-foreground">
                              {messageList.length} message{messageList.length !== 1 ? "s" : ""}
                            </p>
                          </div>

                          {/* Messages */}
                          <Conversation
                            height=""
                            className="flex-1 min-h-0"
                            style={{ overflow: "scroll" }}
                          >
                            <ConversationContent>
                              {messageList.map((msg, idx) => {
                                const isAgent = isAgentMessage(msg.uid)
                                return (
                                  <Message
                                    key={`${msg.turn_id}-${msg.uid}-${idx}`}
                                    from={isAgent ? "assistant" : "user"}
                                    name={isAgent ? "Agent" : "User"}
                                  >
                                    <MessageContent>
                                      <Response>{msg.text}</Response>
                                    </MessageContent>
                                  </Message>
                                )
                              })}

                              {/* In-progress message */}
                              {currentInProgressMessage &&
                                (() => {
                                  const isAgent = isAgentMessage(currentInProgressMessage.uid)
                                  return (
                                    <Message
                                      from={isAgent ? "assistant" : "user"}
                                      name={isAgent ? "Agent" : "User"}
                                    >
                                      <MessageContent className="animate-pulse">
                                        <Response>{currentInProgressMessage.text}</Response>
                                      </MessageContent>
                                    </Message>
                                  )
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
                                placeholder="Type a message..."
                                disabled={!isConnected}
                                className="flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                              />
                              <button
                                onClick={handleSendMessage}
                                disabled={!isConnected || !chatMessage.trim()}
                                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                              >
                                Send
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ),
                  },
                ]}
              />

              {/* Mobile: Fixed Bottom Controls */}
              <div className="flex gap-2 p-2 border-t bg-card flex-shrink-0">
                <MicButton
                  state={micState}
                  icon={isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  audioData={frequencyData}
                  onClick={toggleMute}
                  className="flex-1 min-h-[44px]"
                />
                <button
                  onClick={toggleVideo}
                  className={cn(
                    "flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors min-h-[44px]",
                    isLocalVideoActive
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-background"
                  )}
                >
                  {isLocalVideoActive ? (
                    <Video className="h-4 w-4 inline mr-2" />
                  ) : (
                    <VideoOff className="h-4 w-4 inline mr-2" />
                  )}
                  Camera
                </button>
                <button
                  onClick={handleStop}
                  className="flex-1 rounded-lg border border-destructive bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive hover:bg-destructive/20 min-h-[44px]"
                >
                  End Call
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
