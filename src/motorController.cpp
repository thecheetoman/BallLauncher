#include "constants.h"
#include <Arduino.h>

void initMotor(){
    pinMode(mEnable, OUTPUT);
    pinMode(LPWM, OUTPUT);
    pinMode(RPWM, OUTPUT);
    delay(10);
    analogWrite(LPWM, 100);
    analogWrite(RPWM, 0);
}
bool motorState = false;

//Enable motor
void motorEnable(){
    digitalWrite(mEnable, HIGH);
}
//Disable motor
void motorDisable(){
    digitalWrite(mEnable, LOW);
}

//When turret motor activated, activated motor stage, when not activated, low power stage
void motorStateHigh(){
    motorState = true;
    analogWrite(LPWM, mHigh);
    analogWrite(RPWM, 0);
}
void motorStateLow(){
    motorState = false;
    analogWrite(LPWM, mLow);
    analogWrite(RPWM, 0);
}