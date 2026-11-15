#define CUSTOM_SETTINGS
#define INCLUDE_GAMEPAD_MODULE
#include <DabbleESP32.h>

const char* BT_NAME = "ESP32_DiffDriveBot";

// ---------------- Joystick ----------------
const float RADIUS_DEADZONE = 0.5;
const int MAX_SPEED = 127;

// ---------------- MDD3A pins ----------------
// Motor 1
const int m1a = 26;
const int m1b = 27;

// Motor 2
const int m2a = 32;
const int m2b = 33;

// PWM settings
const int PWM_FREQ = 20000;   // 20 kHz
const int PWM_RES  = 8;       // 0-255


// =====================================================
// Motor 1 control
// speed: -255 to +255
// =====================================================
void setMotor1(int speed)
{
  speed = constrain(speed, -255, 255);

  if (speed > 0)
  {
    // Forward
    ledcWrite(m1a, speed);
    ledcWrite(m1b, 0);
  }
  else if (speed < 0)
  {
    // Reverse
    ledcWrite(m1a, 0);
    ledcWrite(m1b, -speed);
  }
  else
  {
    // Stop
    ledcWrite(m1a, 0);
    ledcWrite(m1b, 0);
  }
}


// =====================================================
// Motor 2 control
// speed: -255 to +255
// =====================================================
void setMotor2(int speed)
{
  speed = constrain(speed, -255, 255);

  if (speed > 0)
  {
    // Forward
    ledcWrite(m2a, speed);
    ledcWrite(m2b, 0);
  }
  else if (speed < 0)
  {
    // Reverse
    ledcWrite(m2a, 0);
    ledcWrite(m2b, -speed);
  }
  else
  {
    // Stop
    ledcWrite(m2a, 0);
    ledcWrite(m2b, 0);
  }
}


void setup()
{
  Serial.begin(115200);

  // Attach PWM to all four MDD3A inputs
  ledcAttach(m1a, PWM_FREQ, PWM_RES);
  ledcAttach(m1b, PWM_FREQ, PWM_RES);

  ledcAttach(m2a, PWM_FREQ, PWM_RES);
  ledcAttach(m2b, PWM_FREQ, PWM_RES);

  // Start with motors stopped
  setMotor1(0);
  setMotor2(0);

  // Start Dabble Bluetooth
  Dabble.begin(BT_NAME);

  Serial.println("ESP32 Differential Drive Ready");
}


void loop()
{
  Dabble.processInput();

  // -------------------------------------------------
  // Read joystick
  // -------------------------------------------------
  float angle  = GamePad.getAngle();
  float radius = GamePad.getRadius();

  int leftSpeed = 0;
  int rightSpeed = 0;


  // -------------------------------------------------
  // Joystick -> differential drive mixing
  // -------------------------------------------------
  if (radius > RADIUS_DEADZONE)
  {
    float rad = angle * PI / 180.0;

    float x = radius * cos(rad);
    float y = radius * sin(rad);

    float left  = y + x;
    float right = y - x;

    float scale = (float)MAX_SPEED / 7.0;

    leftSpeed = constrain(
      (int)(left * scale),
      -MAX_SPEED,
      MAX_SPEED
    );

    rightSpeed = constrain(
      (int)(right * scale),
      -MAX_SPEED,
      MAX_SPEED
    );
  }


  // -------------------------------------------------
  // Send speeds to MDD3A
  // -------------------------------------------------
  setMotor1(leftSpeed);
  setMotor2(rightSpeed);


  // -------------------------------------------------
  // Debug
  // -------------------------------------------------
  Serial.print("Angle: ");
  Serial.print(angle);

  Serial.print("  Radius: ");
  Serial.print(radius);

  Serial.print("  L: ");
  Serial.print(leftSpeed);

  Serial.print("  R: ");
  Serial.println(rightSpeed);


  delay(10);
}