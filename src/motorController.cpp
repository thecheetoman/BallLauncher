#include "constants.h"
#include <Arduino.h>
#include <cmath>

// Ramping variables
int currentRPWM = 0;
int currentLPWM = 0;
int targetRPWM = 0;
int targetLPWM = 0;
int startRPWM = 0;
int startLPWM = 0;
unsigned long rampStartTime = 0;
const unsigned long RAMP_DURATION = 500; // milliseconds for ramp to complete
bool isRamping = false;

void initMotor(){
    pinMode(mEnable, OUTPUT);
    pinMode(LPWM, OUTPUT);
    pinMode(RPWM, OUTPUT);
    delay(10);
    analogWrite(LPWM, 0);
    analogWrite(RPWM, 0);
    currentLPWM = 0;
    currentRPWM = 0;
    targetLPWM = 0;
    targetRPWM = 0;
    digitalWrite(mEnable, HIGH);
}
bool motorState = false;

// Sine curve ramping function - call this regularly in your main loop
void updateMotorRamp(){
    if(!isRamping) return;
    
    unsigned long elapsedTime = millis() - rampStartTime;
    
    if(elapsedTime >= RAMP_DURATION){
        // Ramp complete
        currentRPWM = targetRPWM;
        currentLPWM = targetLPWM;
        isRamping = false;
    } else {
        // Calculate progress (0 to 1)
        float progress = (float)elapsedTime / RAMP_DURATION;
        
        // Apply sine curve (0 to pi/2) for smooth acceleration
        float sinProgress = sin(progress * M_PI / 2.0);
        
        // Interpolate between start and target using sine curve
        currentRPWM = (int)(startRPWM + (targetRPWM - startRPWM) * sinProgress);
        currentLPWM = (int)(startLPWM + (targetLPWM - startLPWM) * sinProgress);
    }
    
    // Write the current values
    analogWrite(LPWM, currentLPWM);
    analogWrite(RPWM, currentRPWM);
}

// Helper function to start a ramp
void startRamp(int newRPWM, int newLPWM){
    startRPWM = currentRPWM;  // Store current values as start point
    startLPWM = currentLPWM;
    targetRPWM = newRPWM;
    targetLPWM = newLPWM;
    rampStartTime = millis();
    isRamping = true;
}

//Enable motor
void motorEnable(){
    motorState = true;
    startRamp(0, 100);
}
//Disable motor
void motorDisable(){
    motorState = true;
    startRamp(0, 0);
}

//When turret motor activated, activated motor stage, when not activated, low power stage
void motorStateHigh(){
    motorState = true;
    startRamp(0, mHigh);
}
void motorStateLow(){
    motorState = false;
    startRamp(0, mLow);
}