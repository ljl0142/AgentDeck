#pragma once
#include <Arduino.h>

namespace AgentDeckConfig {
    constexpr int PROTOCOL_VERSION=1;

    constexpr char HUB_HOST[]="192.168.1.100";
    constexpr uint16_t HUB_PORT=8000;
    constexpr char HUB_PATH[]="/ws";

    constexpr unsigned long RECONNECT_INTERVAL_MS=5000;
    constexpr unsigned long PING_INTERVAL_MS=30000;

    constexpr size_t MAX_INPUT_LENGTH=512;
}