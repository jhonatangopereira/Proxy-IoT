/*
    Projeto: MPU6050-Device-IoT
    Descrição: Código para o ESP32 que realiza a conexão com o servidor TCP e envia dados com destino para a aplicação IoT.
    Autor: Jhonatan Guilherme Oliveira Pereira.
    Data de atualização: 19/11/2023.
*/

// bibliotecas
#include <stdio.h>
#include <string.h>
// bibliotecas do ESP32
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event_loop.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"
#include "nvs_flash.h"
//bibliotecas do sensor MPU6050
#include "driver/i2c.h"
// constantes de acesso do servidor TCP
#define SSID "Wokwi-GUEST"
#define PASSPHARSE ""
#define TCPServerIP "159.203.79.141"
#define PORT 50000
// constante de identificação do sensor MPU6050
#define PIN_SDA GPIO_NUM_2
#define PIN_SCL GPIO_NUM_4
#define I2C_ADDRESS 0x68

#define MPU6050_ACCEL_XOUT_H 0x3B
#define MPU6050_PWR_MGMT_1 0x6B

#undef ESP_ERROR_CHECK
#define ESP_ERROR_CHECK(x) do { esp_err_t rc = (x); if (rc != ESP_OK) { ESP_LOGE(ERROR_TAG, "esp_err_t = %d", rc); assert(0 && #x);} } while(0);

// variáveis globais
static const char *access_id = "201921250012";
static const char *CONFIG_TAG = "CONFIG";
static const char *ERROR_TAG = "ERROR";
static const char *SENSOR_TAG = "MPU6050";
static const char *TCP_TAG = "TCP";
// variável global para o socket
short int sock;

static EventGroupHandle_t wifi_event_group;
const int CONNECTED_BIT = BIT0;
// variáveis globais para o sensor MPU6050
short int accel_x, accel_y, accel_z;


// declaração de funções
void app_main(void);
void setup(void);
static esp_err_t event_handler(void *ctx, system_event_t *event);
void config_wifi(void);
static void initialize_wifi(void);
void connect_proxy(void);
void init_mpu6050_sensor(gpio_num_t scl, gpio_num_t sda);
void read_mpu6050_sensor(void);
void send_sensor_data_to_proxy(void *pvParam);
void send_alive_to_proxy(void *pvParam);

// Função principal
void app_main(void) {
  printf("%s >> app_main\n", CONFIG_TAG);
  // Inicializa o ESP32
  setup();
  // Inicializa o sensor MPU6050
  init_mpu6050_sensor(PIN_SCL, PIN_SDA);
  // Inicializa conexão TCP com o servidor
  connect_proxy();
  // Cria a tarefa que lê os dados do sensor MPU6050
  xTaskCreate(&read_mpu6050_sensor, "read_mpu6050_sensor", 4096, NULL, 5, NULL);
  // Cria a tarefa que envia os dados para o servidor TCP
  // xTaskCreate(&send_sensor_data_to_proxy, "send_sensor_data_to_proxy", 4096, NULL, 5, NULL);
  // Cria a tarefa que envia "alive" para o servidor TCP
  // xTaskCreate(&send_alive_to_proxy, "send_alive_to_proxy", 4096, NULL, 5, NULL);
}

// Função de configuração
void setup(void) {
  printf("%s >> setup\n", CONFIG_TAG);
  ESP_ERROR_CHECK(esp_event_loop_init(event_handler, NULL));
  wifi_event_group = xEventGroupCreate();
  esp_err_t ret = nvs_flash_init();
  if (ret == ESP_ERR_NVS_NO_FREE_PAGES) {
    ESP_ERROR_CHECK(nvs_flash_erase());
    ret = nvs_flash_init();
  }
  ESP_ERROR_CHECK(ret);
  initialize_wifi();
}

/* Conexão WiFi */
// Função de tratamento de eventos do WiFi
static esp_err_t event_handler(void *ctx, system_event_t *event) {
  switch(event->event_id) {
  case SYSTEM_EVENT_STA_START:
    config_wifi();
    break;
  case SYSTEM_EVENT_STA_GOT_IP:
    xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
    break;
  case SYSTEM_EVENT_STA_DISCONNECTED:
    esp_wifi_connect();
    xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
    break;
  default:
    break;
  }
  return ESP_OK;
}

// Função que conecta o ESP32 ao WiFi
void config_wifi(void) {
  wifi_config_t cfg = {
    .sta = {
      .ssid = SSID,
      .password = PASSPHARSE,
    }
  };
  ESP_ERROR_CHECK(esp_wifi_disconnect());
  ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_STA, &cfg));
  ESP_ERROR_CHECK(esp_wifi_connect());
}

// Função que inicializa o WiFi
static void initialize_wifi(void) {
  esp_log_level_set("wifi", ESP_LOG_NONE); // disable wifi driver logging
  tcpip_adapter_init();
  wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
  ESP_ERROR_CHECK(esp_wifi_init(&cfg));
  ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
  ESP_ERROR_CHECK(esp_wifi_start());
}

void connect_proxy(void) {
  printf("%s >> connect_proxy\n", TCP_TAG);
  char host_ip[] = TCPServerIP;
  // int addr_family = 0;
  // int ip_protocol = 0;
  struct sockaddr_in tcpServerAddr;
  tcpServerAddr.sin_addr.s_addr = inet_addr(TCPServerIP);
  tcpServerAddr.sin_family = AF_INET;
  tcpServerAddr.sin_port = htons(PORT);
  int s, r;
  
  xEventGroupWaitBits(wifi_event_group,CONNECTED_BIT,false,true,portMAX_DELAY);

  int sock = socket(AF_INET, SOCK_STREAM, 0);

  if (sock < 0) {
    ESP_LOGE(SENSOR_TAG, "Unable to create socket: errno %d", errno);
    return ;
  }
  ESP_LOGI(TCP_TAG, "Socket created, connecting to %s:%d", host_ip, PORT);

  int err = connect(sock, (struct sockaddr *)&tcpServerAddr, sizeof(tcpServerAddr));
  if (err != 0) {
    ESP_LOGE(TCP_TAG, "Socket unable to connect: errno %d", errno);
    return;
  }
  
  ESP_LOGI(TCP_TAG, "Successfully connected.");

  // Try to login with access_id
  err = send(sock, access_id, strlen(access_id), 0);
  if (err < 0) {
    ESP_LOGE(TCP_TAG, "Error occurred during sending: errno %d", errno);
  }

  char rx_buffer[128];
  int len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
  if (len < 0) {
    // Erro ao receber dados
    ESP_LOGE(TCP_TAG, "recv failed: errno %d", errno);
  } else {
    rx_buffer[len] = 0; // Receber dado de retorno
    if (strcmp(rx_buffer,"ok") == 0)
      printf("Login realizado com sucesso!\n");
    else
      printf("Falha no login!\n");
  }
}

/* Sensor MPU6050 */
// Função que inicializa o sensor MPU6050
void init_mpu6050_sensor(gpio_num_t scl, gpio_num_t sda) {
  printf("%s >> init_mpu6050_sensor\n", SENSOR_TAG);
  // Inicializa o I2C, que é o protocolo de comunicação do MPU6050
	i2c_config_t conf;
	conf.mode = I2C_MODE_MASTER;
	conf.sda_io_num = PIN_SDA;
	conf.scl_io_num = PIN_SCL;
	conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
	conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
	conf.master.clk_speed = 100000;
  conf.clk_flags = 0;
	ESP_ERROR_CHECK(i2c_param_config(I2C_NUM_0, &conf));
	ESP_ERROR_CHECK(i2c_driver_install(I2C_NUM_0, I2C_MODE_MASTER, 0, 0, 0));
}

// Função que lê os dados do sensor MPU6050
void read_mpu6050_sensor(void) {
  printf("%s >> read_mpu6050_sensor\n", SENSOR_TAG);
  i2c_cmd_handle_t cmd;
	vTaskDelay(200 / portTICK_PERIOD_MS);

	cmd = i2c_cmd_link_create();
	ESP_ERROR_CHECK(i2c_master_start(cmd));
	ESP_ERROR_CHECK(i2c_master_write_byte(cmd, (I2C_ADDRESS << 1) | I2C_MASTER_WRITE, 1));
	i2c_master_write_byte(cmd, MPU6050_ACCEL_XOUT_H, 1);
	ESP_ERROR_CHECK(i2c_master_stop(cmd));
	i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
	i2c_cmd_link_delete(cmd);

	cmd = i2c_cmd_link_create();
	ESP_ERROR_CHECK(i2c_master_start(cmd));
	ESP_ERROR_CHECK(i2c_master_write_byte(cmd, (I2C_ADDRESS << 1) | I2C_MASTER_WRITE, 1));
	i2c_master_write_byte(cmd, MPU6050_PWR_MGMT_1, 1);
	i2c_master_write_byte(cmd, 0, 1);
	ESP_ERROR_CHECK(i2c_master_stop(cmd));
	i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
	i2c_cmd_link_delete(cmd);

	uint8_t data[14];
  while (1) {
    // Tell the MPU6050 to position the internal register pointer to register MPU6050_ACCEL_XOUT_H.
    cmd = i2c_cmd_link_create();
    ESP_ERROR_CHECK(i2c_master_start(cmd));
    ESP_ERROR_CHECK(i2c_master_write_byte(cmd, (I2C_ADDRESS << 1) | I2C_MASTER_WRITE, 1));
    ESP_ERROR_CHECK(i2c_master_write_byte(cmd, MPU6050_ACCEL_XOUT_H, 1));
    ESP_ERROR_CHECK(i2c_master_stop(cmd));
    ESP_ERROR_CHECK(i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS));
    i2c_cmd_link_delete(cmd);

    cmd = i2c_cmd_link_create();
    ESP_ERROR_CHECK(i2c_master_start(cmd));
    ESP_ERROR_CHECK(i2c_master_write_byte(cmd, (I2C_ADDRESS << 1) | I2C_MASTER_READ, 1));

    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data,   0));
    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data + 1, 0));
    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data + 2, 0));
    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data + 3, 0));
    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data + 4, 0));
    ESP_ERROR_CHECK(i2c_master_read_byte(cmd, data + 5, 1));

    // i2c_master_read(cmd, data, sizeof(data), 1);
    ESP_ERROR_CHECK(i2c_master_stop(cmd));
    ESP_ERROR_CHECK(i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS));
    i2c_cmd_link_delete(cmd);

    accel_x = (data[0] << 8) | data[1];
    accel_y = (data[2] << 8) | data[3];
    accel_z = (data[4] << 8) | data[5];
    printf("%s >> accel_x: %d, accel_y: %d, accel_z: %d\n", SENSOR_TAG, accel_x, accel_y, accel_z);
    // delay de 1 segundo
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

/* Conexão TCP com Proxy */
// Função que envia dados para o servidor TCP
void send_sensor_data_to_proxy(void *pvParam) {
  printf("%s >> send_sensor_data_to_proxy\n", TCP_TAG);

  // Envia dados para o servidor
  uint8_t value = 10;
  char tx_buffer[128];
  sprintf(tx_buffer, "%hhu", value);
  printf("txbuffer: %s\n", tx_buffer);
  printf("value: %d\n", value);
  printf("sock: %d\n", sock);
  int err = send(sock, tx_buffer, strlen(tx_buffer), 0);
  if (err < 0) { ESP_LOGE(TCP_TAG, "Error occurred during sending: errno %d", errno); }

  vTaskDelay(1000 / portTICK_PERIOD_MS);

  if (sock != -1) {
    ESP_LOGE(TCP_TAG, "Shutting down socket...");
    shutdown(sock, 0);
    close(sock);
  }
  vTaskDelete(NULL);
}

void send_alive_to_proxy(void *pvParam) {
  printf("%s >> send_alive_to_proxy\n", TCP_TAG);
  // delay de 10 segundos
  vTaskDelay(10000 / portTICK_PERIOD_MS);
}
