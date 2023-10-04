#include "telnet_uart_server.h"

void TelnetUARTServer::setup() {
  // Access the UART component based on its name in the YAML configuration
  uart_component_ = App.get_component<UARTComponent>("uart_0");

  // Start the Telnet server
  this->begin();
}

void TelnetUARTServer::loop() {
  // Your loop code if needed
}

void TelnetUARTServer::onClientConnect(AsyncClient* client) {
  // Called when a Telnet client connects
  ESP_LOGD("telnet_uart_server", "Client connected from %s", client->remoteIP().toString().c_str());
}

void TelnetUARTServer::onClientDisconnect(AsyncClient* client) {
  // Called when a Telnet client disconnects
  ESP_LOGD("telnet_uart_server", "Client disconnected from %s", client->remoteIP().toString().c_str());
}

void TelnetUARTServer::onClientData(AsyncClient* client, char* data, size_t len) {
  // Called when data is received from a Telnet client
  ESP_LOGD("telnet_uart_server", "Received %d bytes from client", len);

  // Process the received data (e.g., forward it to UART)
  uart_component_->write(data, len); // Forward data to UART

  // Send a response back to the Telnet client if needed
  client->write("Received your command: ");
  client->write(data, len);
}

// Define the instance of your custom component
TelnetUARTServer telnet_uart_server;
