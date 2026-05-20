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
const unsigned long RAMP_DURATION = 1000; // milliseconds for ramp to complete
bool isRamping = false;

// Queue variables to force sequential stepping (fixes power crashes)
int nextTargetRPWM = -1;
int nextTargetLPWM = -1;

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
}
bool motorState = false;

// FIX: Moved startRamp UP here so updateMotorRamp can see it
void startRamp(int newRPWM, int newLPWM){
    // Safety check: Intercept direct jumps to mHigh from a standstill/low speed
    if (newLPWM >= mHigh && currentLPWM < 100) {
        nextTargetRPWM = newRPWM;
        nextTargetLPWM = newLPWM; // Queue up the mHigh target for later
        
        targetRPWM = 0;
        targetLPWM = 100; // Force it to ramp to the safe 100 stage first
    } else {
        // Regular ramp behavior
        nextTargetRPWM = -1;
        nextTargetLPWM = -1;
        targetRPWM = newRPWM;
        targetLPWM = newLPWM;
    }

    startRPWM = currentRPWM;  // Store current values as start point
    startLPWM = currentLPWM;
    rampStartTime = millis();
    isRamping = true;
}

// Smooth ramping function - call this regularly in your main loop
void updateMotorRamp(){
    if(!isRamping) return;
    
    unsigned long elapsedTime = millis() - rampStartTime;
    
    if(elapsedTime >= RAMP_DURATION){
        // Ramp complete
        currentRPWM = targetRPWM;
        currentLPWM = targetLPWM;
        isRamping = false;

        // If a high-power stage was queued up, start it now automatically
        if(nextTargetLPWM != -1 || nextTargetRPWM != -1){
            int queuedR = nextTargetRPWM;
            int queuedL = nextTargetLPWM;
            nextTargetRPWM = -1; // Clear queue
            nextTargetLPWM = -1;
            startRamp(queuedR, queuedL);
        }
    } else {
        // Calculate progress (0 to 1)
        float progress = (float)elapsedTime / RAMP_DURATION;
        
        // Ease-In-Out curve to prevent current spikes
        float smoothProgress = 0.5 * (1.0 - cos(progress * M_PI));
        
        // Interpolate between start and target
        currentRPWM = (int)(startRPWM + (targetRPWM - startRPWM) * smoothProgress);
        currentLPWM = (int)(startLPWM + (targetLPWM - startLPWM) * smoothProgress);
    }
    
    // Write the current values
    analogWrite(LPWM, currentLPWM);
    analogWrite(RPWM, currentRPWM);
}

//Enable motor
void motorEnable(){
    digitalWrite(mEnable, HIGH);
    motorState = true;
    startRamp(0, 100);
}
//Disable motor
void motorDisable(){
    digitalWrite(mEnable, LOW);
    motorState = false; 
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