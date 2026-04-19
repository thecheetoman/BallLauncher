#include <Arduino.h>
#include <Motor/motorController.h>
 
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
  initMotor();
  motorDisable();
}
 
void processCommand(String cmd) {
  // Handle individual commands
  if (cmd == "C_ON") {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("OK:Comm light on");
  }
  else if (cmd == "C_OFF") {
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("OK:Comm light off");
  }
  else if (cmd == "MHigh") {
    Serial.println("OK:Motor HIGH");
    motorTriggerHandler();
  }
  else if (cmd == "MLow") {
    Serial.println("OK:Motor LOW");
    motorTriggerHandler();
  }
  else if (cmd == "MEnable") {
  motorEnable();
  Serial.println("OK:Motor enabled");
  }
  else if (cmd == "MDisable") {
    motorDisable();
    Serial.println("OK:Motor disabled");
  }
  else if (cmd.length() > 0) {
    Serial.print("ERROR:Unknown command: ");
    Serial.println(cmd);
  }
}
 
void loop() {
  // Check if data available
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    
    // Check if compound command (contains colon)
    int colonIndex = command.indexOf(':');
    
    if (colonIndex > 0) {
      // Split compound command by colon
      String firstCmd = command.substring(0, colonIndex);
      String remainingCmds = command.substring(colonIndex + 1);
      
      // Process first command
      firstCmd.trim();
      processCommand(firstCmd);
      
      // Process remaining commands (could have multiple colons)
      while (remainingCmds.length() > 0) {
        colonIndex = remainingCmds.indexOf(':');
        
        if (colonIndex > 0) {
          String nextCmd = remainingCmds.substring(0, colonIndex);
          nextCmd.trim();
          processCommand(nextCmd);
          remainingCmds = remainingCmds.substring(colonIndex + 1);
        } else {
          // Last command
          remainingCmds.trim();
          processCommand(remainingCmds);
          break;
        }
      }
    } else {
      // Single command, no colon
      processCommand(command);
    }
  }
  
  delay(10); // Small delay to prevent flooding
}