#pragma once

#include <Arduino.h>

enum class HubEventType {
    AuthReady,
    SessionReady,
    StatusChanged,
    MessageSent,
    MessageDelta,
    CommandStarted,
    CommandCompleted,
    TurnCompleted,
    Error,
    Pong,
    Unknown
};

struct HubEvent {
    HubEventType type = HubEventType::Unknown;

    String text;
    String status;
    String errorCode;
    String errorMessage;
    String threadId;
    String command;

    int protocolVersion=0;
    int exitCode=0;
};

String makeAuthLogin(const String& token);
String makeMessageSend(const String& text);
String makeStatusGet();
String makePing();

HubEvent parseHubEvent(const String& json);