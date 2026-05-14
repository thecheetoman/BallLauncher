#pragma once

extern bool motorState;  // Declaration only (extern)

void initMotor();
void motorEnable();
void motorDisable();
void motorStateHigh();
void motorStateLow();
void updateMotorRamp();  // Call this regularly in main loop
void startRamp(int newRPWM, int newLPWM);  // Directly start a ramp to specific values