"use client"

import { useState, useRef } from "react"
import { Mic, MicOff } from "lucide-react"
import { useAgoraVoiceClient } from "@/hooks/useAgoraVoiceClient"
import { useAudioVisualization } from "@/hooks/useAudioVisualization"
import { MicButton } from "@agora/agent-ui-kit"
import { AgentVisualizer, AgentVisualizerState } from "@agora/agent-ui-kit"
import { Conversation, ConversationContent } from "@agora/agent-ui-kit"
import { Message, MessageContent } from "@agora/agent-ui-kit"
import { Response } from "@agora/agent-ui-kit"
import { AgoraLogo } from "@agora/agent-ui-kit"
import { cn } from "@/lib/utils"

const DEFAULT_BACKEND_URL = "http://localhost:8082"

export function VoiceClient() {
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL)
  const [agentUID, setAgentUID] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [chatMessage, setChatMessage] = useState("")
  const conversationRef = useRef<HTMLDivElement>(null)

  const {
    isConnected,
    isMuted,
    micState,
    messageList,
    currentInProgressMessage,
    isAgentSpeaking,
    localAudioTrack,
    joinChannel,
    leaveChannel,
    toggleMute,
    sendMessage,
  } = useAgoraVoiceClient()

  // Get audio visualization data (restart on mute/unmute to fix Web Audio API connection)
  const frequencyData = useAudioVisualization(localAudioTrack, isConnected && !isMuted)

  const handleStart = async () => {
    setIsLoading(true)
    try {
      // Backend will auto-generate random channel if not provided
      const response = await fetch(`${backendUrl}/start-agent`)

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
    } catch (error) {
      console.error("Failed to start:", error)
      alert(`Failed to start: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStop = async () => {
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

  const getAgentState = (): AgentVisualizerState => {
    const state = !isConnected ? "not-joined" : isAgentSpeaking ? "talking" : "listening"
    return state
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
            Voice AI Client
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground hidden md:block">
            React with Agora AI UIKit
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto flex flex-1 px-4 py-6 min-h-0 overflow-hidden">
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
          /* Responsive Layout: Mobile (column) / Desktop (two-column) */
          <div className="flex flex-1 flex-col gap-4 min-h-0 overflow-hidden md:flex-row md:gap-6">
            {/* Mobile: Compact Agent Status Bar (shown on top) */}
            <div className="flex items-center justify-center rounded-lg border bg-card p-3 shadow-lg md:hidden">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "h-3 w-3 rounded-full",
                    isAgentSpeaking ? "bg-green-500 animate-pulse" : "bg-blue-500"
                  )}
                />
                <span className="text-sm font-medium">
                  {isAgentSpeaking ? "Agent Speaking" : "Listening"}
                </span>
              </div>
            </div>

            {/* Desktop: Left Column (visualizer, controls, status) */}
            <div className="hidden md:flex md:w-96 flex-col gap-6 self-stretch">
              {/* Agent Visualizer */}
              <div className="rounded-lg border bg-card p-6 shadow-lg flex-shrink">
                <AgentVisualizer state={getAgentState()} size="sm" />
                <p className="mt-2 text-xs text-center text-muted-foreground">
                  State: {getAgentState()}
                </p>
              </div>

              {/* Controls */}
              <div className="rounded-lg border bg-card p-6 shadow-lg">
                <div className="flex gap-3">
                  <MicButton
                    state={micState}
                    icon={isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                    audioData={frequencyData}
                    onClick={toggleMute}
                    className="flex-1"
                  />
                  <button
                    onClick={handleStop}
                    className="flex-1 rounded-lg border border-destructive bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/20"
                  >
                    End Call
                  </button>
                </div>
              </div>

              {/* Status */}
              <div className="rounded-lg border bg-card p-4 shadow-lg flex-1 flex flex-col justify-center">
                <div className="space-y-2 text-sm">
                  {agentUID && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Agent:</span>
                      <span className="font-mono font-medium">{agentUID}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Mic:</span>
                    <span className="font-mono font-medium">{isMuted ? "Muted" : "Active"}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Conversation */}
            <div
              ref={conversationRef}
              className="flex flex-1 flex-col rounded-lg border bg-card shadow-lg min-h-0 overflow-hidden"
            >
              {/* Conversation Header */}
              <div className="border-b p-4 flex-shrink-0">
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
              <div className="border-t p-3 md:p-4 flex-shrink-0">
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

            {/* Mobile: Fixed Bottom Controls */}
            <div className="flex md:hidden gap-3 p-4 border-t bg-card">
              <MicButton
                state={micState}
                icon={isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                audioData={frequencyData}
                onClick={toggleMute}
                className="flex-1 min-h-[48px]"
              />
              <button
                onClick={handleStop}
                className="flex-1 rounded-lg border border-destructive bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive hover:bg-destructive/20 min-h-[48px]"
              >
                End Call
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
