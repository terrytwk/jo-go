#include <SPI.h>
#include <MFRC522.h>
#include <TFT_eSPI.h>
#include <WiFiClientSecure.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <string.h>

#define SS_PIN 34  // ESP32 pin GIOP5 => Pin 29
#define RST_PIN 20 //

TFT_eSPI tft = TFT_eSPI();

const uint16_t RESPONSE_TIMEOUT = 6000;
const uint16_t IN_BUFFER_SIZE = 5000; //size of buffer to hold HTTP request
const uint16_t OUT_BUFFER_SIZE = 1000; //size of buffer to hold HTTP response
const uint16_t GET_TIME = 900;
char request[IN_BUFFER_SIZE];
char response[OUT_BUFFER_SIZE];

const char test_ID[] = "2B B8 59 B1";

WiFiClientSecure client; //global WiFiClient Secure object
WiFiClient client2; //global WiFiClient Secure object

const char NETWORK[] = "MIT GUEST";
const char PASSWORD[] = "";

uint8_t channel = 1; //network channel on 2.4 GHz

MFRC522 rfid(SS_PIN, RST_PIN); // Instance of the class

// Init array that will store new NUID 
byte nuidPICC[4];
const char tap_in[] = "tap-in";
const char tap_out[] = "tap-out";

const uint8_t RED = 0;
const uint8_t GREEN = 1;
const uint8_t BLUE = 2;

//Audio
uint8_t AUDIO_TRANSDUCER = 14;
uint8_t AUDIO_PWM = 3;

//state for checked in and out
int signed_in;

//To check if the same ID is present

void setup() { 
  Serial.begin(115200); //begin serial comms
  //TFT initializtation stuff:README.md
  tft.setRotation(2); //adjust rotation
  tft.setTextSize(1); //default font size
  tft.fillScreen(TFT_BLACK); //fill background
  tft.setTextColor(TFT_GREEN, TFT_BLACK); //set color of font to green foreground, black background
  tft.setCursor(0, 0, 2); //set cursor
  WiFi.begin(NETWORK, PASSWORD);
  //WiFi.begin(network, password, channel, bssid);

  uint8_t count = 0; //count used for Wifi check times
  Serial.print("Attempting to connect to ");
  Serial.println(NETWORK);
  while (WiFi.status() != WL_CONNECTED && count < 12) {
    delay(500);
    Serial.print(".");
    count++;
  }
  delay(2000);
  if (WiFi.isConnected()) { //if we connected then print our IP, Mac, and SSID we're on
    Serial.println("CONNECTED!");
    Serial.printf("%d:%d:%d:%d (%s) (%s)\n", WiFi.localIP()[3], WiFi.localIP()[2],
                  WiFi.localIP()[1], WiFi.localIP()[0],
                  WiFi.macAddress().c_str() , WiFi.SSID().c_str());
    delay(500);
  } else { //if we failed to connect just Try again.
    Serial.println("Failed to Connect :/  Going to restart");
    Serial.println(WiFi.status());
    ESP.restart(); // restart the ESP (proper way)
  }

  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522 

  pinMode(2, OUTPUT);
  ledcSetup(RED, 200, 8);
  ledcAttachPin(2,RED);
  pinMode(3, OUTPUT);
  ledcSetup(GREEN, 200, 8);
  ledcAttachPin(3,GREEN);
  pinMode(4, OUTPUT);
  ledcSetup(BLUE, 200, 8);
  ledcAttachPin(4,BLUE);

  ledcWrite(RED,225.0);
  ledcWrite(GREEN,225.0);
  ledcWrite(BLUE,0.0);

  pinMode(AUDIO_TRANSDUCER, OUTPUT);
  ledcAttachPin(AUDIO_TRANSDUCER, AUDIO_PWM);

  Serial.println("Tap an RFID/NFC tag on the RFID-RC522 reader");
  signed_in = 0;
}
 
void loop() {
  int offset=0;

  // CODE USED WHEN RFID WORKS
  // If "new card" is present on the sensor
  if (rfid.PICC_IsNewCardPresent()){
    //If the card can be read
    if (rfid.PICC_ReadCardSerial()){
      Serial.println("RFID/NFC Tag Type: ");
      MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
      Serial.println(rfid.PICC_GetTypeName(piccType));
      
      //compare the two byte arrays
      if (signed_in == 0) {
        ledcWriteTone(AUDIO_PWM, 550);
        ledcWrite(RED,225.0);
        ledcWrite(BLUE,225.0);
        ledcWrite(GREEN,0.0);
        delay(1000);
        ledcWriteTone(AUDIO_PWM, 0);
        Serial.println("A new card has been detected. Welcome");
        //change state to signed_in:

        // Store NUID into nuidPICC array
        for (int i = 0; i < 4; i++) {
          nuidPICC[i] = rfid.uid.uidByte[i];
        }
      
        // Print tag onto Serial Monitor
        Serial.println("The NUID tag is:");
        printHex(rfid.uid.uidByte, rfid.uid.size);
        for (int i = 0; i < rfid.uid.size; i++) {
          Serial.println(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
          Serial.println(rfid.uid.uidByte[i], HEX);
        }

        char ID[100];
        offset = 0;
        for (int i = 0; i < 4; i++){
          offset += sprintf (ID + offset, "%02X ",(unsigned char)nuidPICC[i]);
        }

        //POST user to server
        Serial.println("SENDING REQUEST");
        request[0] = '\0';
        response[0] = '\0';
        char body[200]; //for body
        sprintf(body, "&token=%s&endpoint=%s", ID, tap_in); //generate body, posting temp, humidity to server
        int body_len = strlen(body); //calculate body length (for header reporting)
        offset = 0; //reset offset variable for sprintf-ing
        offset += sprintf(request + offset, "POST https://608dev-2.net/sandbox/sc/team7/server/server.py  HTTP/1.1\r\n");
        offset += sprintf(request + offset, "Host: 608dev-2.net\r\n");
        offset += sprintf(request + offset, "Content-Type: application/x-www-form-urlencoded\r\n");
        offset += sprintf(request + offset, "Content-Length: %d\r\n\r\n", body_len);
        offset += sprintf(request + offset, "%s\r\n", body);
        do_http_request("608dev-2.net", request, response, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true);
        signed_in = 1;
      } 
      else if (signed_in == 1){
        int same = 1;
          for (byte i = 0; i < 4; i++){
            if (nuidPICC[i] != rfid.uid.uidByte[i]){
              same = 0;
            }
          }
        if (same == 0){
          ledcWriteTone(AUDIO_PWM, 200);
          ledcWrite(RED,0.0);
          ledcWrite(BLUE,225.0);
          ledcWrite(GREEN,225.0);
          delay(1000);
          ledcWriteTone(AUDIO_PWM, 0);
          ledcWrite(RED,225.0);
          ledcWrite(BLUE,225.0);
          ledcWrite(GREEN,0.0);
          Serial.println("ERROR Someone is Signed in");
        } else{
          ledcWriteTone(AUDIO_PWM, 550);
          ledcWrite(RED,225.0);
          ledcWrite(BLUE,0.0);
          ledcWrite(GREEN,225.0);
          delay(1000);
          ledcWriteTone(AUDIO_PWM, 0);
          
          // Print tag onto Serial Monitor
          Serial.println("The NUID tag is:");
          printHex(rfid.uid.uidByte, rfid.uid.size);

          //Output leaving to the screen
          Serial.println("A new card has been detected. Welcome");
          Serial.println("You are now exiting. Goodbye");

          char ID[100];
          offset = 0;
          for (int i = 0; i < 4; i++){
            offset += sprintf (ID + offset, "%02X ",(unsigned char)nuidPICC[i]);
          }

          //POST user to server
          Serial.println("SENDING REQUEST");
          request[0] = '\0';
          response[0] = '\0';
          char body[200]; //for body
          sprintf(body, "&token=%s&endpoint=%s", ID, tap_out); //generate body, posting temp, humidity to server
          int body_len = strlen(body); //calculate body length (for header reporting)
          offset = 0; //reset offset variable for sprintf-ing
          offset += sprintf(request + offset, "POST https://608dev-2.net/sandbox/sc/team7/server/server.py  HTTP/1.1\r\n");
          offset += sprintf(request + offset, "Host: 608dev-2.net\r\n");
          offset += sprintf(request + offset, "Content-Type: application/x-www-form-urlencoded\r\n");
          offset += sprintf(request + offset, "Content-Length: %d\r\n\r\n", body_len);
          offset += sprintf(request + offset, "%s\r\n", body);
          do_http_request("608dev-2.net", request, response, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true);
          signed_in = 0; 
        }
      }
      // Halt PICC
      rfid.PICC_HaltA();

      // Stop encryption on PCD
      rfid.PCD_StopCrypto1();

    }
  }

}


/**
 * Helper routine to dump a byte array as hex values to Serial. 
 */
void printHex(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
  }
}

/**
 * Helper routine to dump a byte array as dec values to Serial.
 */
void printDec(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], DEC);
  }
}



/*----------------------------------
   char_append Function:
   Arguments:
      char* buff: pointer to character array which we will append a
      char c:
      uint16_t buff_size: size of buffer buff

   Return value:
      boolean: True if character appended, False if not appended (indicating buffer full)
*/
uint8_t char_append(char* buff, char c, uint16_t buff_size) {
  int len = strlen(buff);
  if (len > buff_size) return false;
  buff[len] = c;
  buff[len + 1] = '\0';
  return true;
}


/*----------------------------------
 * do_http_request Function:
 * Arguments:
 *    char* host: null-terminated char-array containing host to connect to
 *    char* request: null-terminated char-arry containing properly formatted HTTP request
 *    char* response: char-array used as output for function to contain response
 *    uint16_t response_size: size of response buffer (in bytes)
 *    uint16_t response_timeout: duration we'll wait (in ms) for a response from server
 *    uint8_t serial: used for printing debug information to terminal (true prints, false doesn't)
 * Return value:
 *    void (none)
 */
void do_http_request(char* host, char* request, char* response, uint16_t response_size, uint16_t response_timeout, uint8_t serial){
  if (client2.connect(host, 80)) { //try to connect to host on port 80
    if (serial) Serial.print(request);//Can do one-line if statements in C without curly braces
    client2.print(request);
    memset(response, 0, response_size); //Null out (0 is the value of the null terminator '\0') entire buffer
    uint32_t count = millis();
    while (client2.connected()) { //while we remain connected read out data coming back
      client2.readBytesUntil('\n',response,response_size);
      if (serial) Serial.println(response);
      if (strcmp(response,"\r")==0) { //found a blank line!
        break;
      }
      memset(response, 0, response_size);
      if (millis()-count>response_timeout) break;
    }
    memset(response, 0, response_size);  
    count = millis();
    while (client2.available()) { //read out remaining text (body of response)
      char_append(response,client2.read(),OUT_BUFFER_SIZE);
    }
    if (serial) Serial.println(response);
    client2.stop();
    if (serial) Serial.println("-----------");  
  }else{
    if (serial) Serial.println("connection failed :/");
    if (serial) Serial.println("wait 0.5 sec...");
    client2.stop();
  }
}  