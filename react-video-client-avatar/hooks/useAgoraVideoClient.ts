/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { IMicrophoneAudioTrack } from "agora-rtc-sdk-ng";
import { RTCHelper } from "@agora/conversational-ai/helper/rtc";
import { SubRenderController } from "@agora/conversational-ai/utils/sub-render";
import { ConversationalAIAPI } from "@agora/conversational-ai";
import type {
  TranscriptItem,
  TranscriptHelperMode,
} from "@agora/conversational-ai/type";
import { TurnStatus, RTCHelperEvents } from "@agora/conversational-ai/type";
import { MicButtonState } from "@agora/agent-ui-kit";

export type VoiceClientConfig = {
  appId: string;
  channel: string;
  token: string | null;
  uid: number;
  microphoneId?: string;
};

export interface IMessageListItem {
  turn_id: number;
  uid: number;
  text: string;
  status: number;
  timestamp?: number;
}

export function useAgoraVideoClient() {
  const [localAudioTrack, setLocalAudioTrack] =
    useState<IMicrophoneAudioTrack | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [micState, setMicState] = useState<MicButtonState>("idle");
  const [messageList, setMessageList] = useState<IMessageListItem[]>([]);
  const [currentInProgressMessage, setCurrentInProgressMessage] =
    useState<IMessageListItem | null>(null);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [remoteAudioTrack, setRemoteAudioTrack] = useState<any>(null);
  const [remoteVideoTrack, setRemoteVideoTrack] = useState<any>(null);

  const rtcHelperRef = useRef<RTCHelper | null>(null);
  const apiRef = useRef<ConversationalAIAPI | null>(null);
  const volumeCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Setup RTC event listeners for both audio and video
  useEffect(() => {
    const rtcHelper = rtcHelperRef.current;
    if (!rtcHelper) return;

    const handleUserPublished = (user: any, mediaType: "audio" | "video") => {
      console.log(`🎥 VIDEO_DEBUG RTCHelper user-published:`, {
        uid: user.uid,
        mediaType,
        hasAudioTrack: !!(user as any).audioTrack,
        hasVideoTrack: !!(user as any).videoTrack,
      });

      if (mediaType === "audio") {
        console.log(`🎥 VIDEO_DEBUG Audio published by user ${user.uid}`);
        setRemoteAudioTrack((user as any).audioTrack);
        setIsAgentSpeaking(true);
      } else if (mediaType === "video") {
        console.log(`🎥 VIDEO_DEBUG Video published by user ${user.uid}`);
        setRemoteVideoTrack((user as any).videoTrack);
      }
    };

    const handleUserUnpublished = (user: any, mediaType: "audio" | "video") => {
      console.log(`🎥 VIDEO_DEBUG RTCHelper user-unpublished:`, {
        uid: user.uid,
        mediaType,
      });

      if (mediaType === "audio") {
        setIsAgentSpeaking(false);
        setRemoteAudioTrack(null);
      } else if (mediaType === "video") {
        setRemoteVideoTrack(null);
      }
    };

    const handleUserLeft = (user: any) => {
      console.log(`🎥 VIDEO_DEBUG User left:`, user.uid);
      setIsAgentSpeaking(false);
      setRemoteAudioTrack(null);
      setRemoteVideoTrack(null);
    };

    // Listen to RTCHelper events - it now handles both audio and video
    rtcHelper.on(RTCHelperEvents.USER_PUBLISHED, handleUserPublished);
    rtcHelper.on(RTCHelperEvents.USER_UNPUBLISHED, handleUserUnpublished);
    rtcHelper.on(RTCHelperEvents.USER_LEFT, handleUserLeft);

    return () => {
      rtcHelper.off(RTCHelperEvents.USER_PUBLISHED, handleUserPublished);
      rtcHelper.off(RTCHelperEvents.USER_UNPUBLISHED, handleUserUnpublished);
      rtcHelper.off(RTCHelperEvents.USER_LEFT, handleUserLeft);
    };
  }, [rtcHelperRef.current]);

  // Monitor remote audio volume levels
  useEffect(() => {
    if (!remoteAudioTrack) {
      if (volumeCheckIntervalRef.current) {
        clearInterval(volumeCheckIntervalRef.current);
        volumeCheckIntervalRef.current = null;
      }
      return;
    }

    const volumes: number[] = [];
    volumeCheckIntervalRef.current = setInterval(() => {
      if (
        remoteAudioTrack &&
        typeof remoteAudioTrack.getVolumeLevel === "function"
      ) {
        const volume = remoteAudioTrack.getVolumeLevel();
        volumes.push(volume);
        if (volumes.length > 3) volumes.shift();

        const isAllZero = volumes.length >= 2 && volumes.every((v) => v === 0);
        const hasSound = volumes.length >= 2 && volumes.some((v) => v > 0);

        if (isAllZero && isAgentSpeaking) {
          setIsAgentSpeaking(false);
        } else if (hasSound && !isAgentSpeaking) {
          setIsAgentSpeaking(true);
        }
      }
    }, 100);

    return () => {
      if (volumeCheckIntervalRef.current) {
        clearInterval(volumeCheckIntervalRef.current);
        volumeCheckIntervalRef.current = null;
      }
    };
  }, [remoteAudioTrack, isAgentSpeaking]);

  const joinChannel = useCallback(
    async (config: VoiceClientConfig) => {
      if (isConnected) {
        // eslint-disable-next-line react-hooks/immutability
        await leaveChannel();
      }

      try {
        // Initialize RTCHelper
        const rtcHelper = RTCHelper.getInstance();
        await rtcHelper.init({
          appId: config.appId,
          channel: config.channel,
          token: config.token,
          uid: config.uid,
        });

        // Create and publish audio track
        const audioTrack = await rtcHelper.createAudioTrack({
          encoderConfig: "high_quality_stereo",
          AEC: true,
          ANS: true,
          AGC: true,
          ...(config.microphoneId ? { microphoneId: config.microphoneId } : {}),
        });

        await rtcHelper.join();
        await rtcHelper.publish();

        setLocalAudioTrack(audioTrack);
        setIsConnected(true);
        setMicState("listening");
        rtcHelperRef.current = rtcHelper;

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
        });

        // Listen to transcript updates
        api.on("transcript-updated" as any, (messages: TranscriptItem[]) => {
          // Convert to IMessageListItem format
          const convertedMessages = messages.map((m) => ({
            turn_id: m.turn_id,
            uid: m.uid,
            text: m.text,
            status: m.status,
            timestamp: m.timestamp,
          }));

          // Filter out in-progress messages
          const completedMessages = convertedMessages.filter(
            (msg) => msg.status !== TurnStatus.IN_PROGRESS,
          );

          const inProgress = convertedMessages.find(
            (msg) => msg.status === TurnStatus.IN_PROGRESS,
          );

          // Log only when NEW agent messages arrive (not on every re-render)
          const agentMessages = messages.filter(
            (m) => m.uid === 0 && m.status === 0,
          ); // IN_PROGRESS
          if (agentMessages.length > 0) {
            agentMessages.forEach((m) => {
              console.log(
                `💬 AGENT MSG turn_id=${m.turn_id} text="${m.text}" (${m.text?.length || 0} chars) status=${m.status}`,
              );
            });
          }

          setMessageList(completedMessages);
          setCurrentInProgressMessage(inProgress || null);
        });

        apiRef.current = api;
      } catch (error) {
        console.error("Error joining channel:", error);
        throw error;
      }
    },
    [isConnected],
  );

  const leaveChannel = useCallback(async () => {
    try {
      // Cleanup API
      if (apiRef.current) {
        apiRef.current.destroy();
        apiRef.current = null;
      }

      // Cleanup RTCHelper
      if (rtcHelperRef.current) {
        await rtcHelperRef.current.leave();
        rtcHelperRef.current = null;
      }

      setLocalAudioTrack(null);
      setIsConnected(false);
      setMicState("idle");
      setIsAgentSpeaking(false);
      setMessageList([]);
      setCurrentInProgressMessage(null);
      setRemoteVideoTrack(null);
    } catch (error) {
      console.error("Error leaving channel:", error);
    }
  }, []);

  const toggleMute = useCallback(async () => {
    const rtcHelper = rtcHelperRef.current;
    if (!rtcHelper) return;

    try {
      await rtcHelper.setMuted(!isMuted);
      setIsMuted(!isMuted);
      setMicState(!isMuted ? "idle" : "listening");
    } catch (error) {
      console.error("Error toggling mute:", error);
    }
  }, [isMuted]);

  const sendMessage = useCallback(
    async (message: string, agentUid: string = "100") => {
      const api = apiRef.current;
      if (!api) {
        console.error("Cannot send message: API not initialized");
        return false;
      }

      try {
        await api.sendMessage(message, agentUid, "APPEND");
        return true;
      } catch (error) {
        console.error("Error sending message:", error);
        return false;
      }
    },
    [],
  );

  return {
    isConnected,
    isMuted,
    micState,
    messageList,
    currentInProgressMessage,
    isAgentSpeaking,
    localAudioTrack,
    remoteVideoTrack,
    joinChannel,
    leaveChannel,
    toggleMute,
    sendMessage,
    rtcHelperRef,
  };
}
