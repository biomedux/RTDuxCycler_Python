#include <AccelStepper.h>
#include <Servo.h>

// Stepper motor pins
const int M1 = 2; //orange, A-
const int M2 = 3; //pink, A+
const int M3 = 4; //yellow, B+
const int M4 = 5; //blue, B-

// Home sensor constants
const int SENSOR = 7; // hall sensor
const int SENSOR_ON = 0; // home sensor polarity

// Led sensor constantsR
const int LED_PWM = 10;

// Servo motor constants
const int LID_SERVO_PIN = 8;
const int CHAMBER_SERVO_PIN = 9;

// Led var
int pwm = 0;

// Servo var
Servo lid_servo;
Servo chamber_servo;

int lid_servo_pwm = 2000;
int chamber_servo_pwm = 1000;

// Speed var
int homeHighSp = 0; // home high speed (coarse search 시 사용)
int homeLowSp = 0; // home low speed (fine search 시 사용)
int mSpeed = 0; // max speed
int acc = 0; // acceleration

// Position var
int targetPos = 0;
int targetDir = 0;
int curPos = 0;

// Flag var
bool homing = false; // homing 중인가?
bool homefine = false; // home coarse search가 끝나고 home fine search 중인가?
bool runAllowed = false;

// Command var
char cmd;

//Response header
char header_byte[2] = {255, 255};
String res_header = String(header_byte);

AccelStepper stepper(AccelStepper::FULL4WIRE, M1, M2, M3, M4);

void lid_servo_init(){
  lid_servo.attach(LID_SERVO_PIN);
  lid_servo.writeMicroseconds(lid_servo_pwm);
  delay(6000);  
  //lid_servo.detach();
}

void chamber_servo_init(){
  chamber_servo.attach(CHAMBER_SERVO_PIN);
  chamber_servo.writeMicroseconds(chamber_servo_pwm);
  delay(6000);
  //chamber_servo.detach();
}

void homeInt()
{
  if( homing ){
    if( !homefine ) {// When home fine is 'false'
      homefine = true;
      stepper.setMaxSpeed(homeLowSp);
      stepper.move(-10000);
    }
    else {// When home fine is 'true'
      stepper.stop();
      curPos = 0;
      targetPos = 0;
  
      stepper.setCurrentPosition(0);
      stepper.setMaxSpeed(mSpeed);
      
      homing = false;
      homefine = false;
      runAllowed = false;
  
      Serial.println(res_header + "done");
    }
 }
  
}

void stepper_release()
{
  digitalWrite(M1, LOW);
  digitalWrite(M2, LOW);
  digitalWrite(M3, LOW);
  digitalWrite(M4, LOW);
}

void setup() {
  // Set baudrate
  Serial.begin(9600);
  
  // Set fine search interrupt
  attachInterrupt(digitalPinToInterrupt(SENSOR), homeInt, CHANGE);//중간에 껐다 켰다하면 이상동작

  // Set enable pin
//  pinMode(LED_ENABLE, OUTPUT);
//  analogWrite(LED_ENABLE, pwm);
  pinMode(LED_PWM, OUTPUT);
  analogWrite(LED_PWM, pwm);
  // Set led pins
  //pinMode(LED_PIN, OUTPUT);

  // Set Servo
  // servo1.attach(SERVO_PIN1); // lid
  // servo2.attach(SERVO_PIN2); // tray
  // servo1.writeMicroseconds(servo1_pwm);
  // servo2.writeMicroseconds(servo2_pwm);

  lid_servo_init();
  chamber_servo_init();
}

void loop() {
  if(Serial.available() > 0)
  { 
    cmd = Serial.read();
    if (cmd == 'P')// Set led PWM
    {
      pwm = Serial.parseInt();
      analogWrite(LED_PWM, pwm);
    }
    else if(cmd == 'p')// Get led PWM
    {
      Serial.println(res_header + pwm);
    }
    else if(cmd == 'Y')// Set servo1(Lid) pwm
    {
      lid_servo_pwm = Serial.parseInt();
      
      //lid_servo.attach(LID_SERVO_PIN);
            
      lid_servo.writeMicroseconds(lid_servo_pwm);

      delay(6000);

      //chamber_servo.detach();

      Serial.println(res_header + "done " + String(lid_servo_pwm));
    }
    else if(cmd == 'X')// Set servo2(Tray) pwm
    {
      chamber_servo_pwm = Serial.parseInt();
      
      //chamber_servo.attach(CHAMBER_SERVO_PIN);
            
      chamber_servo.writeMicroseconds(chamber_servo_pwm);

      delay(6000);

      //chamber_servo.detach();

      Serial.println(res_header + "done " + String(chamber_servo_pwm));
    }
    else if(cmd == 'H')// Set home high speed
    {
      homeHighSp = Serial.parseInt();
    }
    else if(cmd == 'h')// Get home high speed
    {
      Serial.println(res_header + String(homeHighSp));
    }
    else if(cmd == 'S')// Set home low speed
    {
      homeLowSp = Serial.parseInt();
    }
    else if(cmd == 's')// Get home low speed
    {
      Serial.println(res_header + String(homeLowSp));
    }
    else if(cmd == 'M')// Set max speed
    {
      mSpeed = Serial.parseInt();
      stepper.setMaxSpeed(mSpeed);
    }
    else if(cmd == 'm')// Get max speed
    {
      Serial.println(res_header + String(stepper.maxSpeed()));
    }
    else if(cmd == 'C')// Set current position
    {
      int pos = Serial.parseInt();
      stepper.setCurrentPosition(pos);
    }
    else if(cmd == 'c')// Get current position
    {
      Serial.println(res_header + String(stepper.currentPosition()));
    }
    else if(cmd == 'N')// Set target posiition
    {
      targetPos = Serial.parseInt();
      stepper.moveTo(targetPos);
      runAllowed = true;
    }
    else if(cmd == 'E')// Emergency stop
    {
      homing = false;
      homefine = false;
      runAllowed = false;
      stepper.stop();
    }
    else if(cmd == 'A')// Set accel
    {
      acc = Serial.parseInt();
      stepper.setAcceleration(acc);
    }
    else if(cmd == 'a')// Get accel
    {
      Serial.println(res_header + String(acc));
    }
    else if(cmd == 'o')// Get home sensor signal
    {
      Serial.println(res_header + String(digitalRead(SENSOR)));
    }
    else if(cmd == 'G')// Get home sensor signal
    {
      homing = true;
      runAllowed = true;

      if(digitalRead(SENSOR) == SENSOR_ON){//home sensor 인식 되면
        homefine = true;
        stepper.setMaxSpeed(homeLowSp);
        targetPos = -10000;
        stepper.move(targetPos);
      }
      else{                               //home sensor 인식이 안되면
        homefine = false;
        stepper.setMaxSpeed(homeHighSp);
        targetPos = 10000;
        stepper.move(targetPos); //negative 방향으로 충분히 검색한다.
      }
    }
  }// End of Serial.avaliable

  if (runAllowed){
    stepper.run();
    if ( !stepper.isRunning() ){
      runAllowed = false;
      stepper_release();
      Serial.println(res_header + "done");
    }
  }
}// End of loop
