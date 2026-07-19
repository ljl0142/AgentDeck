#include <Arduino.h>
#include <M5Cardputer.h>

void setup() {
    auto cfg = M5.config();
    M5Cardputer.begin(cfg, true);

    Serial.begin(115200);
    Serial.println("AgentDeck started");
}

void loop() {
    M5Cardputer.update();
    delay(10);
}