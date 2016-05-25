/*
 * Michael J. Harms
 * 2015-12-26
 * harmsm@gmail.com
 * 
 */

/* ----------------------------------------------------------------------------
 * Constants              
 * --------------------------------------------------------------------------*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "CmdMessenger.h"

/* Serial communications */
const int BAUD_RATE = 115200;

/* Motor and sensor configuration */
const int NUM_MOTORS = 2;                       // number of motors being controlled
const int SPEEDOMETER_PINS[2] = {A0,A1};        // analog input pins 
const int MOTOR_DIRECTION_PINS[2] = {2,4};      // any digtial pins
const int MOTOR_SPEED_PINS[2] = {3,5};          // should be pwm pins
const int MOTOR_THROTTLE_MIN = 0;               // min motor throttle (pwm min)
const int MOTOR_THROTTLE_MAX = 255;             // max motor throttle (pwm max)
const double MAGNET_SPACING = 1/12.0;           // (1/num_magnets) on wheels, assuming even spacing

/* PID motor control */
const double PID_KP[2] = {50.0,50.0};           // PID proportional constant
const double PID_KI[2] = {0.05,0.05};           // PID integral constant
const double PID_EXPECT_DELAY[2] = {50,50};     // ms to weight between checks for slow motors
const double PID_EXPECT_SCALAR[2] = {0.5,0.5};  // decay constant for estimated motor speed
const int SAMPLING_PERIOD = 0;                  // ms, how often to check sensors and update system

/* Sundry variables used to keep track of wheel and motor behavior */
unsigned int motor_throttle[2] = {0,0};         // pwm throttle, between 0 and 255
unsigned long last_sensor_value[2] = {0,0};     // last sensor value, 0 or 1
unsigned long last_sensor_flip_time[2] = {0,0}; // time (ms, absolute) of last sensor flip from HIGH->LOW
double expected_new_flip_time[2] = {0,0};       // guesstimate of next flip.
double motor_set_speed[2] = {0,0};              // motor set speed, in revolutions per s
int motor_set_direction[2] = {0,0};             // motor direction, 0 (forward), 1 (reverse)
double estimated_speed[2] = {0,0};              // current best guess of speed (revolutions/s)
double error[2] = {0.0, 0.0};                   // raw error (set - actual)
double integral_error[2] = {0.0, 0.0};          // integrated error over time

/* ----------------------------------------------------------------------------
 * Serial communication (using cmdMessenger callbacks)
 * --------------------------------------------------------------------------*/

/* Attach a CmdMessenger instance to the default serial port */
CmdMessenger c = CmdMessenger(Serial,fld_separator=',',cmd_separator=';',esc_character='/');

/* Define available CmdMessenger commands */
enum {
    cmd_set_speed,
    cmd_get_speed,
    cmd_set_speed_return,
    cmd_get_speed_return,
    cmd_error,
};

/* Define callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    // Attach callback methods
    c.attach(on_unknown_command);
    c.attach(cmd_set_speed,on_set_speed);
    c.attach(cmd_get_speed,on_get_speed);
}

void on_unknown_command(void){
    c.sendCmd(cmd_error,"Command without callback.");
}

void on_set_speed(void){
    
    /* Set the motor speed based on what comes in over serial */

    int i;
    double tmp_read;
    
    for (i = 0; i < NUM_MOTORS; i++){
        tmp_read = c.readDoubleArg();

        motor_set_speed[i] = abs(tmp_read);
        if (tmp_read < 0){
            motor_set_direction[i] = 1;
        } else { 
            motor_set_direction[i] = 0;
        }
    }

    /* Acknowledge command recieved successfully. */
    c.sendCmd(cmd_set_speed_return,0);

}

void on_get_speed(void){

    int i;
    c.sendCmdStart(cmd_get_speed_return);
    for (i = 0; i < NUM_MOTORS; i++){
        c.sendCmdArg(estimated_speed[i]*motor_set_direction[i]);
        c.sendCmdArg(motor_throttle[i]);   
    }
    c.sendCmdEnd();

}

/* ----------------------------------------------------------------------------
 * Main motor and speedometer feedback loop
 * --------------------------------------------------------------------------*/

void speed_motor_feedback(void){
    
    /* Measure the speed of each wheel, compare to the set speed, and then adjust
     * each throttle appropriately */
 
    int sensor_value, update, new_throttle;
    unsigned long current_time, delta_t;

    /* Loop over each motor */ 
    for (int i = 0; i < NUM_MOTORS; i++){
            
        /* Get the new time */
        current_time = millis();
        delta_t = current_time - last_sensor_flip_time[i];

        /* Check: is magnet in front of hall sensor? (0 -> yes, 1 -> no)*/ 
        sensor_value = digitalRead(SPEEDOMETER_PINS[i]);

        /* If the sensor has changed state */
        update = 0;
        if (sensor_value != last_sensor_value[i]){
        
            last_sensor_value[i] = sensor_value;
        
            /* Only actually set throttle based on HIGH->LOW transitions.  This 
             * corresponds to having the magnet starting its pass in front of 
             * the hall sensor rather than leaving it.   */
            if (sensor_value == 0){

                estimated_speed[i] = MAGNET_SPACING * 1000.0/(delta_t);
                last_sensor_flip_time[i] = current_time; 
          
                /* Guesstimate when the next sensor reading will be so, if the motor
                 * slows a lot, we'll notice that the magnet pass is late and be able to
                 * crank up the motor */
                expected_new_flip_time[i] = current_time + 1000.0*MAGNET_SPACING/motor_set_speed[i] + PID_EXPECT_DELAY[i];

                update = 1;
            }
   
        }

        /* If there's no flip, but we've been waiting longer than expected, 
         * scale down the estimated speed, start saying we expect the magnet to appear
         * very soon, and then run PID */
        if ((update == 0) && (current_time > expected_new_flip_time[i])){
            estimated_speed[i] = estimated_speed[i]*PID_EXPECT_SCALAR[i];
            expected_new_flip_time[i] = current_time + PID_EXPECT_DELAY[i];
            update = 1;
        }

        /* If the motor direction is flipped, reset the integrators etc.  Assume
         * start from stop */
        if (MOTOR_DIRECTION_PINS[i] != set_motor_direction[i]){

            digitalWrite(MOTOR_DIRECTION_PINS[i],set_motor_direction[i]);

            estimated_speed[i] = 0.0;
            integral_error[i] = 0.0;
            
            last_sensor_value[i] = sensor_value;
            last_sensor_flip_time[i] = current_time; 
            
            update = 1;
        }

        // If we're set to update our throttle ...
        if (update == 1){

            // Calculate errors
            error[i] = motor_set_speed[i] - estimated_speed[i];
            integral_error[i] = integral_error[i] + error[i]*delta_t;

            // apply PID controller
            new_throttle = PID_KP[i]*(error[i] + PID_KI[i]*integral_error[i]);
       
            // Cap out throttles.  If we cap out, don't account for integral error
            // because we can't actually adjust any more.  The accumulated error 
            // would lead to massive under/overshoot.
            if (new_throttle > MOTOR_THROTTLE_MAX){
                new_throttle = MOTOR_THROTTLE_MAX;
                integral_error[i] = integral_error[i] - error[i]*delta_t;
            }

            if (new_throttle < MOTOR_THROTTLE_MIN){
                new_throttle = MOTOR_THROTTLE_MIN;
                integral_error[i] = integral_error[i] - error[i]*delta_t;
            }
           
            // Apply new throttle setting to the motor. 
            motor_throttle[i] = new_throttle;
            analogWrite(MOTOR_SPEED_PINS[i],motor_throttle[i]); 

        }


    }

}

/* ---------------------------------------------------------------------------
 * Set up (on boot or reset). 
 * -------------------------------------------------------------------------- */

void setup() {

    /* Initialize the sensors and motors */
    for (int i = 0; i < NUM_MOTORS; i++){

        pinMode(SPEEDOMETER_PINS[i],INPUT);
        last_sensor_value[i] = digitalRead(SPEEDOMETER_PINS[i]);
        last_sensor_flip_time[i] = millis();
        expected_new_flip_time[i] = last_sensor_flip_time[i];
      
        pinMode(MOTOR_SPEED_PINS[i],OUTPUT); 
        analogWrite(MOTOR_SPEED_PINS[i],0);

        motor_throttle[i] = 0.0;
        estimated_speed[i] = 0.0;
        integral_error[i] = 0.0;

        pinMode(MOTOR_DIRECTION_PINS[i],OUTPUT);
        digitalWrite(MOTOR_DIRECTION_PINS[i],0);

    }

    /* Initialize serial communication at BAUD_RATE bits per second: */
    Serial.begin(BAUD_RATE);

}

/* ---------------------------------------------------------------------------
 * Main loop
 * -------------------------------------------------------------------------- */

void loop() {

    /* Deal with serial I/O */
    c.feedinSerialData();

    /* Motor control feedback loop, integrating speedometers and motors to 
     * hold a fixed speed. */
    speed_motor_feedback();

    delay(SAMPLING_PERIOD);

}


