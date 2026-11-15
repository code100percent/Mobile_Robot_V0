#include "network_config.h"

// =====================================================
// ESP32 micro-ROS Differential Drive via /cmd_vel
// Subscribes to geometry_msgs/msg/Twist published by
// teleop_twist_keyboard (or any cmd_vel publisher)
// Drives an MDD3A dual motor driver.
// =====================================================

#include <micro_ros_arduino.h>

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <geometry_msgs/msg/twist.h>


//wifi config 
char ssid[] = ROBOT_WIFI_SSID;
char password[] = ROBOT_WIFI_PASSWORD;
char agent_ip[] = ROBOT_AGENT_IP;   // IP of the PC running the micro-ROS agent
const uint16_t agent_port = ROBOT_AGENT_PORT;

// -----------------------------------------------------
// micro-ROS objects
// -----------------------------------------------------
rcl_subscription_t subscriber;
geometry_msgs__msg__Twist msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

#define RCCHECK(fn)                 \
  {                                 \
    rcl_ret_t temp_rc = fn;         \
    if ((temp_rc != RCL_RET_OK)) {  \
      error_loop();                 \
    }                               \
  }
#define RCSOFTCHECK(fn)             \
  {                                 \
    rcl_ret_t temp_rc = fn;         \
    (void)temp_rc;                  \
  }

// -----------------------------------------------------
// Robot parameters -- ADJUST THESE FOR YOUR ROBOT
// -----------------------------------------------------
const float WHEEL_BASE        = 0.355f;  // distance between the two wheels, in meters
const float MAX_LINEAR_SPEED  = 0.5f;   // m/s that corresponds to full PWM (255)
const int   MAX_PWM           = 255;

// -----------------------------------------------------
// MDD3A pins (same as your original code)
// -----------------------------------------------------
const int m1a = 26;
const int m1b = 27;
const int m2a = 32;
const int m2b = 33;

const int PWM_FREQ = 20000;   // 20 kHz
const int PWM_RES  = 8;       // 0-255

// -----------------------------------------------------
// Safety timeout: stop motors if no cmd_vel received
// -----------------------------------------------------
unsigned long last_cmd_time = 0;
const unsigned long CMD_TIMEOUT = 500; // ms

#define LED_PIN 2

// =====================================================
// Error loop -- blinks onboard LED forever on failure
// =====================================================
void error_loop() {
  while (1) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
}

// =====================================================
// Motor 1 control (speed: -255 to +255)
// =====================================================
void setMotor1(int speed) {
  speed = constrain(speed, -255, 255);

  if (speed > 0) {
    ledcWrite(m1a, speed);
    ledcWrite(m1b, 0);
  } else if (speed < 0) {
    ledcWrite(m1a, 0);
    ledcWrite(m1b, -speed);
  } else {
    ledcWrite(m1a, 0);
    ledcWrite(m1b, 0);
  }
}

// =====================================================
// Motor 2 control (speed: -255 to +255)
// =====================================================
void setMotor2(int speed) {
  speed = constrain(speed, -255, 255);

  if (speed > 0) {
    ledcWrite(m2a, speed);
    ledcWrite(m2b, 0);
  } else if (speed < 0) {
    ledcWrite(m2a, 0);
    ledcWrite(m2b, -speed);
  } else {
    ledcWrite(m2a, 0);
    ledcWrite(m2b, 0);
  }
}

void stopMotors() {
  setMotor1(0);
  setMotor2(0);
}

// =====================================================
// cmd_vel subscription callback
// Converts Twist (linear.x, angular.z) into left/right
// wheel PWM using standard differential-drive kinematics
// =====================================================
void cmd_vel_callback(const void *msgin) {
  const geometry_msgs__msg__Twist *twist_msg =
      (const geometry_msgs__msg__Twist *)msgin;

  float linear_x  = (float)twist_msg->linear.x;   // m/s
  float angular_z = (float)twist_msg->angular.z;  // rad/s

  // Differential drive kinematics
  float left_speed_mps  = linear_x - (angular_z * WHEEL_BASE / 2.0f);
  float right_speed_mps = linear_x + (angular_z * WHEEL_BASE / 2.0f);

  // Convert m/s -> PWM (-255..255)
  int left_pwm  = (int)((left_speed_mps  / MAX_LINEAR_SPEED) * MAX_PWM);
  int right_pwm = (int)((right_speed_mps / MAX_LINEAR_SPEED) * MAX_PWM);

  left_pwm  = constrain(left_pwm,  -MAX_PWM, MAX_PWM);
  right_pwm = constrain(right_pwm, -MAX_PWM, MAX_PWM);

  setMotor1(left_pwm);
  setMotor2(right_pwm);

  last_cmd_time = millis();
}

// =====================================================
// Setup
// =====================================================
void setup() {
  // Use Serial (USB) as the micro-ROS transport.
  // set_microros_transports();
  
  //for wifi 
  set_microros_wifi_transports(ssid, password, agent_ip, agent_port);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // Attach PWM to all four MDD3A inputs
  ledcAttach(m1a, PWM_FREQ, PWM_RES);
  ledcAttach(m1b, PWM_FREQ, PWM_RES);
  ledcAttach(m2a, PWM_FREQ, PWM_RES);
  ledcAttach(m2b, PWM_FREQ, PWM_RES);

  stopMotors();

  delay(2000); // give the micro-ROS agent time to be ready

  allocator = rcl_get_default_allocator();

  // Create init_options
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));

  // Create node
  RCCHECK(rclc_node_init_default(&node, "esp32_diffdrive_node", "", &support));

  // Create subscriber on /cmd_vel
  RCCHECK(rclc_subscription_init_default(
      &subscriber,
      &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
      "/cmd_vel"));

  // Create executor
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(
      &executor, &subscriber, &msg, &cmd_vel_callback, ON_NEW_DATA));

  digitalWrite(LED_PIN, LOW);
}

// =====================================================
// Loop
// =====================================================
void loop() {
  // Safety: stop motors if no cmd_vel has arrived recently
  if (millis() - last_cmd_time > CMD_TIMEOUT) {
    stopMotors();
  }

  RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)));
}
