"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import AgoraRTC, {
  IAgoraRTCClient,
  IMicrophoneAudioTrack,
  IRemoteAudioTrack,
  IAgoraRTCRemoteUser,
} from "agora-rtc-sdk-ng";
import AgoraRTM, { RTMClient } from "agora-rtm";
import {
  AgoraVoiceAI,
  AgoraVoiceAIEvents,
  TurnStatus,
  ChatMessageType,
  ChatMessagePriority,
  TranscriptHelperMode,
} from "agora-agent-client-toolkit";
import type { TranscriptHelperItem } from "agora-agent-client-toolkit";
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

export function useAgoraVoiceClient() {
  const [localAudioTrack, setLocalAudioTrack] =
    useState<IMicrophoneAudioTrack | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [micState, setMicState] = useState<MicButtonState>("idle");
  const [messageList, setMessageList] = useState<IMessageListItem[]>([]);
  const [currentInProgressMessage, setCurrentInProgressMessage] =
    useState<IMessageListItem | null>(null);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [remoteAudioTrack, setRemoteAudioTrack] =
    useState<IRemoteAudioTrack | null>(null);

  const rtcClientRef = useRef<IAgoraRTCClient | null>(null);
  const rtmClientRef = useRef<RTMClient | null>(null);
  const aiRef = useRef<AgoraVoiceAI | null>(null);
  const localAudioTrackRef = useRef<IMicrophoneAudioTrack | null>(null);
  const volumeCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Setup RTC event listeners
  useEffect(() => {
    const rtcClient = rtcClientRef.current;
    if (!rtcClient) return;

    const handleUserPublished = async (
      user: IAgoraRTCRemoteUser,
      mediaType: "audio" | "video",
    ) => {
      if (mediaType === "audio") {
        await rtcClient.subscribe(user, "audio");
        const track = user.audioTrack;
        if (track) {
          track.play();
          setRemoteAudioTrack(track);
          setIsAgentSpeaking(true);
        }
      }
    };

    const handleUserUnpublished = (
      user: IAgoraRTCRemoteUser,
      mediaType: "audio" | "video",
    ) => {
      if (mediaType === "audio") {
        setIsAgentSpeaking(false);
        setRemoteAudioTrack(null);
      }
    };

    const handleUserLeft = () => {
      setIsAgentSpeaking(false);
      setRemoteAudioTrack(null);
    };

    rtcClient.on("user-published", handleUserPublished);
    rtcClient.on("user-unpublished", handleUserUnpublished);
    rtcClient.on("user-left", handleUserLeft);

    return () => {
      rtcClient.off("user-published", handleUserPublished);
      rtcClient.off("user-unpublished", handleUserUnpublished);
      rtcClient.off("user-left", handleUserLeft);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rtcClientRef.current]);

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

  const leaveChannel = useCallback(async () => {
    try {
      // Cleanup AgoraVoiceAI
      if (aiRef.current) {
        aiRef.current.unsubscribe();
        aiRef.current.destroy();
        aiRef.current = null;
      }

      // Cleanup RTM
      if (rtmClientRef.current) {
        try {
          await rtmClientRef.current.logout();
        } catch {
          // ignore logout errors
        }
        rtmClientRef.current = null;
      }

      // Cleanup local audio track
      if (localAudioTrackRef.current) {
        localAudioTrackRef.current.stop();
        localAudioTrackRef.current.close();
        localAudioTrackRef.current = null;
      }

      // Cleanup RTC client
      if (rtcClientRef.current) {
        await rtcClientRef.current.leave();
        rtcClientRef.current = null;
      }

      setLocalAudioTrack(null);
      setIsConnected(false);
      setMicState("idle");
      setIsAgentSpeaking(false);
      setMessageList([]);
      setCurrentInProgressMessage(null);
    } catch (error) {
      console.error("Error leaving channel:", error);
    }
  }, []);

  const joinChannel = useCallback(
    async (config: VoiceClientConfig) => {
      if (isConnected) {
        await leaveChannel();
      }

      try {
        // 1. Create RTC client
        const rtcClient = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
        rtcClientRef.current = rtcClient;

        // 2. Create microphone audio track
        const audioTrack = await AgoraRTC.createMicrophoneAudioTrack({
          encoderConfig: "high_quality_stereo",
          AEC: true,
          ANS: true,
          AGC: true,
          ...(config.microphoneId ? { microphoneId: config.microphoneId } : {}),
        });
        localAudioTrackRef.current = audioTrack;

        // 3. Join RTC channel
        await rtcClient.join(
          config.appId,
          config.channel,
          config.token,
          config.uid,
        );

        // 4. Publish audio track
        await rtcClient.publish([audioTrack]);

        setLocalAudioTrack(audioTrack);
        setIsConnected(true);
        setMicState("listening");

        // 5. Create and login RTM client
        const rtmClient = new AgoraRTM.RTM(config.appId, `${config.uid}`);
        await rtmClient.login({
          token: config.token ?? undefined,
        });
        await rtmClient.subscribe(config.channel);
        rtmClientRef.current = rtmClient;

        // 6. Initialize AgoraVoiceAI (async)
        const ai = await AgoraVoiceAI.init({
          rtcEngine: rtcClient,
          rtmConfig: { rtmEngine: rtmClient },
          renderMode: TranscriptHelperMode.TEXT,
          enableLog: true,
        });

        // 7. Subscribe to messages on channel
        ai.subscribeMessage(config.channel);

        // 8. Listen to transcript updates
        ai.on(
          AgoraVoiceAIEvents.TRANSCRIPT_UPDATED,
          (messages: TranscriptHelperItem<unknown>[]) => {
            // Fix missing spaces: server sometimes omits spaces after punctuation
            const fixSpacing = (t: string) =>
              t.replace(/([.!?,:;])([A-Za-z])/g, "$1 $2");

            const convertedMessages: IMessageListItem[] = messages.map((m) => ({
              turn_id: m.turn_id,
              uid: parseInt(m.uid) || 0,
              text: fixSpacing(m.text),
              status: m.status,
              timestamp: m._time,
            }));

            // Filter out in-progress messages and sort by timestamp
            const completedMessages = convertedMessages
              .filter((msg) => msg.status !== TurnStatus.IN_PROGRESS)
              .sort((a, b) => (a.timestamp ?? 0) - (b.timestamp ?? 0));

            const inProgress = convertedMessages.find(
              (msg) => msg.status === TurnStatus.IN_PROGRESS,
            );

            setMessageList(completedMessages);
            setCurrentInProgressMessage(inProgress || null);
          },
        );

        aiRef.current = ai;
      } catch (error) {
        console.error("Error joining channel:", error);
        throw error;
      }
    },
    [isConnected, leaveChannel],
  );

  const toggleMute = useCallback(async () => {
    const audioTrack = localAudioTrackRef.current;
    if (!audioTrack) return;

    try {
      await audioTrack.setEnabled(isMuted);
      setIsMuted(!isMuted);
      setMicState(!isMuted ? "idle" : "listening");
    } catch (error) {
      console.error("Error toggling mute:", error);
    }
  }, [isMuted]);

  const sendMessage = useCallback(
    async (message: string, agentUid: string = "100") => {
      const ai = aiRef.current;
      if (!ai) {
        console.error("Cannot send message: AgoraVoiceAI not initialized");
        return false;
      }

      try {
        await ai.sendText(agentUid, {
          text: message,
          messageType: ChatMessageType.TEXT,
          priority: ChatMessagePriority.INTERRUPTED,
          responseInterruptable: true,
        });
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
    joinChannel,
    leaveChannel,
    toggleMute,
    sendMessage,
    rtmClient: rtmClientRef.current,
  };
}
