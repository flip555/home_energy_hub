#pragma once

#include "esphome.h"

class TelnetUARTServer : public Component, public AsyncServer {
 public:
  // Constructor
  TelnetUARTServer() : AsyncServer(23) {} // Telnet server on port 23

  void setup() override;
  void loop() override;
  void onClientConnect(AsyncClient* client);
  void onClientDisconnect(AsyncClient* client);
  void onClientData(AsyncClient* client, char* data, size_t len);

 private:
  UARTComponent* uart_component_; // Reference to the UART component
};
