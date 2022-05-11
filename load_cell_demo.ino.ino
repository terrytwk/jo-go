#include "HX711.h"
#include <WiFi.h>
#include <ArduinoJson.h>

#define DOUT  3
#define CLK  4

HX711 scale;
float weight; 
float new_weight;
int num_items = 0;
long timer = millis();
bool check_timer = false;

int offset=0;
char json_body[200];

char network[] = "MIT";
char password[] = "";
uint8_t scanning = 0;
uint8_t channel = 1; //network channel on 2.4 GHz

//Some constants and some resources:
const int RESPONSE_TIMEOUT = 6000; //ms to wait for response from host
const int GETTING_PERIOD = 2000; //periodicity of getting a number fact.
const int BUTTON_TIMEOUT = 1000; //button timeout in milliseconds
const uint16_t IN_BUFFER_SIZE = 1000; //size of buffer to hold HTTP request
const uint16_t OUT_BUFFER_SIZE = 10000; //size of buffer to hold HTTP response
char request_buffer[IN_BUFFER_SIZE]; //char array buffer to hold HTTP request
char response_buffer[OUT_BUFFER_SIZE]; //char array buffer to hold HTTP response

StaticJsonDocument<200> doc;

void setup() {
  Serial.begin(115200);

  WiFi.begin(network, password);

  uint8_t count = 0; //count used for Wifi check times
  Serial.print("Attempting to connect to ");
  Serial.println(network);
  while (WiFi.status() != WL_CONNECTED && count < 12) {
    delay(500);
    Serial.print(".");
    count++;
  }
  delay(2000);
  if (WiFi.isConnected()) { //if we connected then print our IP, Mac, and SSID we're on
    Serial.println("CONNECTED!");
    Serial.println(WiFi.localIP().toString() + " (" + WiFi.macAddress() + ") (" + WiFi.SSID() + ")");
    delay(500);
  } else { //if we failed to connect just Try again.
    Serial.println("Failed to Connect :/  Going to restart");
    Serial.println(WiFi.status());
    ESP.restart(); // restart the ESP (proper way)
  }
  
  scale.begin(DOUT, CLK);

  scale.set_scale();
  // scale.tare();
  weight = scale.get_units();
  new_weight = weight;
  Serial.print("Weight: ");
  Serial.println(weight);

  Serial.println("GET REQUEST MADE HERE");
  get_info();
  num_buttons = 0;
  
  
  Serial.println("POST REQUEST MADE HERE");
  post_info();

  Serial.println("num buttons in set up: ");
  Serial.println(num_buttons);
}

void loop() {
  
  new_weight = scale.get_units();
  
  Serial.print("num_buttons: ");
  Serial.println(num_buttons);

  Serial.println("START");
  Serial.println(new_weight - weight);
  Serial.println(new_weight);
  Serial.println(weight);
  Serial.println("FINISH");
  
  if ((new_weight - weight >= 20000) && (new_weight - weight <= 70000)) {

    // Serial.print("new weight - ");
    // Serial.println(new_weight);

    // Serial.print("weight - ");
    // Serial.println(weight);

    Serial.println(new_weight);
    Serial.println(weight);

    num_items =  num_items + 1;
    
    Serial.print("num_buttons: ");
    Serial.print(num_items);
    Serial.print(" weight: ");
    Serial.print(weight);
    Serial.print(" new weight: ");
    Serial.println(new_weight);

    post_info();
    weight = new_weight;

    timer = millis();
    while (millis() - timer < 3000);

    weight = scale.get_units();
    new_weight = scale.get_units();
  }
  else if ((new_weight - weight <= -20000) && (new_weight - weight >= -70000)) {
    // Serial.print("new weight - ");
    Serial.println(new_weight);
    Serial.println(weight);
    // Serial.print("weight - ");
    

    num_items = num_items - 1;

    // Serial.print("num_buttons: ");
    // Serial.print(num_buttons);
    // Serial.print(" weight: ");
    // Serial.print(weight);
    // Serial.print(" new weight: ");
    // Serial.println(new_weight);

    post_info();
    weight = new_weight;

    timer = millis();
    while (millis() - timer < 3000);

    weight = scale.get_units();
    new_weight = scale.get_units();
  }
}

void post_info() {
  // https://608dev-2.net/sandbox/sc/team7/server/server.py with a body of endpoint="items", item_name=<item>, and item_count=<current_item_count>
  memset(json_body, 0, 200);
  
  sprintf(json_body, "endpoint=%s&item_name=%s&item_count=%d", "items", "LCD", num_items);

  offset = 0;
  offset += sprintf(request_buffer, "POST https://608dev-2.net/sandbox/sc/team7/server/server.py HTTP/1.1\r\n");
  offset += sprintf(request_buffer + offset, "Host: 608dev-2.net\r\n");
  offset += sprintf(request_buffer + offset, "Content-Type: application/x-www-form-urlencoded\r\n");
  offset += sprintf(request_buffer + offset, "cache-control: no-cache\r\n");
  offset += sprintf(request_buffer + offset, "Content-Length: %d\r\n\r\n", strlen(json_body));
  offset += sprintf(request_buffer + offset, "%s\r\n", json_body);  

  do_http_request("608dev-2.net", request_buffer, response_buffer, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true); 
}

void get_info() {
  sprintf(request_buffer, "GET https://608dev-2.net/sandbox/sc/team7/server/server.py?endpoint=items&item=LCD HTTP/1.1\r\n");
  //  will return a JSON of this format {"status": 200, "message": "GET request successful.", "<item_name>": <current_number>}

  strcat(request_buffer, "Host: 608dev-2.net\r\n");
  strcat(request_buffer, "\r\n");
  do_http_request("608dev-2.net", request_buffer, response_buffer, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true);

  deserializeJson(doc, response_buffer);

  JsonVariant a = doc["LCD"];
  auto b = a.as<int>();
  int number = b;
  num_items = number;  
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
  WiFiClient client2;
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

uint8_t char_append(char* buff, char c, uint16_t buff_size) {
        int len = strlen(buff);
        if (len>buff_size) return false;
        buff[len] = c;
        buff[len+1] = '\0';
        return true;
}