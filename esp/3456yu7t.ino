#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>
#define ANALOG_PIN A0  
#define EEPROM_SIZE 64  
#define MAX_ATTEMPTS 20 
ESP8266WebServer server(80);
struct Config {
  char ssid[32];
  char password[32];
};
Config config;
String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <title>WiFi Setup</title>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial; padding: 20px; text-align: center; }
    input, button { margin: 10px 0; padding: 10px; width: 80%%; max-width: 300px; }
  </style>
</head>
<body>
  <h2>Настройка WiFi</h2>
  <form method="post" action="/save">
    <label>SSID: <input type="text" name="ssid"></label><br>
    <label>Password: <input type="password" name="password"></label><br>
    <button type="submit">Сохранить</button>
  </form>
</body>
</html>
)rawliteral";
void setup() {
  Serial.begin(115200);
  Serial.println("\nЗапуск ESP8266...");
  EEPROM.begin(EEPROM_SIZE);
   EEPROM.get(0, config);
   Serial.print("Сохранённый SSID: ");
  Serial.println(config.ssid);
  Serial.print("Сохранённый пароль: ");
  Serial.println(config.password);
  if (strlen(config.ssid) > 0) {
    Serial.println("Попытка подключения к сохранённой сети...");
    WiFi.begin(config.ssid, config.password);
       int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < MAX_ATTEMPTS) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n❌ Не удалось подключиться к Wi-Fi! Запуск точки доступа...");
    WiFi.mode(WIFI_AP);
    WiFi.softAP("MicSetup", "12345678");
    Serial.println("✅ Точка доступа 'MicSetup' создана.");
    Serial.println("🌐 Откройте браузер и перейдите на http://192.168.4.1/");
    server.on("/", HTTP_GET, handleRoot);
    server.on("/save", HTTP_POST, handleSave);
  } else {
    Serial.println("\n✅ Подключено к Wi-Fi!");
    Serial.print("🌍 IP-адрес: ");
    Serial.println(WiFi.localIP());
    server.on("/data", HTTP_GET, handleData);
  }
  server.begin();
  Serial.println("📡 Веб-сервер запущен!");
}
void loop() {
  server.handleClient();
}
void handleRoot() {
  server.send(200, "text/html", html);
}
void handleSave() {
  if (server.hasArg("ssid") && server.hasArg("password")) {
    String newSSID = server.arg("ssid");
    String newPassword = server.arg("password");

    Serial.println("\n💾 Сохранение Wi-Fi параметров...");
    Serial.print("🔗 Новый SSID: ");
    Serial.println(newSSID);
    memset(&config, 0, sizeof(Config));
    strncpy(config.ssid, newSSID.c_str(), sizeof(config.ssid) - 1);
    strncpy(config.password, newPassword.c_str(), sizeof(config.password) - 1);
    EEPROM.put(0, config);
    if (!EEPROM.commit()) {
      Serial.println("❌ Ошибка сохранения в EEPROM!");
    } else {
      Serial.println("✅ Данные успешно сохранены!");
    }
    String response = R"rawliteral(
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta http-equiv="refresh" content="3;url=/" />
      <title>Сохранение</title>
      <style>body { font-family: Arial; text-align: center; padding: 50px; }</style>
    </head>
    <body>
      <h2>Данные сохранены!</h2>
      <p>Перезагрузка устройства...</p>
    </body>
    </html>
    )rawliteral";
    server.send(200, "text/html", response);
    delay(2000);
    ESP.restart();
  } else {
    server.send(400, "text/plain", "Ошибка: Не все параметры переданы.");
  }
}
void handleData() {
  int micValue = analogRead(ANALOG_PIN);
  server.send(200, "text/plain", String(micValue));
}

