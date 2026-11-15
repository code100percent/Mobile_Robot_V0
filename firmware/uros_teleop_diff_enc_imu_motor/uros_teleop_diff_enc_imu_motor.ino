#include "network_config.h"

// =====================================================
// ESP32 micro-ROS (WiFi) differential drive robot
//
// Subscribes : /cmd_vel        geometry_msgs/Twist
// Publishes  : /imu/data_raw   sensor_msgs/Imu          (50 Hz)
//              /wheel_ticks    std_msgs/Int32MultiArray (20 Hz)
//                              data[0] = left ticks, data[1] = right ticks
//
// Motor driver : MDD3A
// Encoder 1 (left)  : A=GPIO35, B=GPIO34
// Encoder 2 (right) : A=GPIO13, B=GPIO14
// MPU6050 (I2C)     : SDA=GPIO21, SCL=GPIO22
// =====================================================

#include <micro_ros_arduino.h>
#include <Wire.h>

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rmw_microros/rmw_microros.h>

#include <geometry_msgs/msg/twist.h>
#include <sensor_msgs/msg/imu.h>
#include <std_msgs/msg/int32_multi_array.h>

// -----------------------------------------------------
// WiFi 
// -----------------------------------------------------
char ssid[] = ROBOT_WIFI_SSID;
char password[] = ROBOT_WIFI_PASSWORD;
char agent_ip[] = ROBOT_AGENT_IP;   // IP of the PC running the micro-ROS agent
const uint16_t agent_port = ROBOT_AGENT_PORT;

// -----------------------------------------------------
// micro-ROS objects
// -----------------------------------------------------
rcl_subscription_t cmd_sub;
rcl_publisher_t imu_pub;
rcl_publisher_t ticks_pub;
rcl_timer_t imu_timer;
rcl_timer_t ticks_timer;

geometry_msgs__msg__Twist cmd_msg;
sensor_msgs__msg__Imu imu_msg;
std_msgs__msg__Int32MultiArray ticks_msg;
int32_t ticks_data[2];

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
// Robot parameters
// -----------------------------------------------------
const float WHEEL_BASE       = 0.355f;  // meters
const float MAX_LINEAR_SPEED = 0.5f;    // m/s at full PWM
const int   MAX_PWM          = 255;

// -----------------------------------------------------
// MDD3A pins
// -----------------------------------------------------
const int m1a = 26;
const int m1b = 27;
const int m2a = 32;
const int m2b = 33;

const int PWM_FREQ = 20000;
const int PWM_RES  = 8;

// -----------------------------------------------------
// Encoders
// -----------------------------------------------------
const int E1A = 35, E1B = 34;   // left  (no internal pull-ups on 34/35)
const int E2A = 13, E2B = 14;   // right

// Flip to -1 if a wheel counts backwards when the robot drives forward
const int ENC1_SIGN = 1;
const int ENC2_SIGN = -1;       // right encoder faces the opposite way

volatile long ticks1 = 0;
volatile long ticks2 = 0;
volatile uint8_t prev1 = 0;
volatile uint8_t prev2 = 0;

// Quadrature lookup table (4x decoding): index = (prev << 2) | current
const int8_t QEM[16] = {0, -1, 1, 0,  1, 0, 0, -1,  -1, 0, 0, 1,  0, 1, -1, 0};

void IRAM_ATTR isr1() {
  uint8_t cur = (digitalRead(E1A) << 1) | digitalRead(E1B);
  ticks1 += QEM[(prev1 << 2) | cur];
  prev1 = cur;
}

void IRAM_ATTR isr2() {
  uint8_t cur = (digitalRead(E2A) << 1) | digitalRead(E2B);
  ticks2 += QEM[(prev2 << 2) | cur];
  prev2 = cur;
}

// -----------------------------------------------------
// MPU6050
// -----------------------------------------------------
const uint8_t MPU_ADDR = 0x68;
const float G_TO_MS2   = 9.80665f;
const float DEG_TO_RAD_F = 0.01745329252f;
bool mpu_ok = false;
float gx_bias = 0, gy_bias = 0, gz_bias = 0;   // rad/s

// -----------------------------------------------------
// Safety timeout
// -----------------------------------------------------
unsigned long last_cmd_time = 0;
const unsigned long CMD_TIMEOUT = 1000;  // ms (WiFi is less steady than USB)

#define LED_PIN 2

// =====================================================
void error_loop() {
  while (1) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
}

// =====================================================
// Motors
// =====================================================
void setMotor1(int speed) {
  speed = constrain(speed, -255, 255);
  if (speed > 0)      { ledcWrite(m1a, speed); ledcWrite(m1b, 0); }
  else if (speed < 0) { ledcWrite(m1a, 0);     ledcWrite(m1b, -speed); }
  else                { ledcWrite(m1a, 0);     ledcWrite(m1b, 0); }
}

void setMotor2(int speed) {
  speed = constrain(speed, -255, 255);
  if (speed > 0)      { ledcWrite(m2a, speed); ledcWrite(m2b, 0); }
  else if (speed < 0) { ledcWrite(m2a, 0);     ledcWrite(m2b, -speed); }
  else                { ledcWrite(m2a, 0);     ledcWrite(m2b, 0); }
}

void stopMotors() {
  setMotor1(0);
  setMotor2(0);
}

// =====================================================
// MPU6050 helpers
// =====================================================
int16_t read16() {
  int16_t hi = Wire.read();
  return (hi << 8) | Wire.read();
}

bool mpuInit() {
  Wire.begin(21, 22);
  Wire.setClock(400000);

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); Wire.write(0x00);          // wake up
  if (Wire.endTransmission() != 0) return false;

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1A); Wire.write(0x03);          // DLPF ~44 Hz
  Wire.endTransmission();
  return true;
}

// Reads raw accel (g) and gyro (rad/s, bias not removed)
bool mpuRead(float &ax, float &ay, float &az, float &gx, float &gy, float &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, (uint8_t)14, (uint8_t)true) != 14) return false;

  ax = read16() / 16384.0f;
  ay = read16() / 16384.0f;
  az = read16() / 16384.0f;
  read16();                                    // temperature
  gx = read16() / 131.0f * DEG_TO_RAD_F;
  gy = read16() / 131.0f * DEG_TO_RAD_F;
  gz = read16() / 131.0f * DEG_TO_RAD_F;
  return true;
}

// Average gyro at rest -> bias. Keep the robot still during boot.
void calibrateGyro() {
  const int N = 300;
  double sx = 0, sy = 0, sz = 0;
  int good = 0;
  for (int i = 0; i < N; i++) {
    float ax, ay, az, gx, gy, gz;
    if (mpuRead(ax, ay, az, gx, gy, gz)) {
      sx += gx; sy += gy; sz += gz; good++;
    }
    delay(5);
  }
  if (good > 0) {
    gx_bias = sx / good;
    gy_bias = sy / good;
    gz_bias = sz / good;
  }
}

// =====================================================
// Timestamp helper (uses agent time if synced)
// =====================================================
void stampNow(builtin_interfaces__msg__Time &t) {
  int64_t ns = rmw_uros_epoch_nanos();
  t.sec = (int32_t)(ns / 1000000000LL);
  t.nanosec = (uint32_t)(ns % 1000000000LL);
}

// =====================================================
// Callbacks
// =====================================================
void cmd_vel_callback(const void *msgin) {
  const geometry_msgs__msg__Twist *twist_msg =
      (const geometry_msgs__msg__Twist *)msgin;

  float linear_x  = (float)twist_msg->linear.x;
  float angular_z = (float)twist_msg->angular.z;

  float left_mps  = linear_x - (angular_z * WHEEL_BASE / 2.0f);
  float right_mps = linear_x + (angular_z * WHEEL_BASE / 2.0f);

  int left_pwm  = (int)((left_mps  / MAX_LINEAR_SPEED) * MAX_PWM);
  int right_pwm = (int)((right_mps / MAX_LINEAR_SPEED) * MAX_PWM);

  left_pwm  = constrain(left_pwm,  -MAX_PWM, MAX_PWM);
  right_pwm = constrain(right_pwm, -MAX_PWM, MAX_PWM);

  setMotor1(left_pwm);
  setMotor2(right_pwm);

  last_cmd_time = millis();
}

void imu_timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
  (void)last_call_time;
  if (timer == NULL || !mpu_ok) return;

  float ax, ay, az, gx, gy, gz;
  if (!mpuRead(ax, ay, az, gx, gy, gz)) return;

  stampNow(imu_msg.header.stamp);

  imu_msg.linear_acceleration.x = ax * G_TO_MS2;
  imu_msg.linear_acceleration.y = ay * G_TO_MS2;
  imu_msg.linear_acceleration.z = az * G_TO_MS2;

  imu_msg.angular_velocity.x = gx - gx_bias;
  imu_msg.angular_velocity.y = gy - gy_bias;
  imu_msg.angular_velocity.z = gz - gz_bias;

  RCSOFTCHECK(rcl_publish(&imu_pub, &imu_msg, NULL));
}

void ticks_timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
  (void)last_call_time;
  if (timer == NULL) return;

  ticks_data[0] = (int32_t)(ENC1_SIGN * ticks1);   // left
  ticks_data[1] = (int32_t)(ENC2_SIGN * ticks2);   // right

  RCSOFTCHECK(rcl_publish(&ticks_pub, &ticks_msg, NULL));
}

// =====================================================
// Setup
// =====================================================
void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.begin(115200);   // USB serial is free now (WiFi transport)
  delay(200);
  Serial.print("Reset reason: ");
  Serial.println((int)esp_reset_reason());

  // ---- PWM / motors ----
  ledcAttach(m1a, PWM_FREQ, PWM_RES);
  ledcAttach(m1b, PWM_FREQ, PWM_RES);
  ledcAttach(m2a, PWM_FREQ, PWM_RES);
  ledcAttach(m2b, PWM_FREQ, PWM_RES);
  stopMotors();

  // ---- Encoders ----
  pinMode(E1A, INPUT); pinMode(E1B, INPUT);              // 34/35: no pull-ups
  pinMode(E2A, INPUT_PULLUP); pinMode(E2B, INPUT_PULLUP);
  prev1 = (digitalRead(E1A) << 1) | digitalRead(E1B);
  prev2 = (digitalRead(E2A) << 1) | digitalRead(E2B);
  attachInterrupt(digitalPinToInterrupt(E1A), isr1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(E1B), isr1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(E2A), isr2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(E2B), isr2, CHANGE);

  // ---- MPU6050 (calibrate while robot is still) ----
  mpu_ok = mpuInit();
  if (mpu_ok) {
    Serial.println("MPU6050 OK, calibrating gyro (keep robot still)...");
    calibrateGyro();
    Serial.println("Gyro calibrated.");
  } else {
    Serial.println("MPU6050 NOT found - IMU topic will not publish");
  }

  // ---- micro-ROS over WiFi ----
  set_microros_wifi_transports(ssid, password, agent_ip, agent_port);
  delay(2000);

  allocator = rcl_get_default_allocator();
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "esp32_robot_node", "", &support));

  // Sync time with the agent (for message timestamps)
  rmw_uros_sync_session(1000);

  // ---- Subscriber: /cmd_vel ----
  RCCHECK(rclc_subscription_init_default(
      &cmd_sub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
      "/cmd_vel"));

  // ---- Publisher: /imu/data_raw (best effort) ----
  RCCHECK(rclc_publisher_init_best_effort(
      &imu_pub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
      "/imu/data_raw"));

  // ---- Publisher: /wheel_ticks ----
  RCCHECK(rclc_publisher_init_best_effort(
      &ticks_pub, &node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
      "/wheel_ticks"));

  // ---- Static message setup (no dynamic memory) ----
  static char frame_id[] = "imu_link";
  imu_msg.header.frame_id.data = frame_id;
  imu_msg.header.frame_id.size = strlen(frame_id);
  imu_msg.header.frame_id.capacity = sizeof(frame_id);

  imu_msg.orientation_covariance[0] = -1;   // -1 = orientation not provided
  for (int i = 0; i < 9; i++) {
    imu_msg.angular_velocity_covariance[i]    = 0;
    imu_msg.linear_acceleration_covariance[i] = 0;
  }
  imu_msg.angular_velocity_covariance[0]    = 0.0004;
  imu_msg.angular_velocity_covariance[4]    = 0.0004;
  imu_msg.angular_velocity_covariance[8]    = 0.0004;
  imu_msg.linear_acceleration_covariance[0] = 0.01;
  imu_msg.linear_acceleration_covariance[4] = 0.01;
  imu_msg.linear_acceleration_covariance[8] = 0.01;

  ticks_msg.data.data = ticks_data;
  ticks_msg.data.size = 2;
  ticks_msg.data.capacity = 2;
  ticks_msg.layout.dim.data = NULL;
  ticks_msg.layout.dim.size = 0;
  ticks_msg.layout.dim.capacity = 0;
  ticks_msg.layout.data_offset = 0;

  // ---- Timers ----
  RCCHECK(rclc_timer_init_default(
      &imu_timer, &support, RCL_MS_TO_NS(20), imu_timer_callback));    // 50 Hz
  RCCHECK(rclc_timer_init_default(
      &ticks_timer, &support, RCL_MS_TO_NS(50), ticks_timer_callback)); // 20 Hz

  // ---- Executor: 1 subscription + 2 timers = 3 handles ----
  RCCHECK(rclc_executor_init(&executor, &support.context, 3, &allocator));
  RCCHECK(rclc_executor_add_subscription(
      &executor, &cmd_sub, &cmd_msg, &cmd_vel_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_timer(&executor, &imu_timer));
  RCCHECK(rclc_executor_add_timer(&executor, &ticks_timer));

  digitalWrite(LED_PIN, LOW);
  Serial.println("micro-ROS ready.");
}

// =====================================================
// Loop
// =====================================================
void loop() {
  if (millis() - last_cmd_time > CMD_TIMEOUT) {
    stopMotors();
  }
  RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5)));
}
