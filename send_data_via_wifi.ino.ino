// Import required libraries
#include "ESP8266WiFi.h"
#include <aREST.h>
#include "DHT.h"

// DHT11 sensor pins
#define DHTPIN D4
#define DHTPIN1 D5
#define DHTTYPE DHT11

// Create aREST instance
aREST rest = aREST();

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE, 15);
DHT dht1(DHTPIN1, DHTTYPE, 15);

// WiFi parameters
const char* ssid = "No-wifi";
const char* password = "Hoi lam gi ???";

// The port to listen for incoming TCP connections 
#define LISTEN_PORT           80

// Create an instance of the server
WiFiServer server(LISTEN_PORT);

// Variables to be exposed to the API
int temperature=0;
int humidity=0;

void setup(void)
{  
  // Start Serial
  Serial.begin(115200);
  
  // Init DHT 
  dht.begin();
  dht1.begin();
  
  // Init variables and expose them to REST API
  rest.variable("temperature",&temperature);
  rest.variable("humidity",&humidity);
    
  // Give name and ID to device
  rest.set_id("1");
  rest.set_name("sensor_module");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
 
  // Start the server
  server.begin();
  Serial.println("Server started");
  
  // Print the IP address
  Serial.println(WiFi.localIP());
  
}

void loop() {
  
  // Reading temperature and humidity
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  temperature1 = dht1.readTemperature();
  humidity1 = dht1.readHumidity();
  
  // Handle REST calls
  WiFiClient client = server.available();
  if (!client) {
    return;
  }
  while(!client.available()){
    delay(1);
  }
  rest.handle(client);

//  sleep(5000);
}