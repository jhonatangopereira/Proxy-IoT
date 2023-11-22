# Projeto de IoT com Acelerômetro e Dashboard em Python

Bem-vindo ao projeto de Internet das Coisas (IoT) que utiliza um acelerômetro como sensor. Neste projeto, implementamos o código em um microcontrolador ESP (ESP8266) para coletar dados do acelerômetro MPU6050 e enviá-los por meio de um proxy para uma aplicação em Python. Os dados coletados são então exibidos em um dashboard para análise e visualização.

## Visão Geral

O projeto consiste em duas partes principais:

1. **Código do ESP com Acelerômetro:** Implementação do código no microcontrolador ESP para ler os dados do acelerômetro e enviar essas informações para um servidor proxy. O código do ESP pode ser encontrado [aqui](https://wokwi.com/projects/381844202174854145).
2. **Aplicação Python e Dashboard:** Uma aplicação em Python que atua como um servidor proxy para receber os dados do ESP. Além disso, implementamos um dashboard para visualizar e analisar os dados do acelerômetro em tempo real.

## Configuração do Ambiente

1. Clone este repositório:
   <pre><div class="bg-black rounded-md"><div class="flex items-center relative text-gray-200 bg-gray-800 gizmo:dark:bg-token-surface-primary px-4 py-2 text-xs font-sans justify-between rounded-t-md"><span>bash</span><button class="flex ml-auto gizmo:ml-0 gap-1 items-center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-sm"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 4C10.8954 4 10 4.89543 10 6H14C14 4.89543 13.1046 4 12 4ZM8.53513 4C9.22675 2.8044 10.5194 2 12 2C13.4806 2 14.7733 2.8044 15.4649 4H17C18.6569 4 20 5.34315 20 7V19C20 20.6569 18.6569 22 17 22H7C5.34315 22 4 20.6569 4 19V7C4 5.34315 5.34315 4 7 4H8.53513ZM8 6H7C6.44772 6 6 6.44772 6 7V19C6 19.5523 6.44772 20 7 20H17C17.5523 20 18 19.5523 18 19V7C18 6.44772 17.5523 6 17 6H16C16 7.10457 15.1046 8 14 8H10C8.89543 8 8 7.10457 8 6Z" fill="currentColor"></path></svg>Copy code</button></div><div class="p-4 overflow-y-auto"><code class="!whitespace-pre hljs language-bash">git clone https://github.com/seu-usuario/nome-do-repositorio.git
   </code></div></div></pre>
2. Instale as dependências da aplicação Python:
   <pre><div class="bg-black rounded-md"><div class="flex items-center relative text-gray-200 bg-gray-800 gizmo:dark:bg-token-surface-primary px-4 py-2 text-xs font-sans justify-between rounded-t-md"><span>bash</span><button class="flex ml-auto gizmo:ml-0 gap-1 items-center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-sm"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 4C10.8954 4 10 4.89543 10 6H14C14 4.89543 13.1046 4 12 4ZM8.53513 4C9.22675 2.8044 10.5194 2 12 2C13.4806 2 14.7733 2.8044 15.4649 4H17C18.6569 4 20 5.34315 20 7V19C20 20.6569 18.6569 22 17 22H7C5.34315 22 4 20.6569 4 19V7C4 5.34315 5.34315 4 7 4H8.53513ZM8 6H7C6.44772 6 6 6.44772 6 7V19C6 19.5523 6.44772 20 7 20H17C17.5523 20 18 19.5523 18 19V7C18 6.44772 17.5523 6 17 6H16C16 7.10457 15.1046 8 14 8H10C8.89543 8 8 7.10457 8 6Z" fill="currentColor"></path></svg>Copy code</button></div><div class="p-4 overflow-y-auto"><code class="!whitespace-pre hljs language-bash">pip install -r requirements.txt
   </code></div></div></pre>
3. Insira as variáveis de ambiente no arquivo _.env_.

## Executando o Projeto

1. Carregue o código do ESP no microcontrolador utilizando a plataforma de simulação fornecida [aqui](https://wokwi.com/projects/381844202174854145).
2. Execute a aplicação Python:
   ```bash
   python step_counter_dashboard.py
   ```
3. Abra o navegador e acesse o dashboard em `http://localhost:5000`.

## Funcionamento

O microcontrolador ESP lê os dados do acelerômetro e os envia para a aplicação Python por meio de uma conexão TCP. A aplicação Python se conecta ao próximo aguardando quaisquer recebimento de dados, atualizando o dashboard em tempo real.

## Estrutura do Projeto

### ESP
* `MPU6050-Device-IoT.c`: Código do ESP que lê os dados do acelerômetro e os envia para o proxy.

### Python
* `step_counter_dashboard.py`: Contém a aplicação Python que recebe os dados por proxy e executa o código para o dashboard.

## Recursos Adicionais

* [Documentação do ESP8266](https://docs.espressif.com/projects/esp8266-rtos-sdk/en/latest/)
* [Dash - Documentação](https://dash.plotly.com/)

Sinta-se à vontade para explorar o código-fonte e adaptá-lo de acordo com suas necessidades. Se tiver alguma dúvida ou sugestão, fique à vontade para entrar em contato.
