"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { IMicrophoneAudioTrack } from "agora-rtc-sdk-ng"
import { RTCHelper } from "@agora/conversational-ai/helper/rtc"
import { SubRenderController } from "@agora/conversational-ai/utils/sub-render"
import { ConversationalAIAPI } from "@agora/conversational-ai"
import type { TranscriptItem, TranscriptHelperMode } from "@agora/conversational-ai/type"
import { TurnStatus, RTCHelperEvents } from "@agora/conversational-ai/type"
import { MicButtonState } from "@agora/agent-ui-kit"

export type VoiceClientConfig = {
  appId: string
  channel: string
  token: string | null
  uid: number
}

export interface IMessageListItem {
  turn_id: number
  uid: number
  text: string
  status: number
  timestamp?: number
}

export function useAgoraVoiceClient() {
  const [localAudioTrack, setLocalAudioTrack] = useState<IMicrophoneAudioTrack | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [micState, setMicState] = useState<MicButtonState>("idle")
  const [messageList, setMessageList] = useState<IMessageListItem[]>([])
  const [currentInProgressMessage, setCurrentInProgressMessage] = useState<IMessageListItem | null>(
    null
  )
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false)
  const [remoteAudioTrack, setRemoteAudioTrack] = useState<any>(null)

  const rtcHelperRef = useRef<RTCHelper | null>(null)
  const apiRef = useRef<ConversationalAIAPI | null>(null)
  const volumeCheckIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Setup RTC event listeners
  useEffect(() => {
    const rtcHelper = rtcHelperRef.current
    if (!rtcHelper) return

    const handleUserPublished = (user: any, mediaType: "audio" | "video") => {
      if (mediaType === "audio" && user.audioTrack) {
        user.audioTrack.play()
        setRemoteAudioTrack(user.audioTrack)
        setIsAgentSpeaking(true)
      }
    }

    const handleUserUnpublished = (user: any, mediaType: "audio" | "video") => {
      if (mediaType === "audio") {
        setIsAgentSpeaking(false)
        setRemoteAudioTrack(null)
      }
    }

    const handleUserLeft = (user: any) => {
      setIsAgentSpeaking(false)
      setRemoteAudioTrack(null)
    }

    rtcHelper.on(RTCHelperEvents.USER_PUBLISHED, handleUserPublished)
    rtcHelper.on(RTCHelperEvents.USER_UNPUBLISHED, handleUserUnpublished)
    rtcHelper.on(RTCHelperEvents.USER_LEFT, handleUserLeft)

    return () => {
      rtcHelper.off(RTCHelperEvents.USER_PUBLISHED, handleUserPublished)
      rtcHelper.off(RTCHelperEvents.USER_UNPUBLISHED, handleUserUnpublished)
      rtcHelper.off(RTCHelperEvents.USER_LEFT, handleUserLeft)
    }
  }, [rtcHelperRef.current])

  // Monitor remote audio volume levels
  useEffect(() => {
    if (!remoteAudioTrack) {
      if (volumeCheckIntervalRef.current) {
        clearInterval(volumeCheckIntervalRef.current)
        volumeCheckIntervalRef.current = null
      }
      return
    }

    const volumes: number[] = []
    volumeCheckIntervalRef.current = setInterval(() => {
      if (remoteAudioTrack && typeof remoteAudioTrack.getVolumeLevel === "function") {
        const volume = remoteAudioTrack.getVolumeLevel()
        volumes.push(volume)
        if (volumes.length > 3) volumes.shift()

        const isAllZero = volumes.length >= 2 && volumes.every((v) => v === 0)
        const hasSound = volumes.length >= 2 && volumes.some((v) => v > 0)

        if (isAllZero && isAgentSpeaking) {
          setIsAgentSpeaking(false)
        } else if (hasSound && !isAgentSpeaking) {
          setIsAgentSpeaking(true)
        }
      }
    }, 100)

    return () => {
      if (volumeCheckIntervalRef.current) {
        clearInterval(volumeCheckIntervalRef.current)
        volumeCheckIntervalRef.current = null
      }
    }
  }, [remoteAudioTrack, isAgentSpeaking])

  const joinChannel = useCallback(
    async (config: VoiceClientConfig) => {
      if (isConnected) {
        await leaveChannel()
      }

      try {
        // Initialize RTCHelper
        const rtcHelper = RTCHelper.getInstance()
        await rtcHelper.init({
          appId: config.appId,
          channel: config.channel,
          token: config.token,
          uid: config.uid,
        })

        // Create and publish audio track
        const audioTrack = await rtcHelper.createAudioTrack({
          encoderConfig: "high_quality_stereo",
          AEC: true,
          ANS: true,
          AGC: true,
        })

        await rtcHelper.join()
        await rtcHelper.publish()

        setLocalAudioTrack(audioTrack)
        setIsConnected(true)
        setMicState("listening")
        rtcHelperRef.current = rtcHelper

        // Initialize ConversationalAIAPI with SubRenderController and RTM
        const api = ConversationalAIAPI.init({
          rtcEngine: rtcHelper.client!,
          rtmConfig: {
            appId: config.appId,
            uid: `${config.uid}`, // RTM uid must be string
            token: config.token,
            channel: config.channel,
          },
          renderMode: "auto" as TranscriptHelperMode,
          enableLog: true,
        })

        // Listen to transcript updates
        api.on("transcript-updated" as any, (messages: TranscriptItem[]) => {
          // Convert to IMessageListItem format
          const convertedMessages = messages.map((m) => ({
            turn_id: m.turn_id,
            uid: m.uid,
            text: m.text,
            status: m.status,
            timestamp: m.timestamp,
          }))

          // Filter out in-progress messages
          const completedMessages = convertedMessages.filter(
            (msg) => msg.status !== TurnStatus.IN_PROGRESS
          )

          const inProgress = convertedMessages.find((msg) => msg.status === TurnStatus.IN_PROGRESS)

          setMessageList(completedMessages)
          setCurrentInProgressMessage(inProgress || null)
        })

        apiRef.current = api
      } catch (error) {
        console.error("Error joining channel:", error)
        throw error
      }
    },
    [isConnected]
  )

  const leaveChannel = useCallback(async () => {
    try {
      // Cleanup API
      if (apiRef.current) {
        apiRef.current.destroy()
        apiRef.current = null
      }

      // Cleanup RTCHelper
      if (rtcHelperRef.current) {
        await rtcHelperRef.current.leave()
        rtcHelperRef.current = null
      }

      setLocalAudioTrack(null)
      setIsConnected(false)
      setMicState("idle")
      setIsAgentSpeaking(false)
      setMessageList([])
      setCurrentInProgressMessage(null)
    } catch (error) {
      console.error("Error leaving channel:", error)
    }
  }, [])

  const toggleMute = useCallback(async () => {
    const rtcHelper = rtcHelperRef.current
    if (!rtcHelper) return

    try {
      await rtcHelper.setMuted(!isMuted)
      setIsMuted(!isMuted)
      setMicState(!isMuted ? "idle" : "listening")
    } catch (error) {
      console.error("Error toggling mute:", error)
    }
  }, [isMuted])

  const sendMessage = useCallback(async (message: string, agentUid: string = "100") => {
    const api = apiRef.current
    if (!api) {
      console.error("Cannot send message: API not initialized")
      return false
    }

    try {
      await api.sendMessage(message, agentUid, "APPEND")
      return true
    } catch (error) {
      console.error("Error sending message:", error)
      return false
    }
  }, [])

  return {
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
  }
}
