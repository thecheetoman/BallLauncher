#pragma once

extern bool motorState;  // Declaration only (extern)

void initMotor();
void motorEnable();
void motorDisable();
void motorTriggerHandler();