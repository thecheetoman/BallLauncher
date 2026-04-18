#include <Arduino.h>

void setup() {
  //Comms
  // Start serial at 9600 baud
  Serial.begin(9600);
  // Built-in LED for power info
  pinMode(LED_BUILTIN, OUTPUT);
  // Wait for serial to be ready
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  Serial.println("Arduino Ready!");
}

void loop() {
  // Check if data available
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    
    // Process commands
    if (command == "LED_ON") {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("OK:LED_ON");
    }
    else {
      Serial.print("ERROR");
      Serial.println(command);
    }
  }
  
  delay(10); // Small delay to prevent flooding
}