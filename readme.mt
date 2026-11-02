python.exe treinamento.py
Comandinho para rodar o treinamento

## Configuração do acesso externo com Cloudflare Tunnel (Windows)

### 1. Instalação do Cloudflare Tunnel

1. Acesse a página oficial de downloads:
   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

2. Baixe a versão `Windows 64-bit`.

3. Salve o arquivo na pasta `Downloads`.

4. Abra o CMD e acesse a pasta:

```cmd
cd %USERPROFILE%\Downloads
```

5. Verifique se o executável está presente:

```cmd
dir cloudflared*
```

6. Teste a instalação:

```cmd
cloudflared-windows-amd64.exe --version
```

### 2. Inicialização do projeto Django

1. Abra um terminal na pasta raiz do projeto, onde está localizado o arquivo `manage.py`.

2. Ative o ambiente virtual, caso exista:

```cmd
.venv\Scripts\activate
```

3. Inicie o servidor Django:

```cmd
python manage.py runserver 0.0.0.0:8000
```

4. Verifique se o sistema está funcionando localmente:

```text
http://127.0.0.1:8000
```

Mantenha esse terminal aberto.

### 3. Configuração do Cloudflare Tunnel

1. Abra uma segunda janela do CMD.

2. Acesse a pasta onde o executável do Cloudflare foi baixado:

```cmd
cd %USERPROFILE%\Downloads
```

3. Execute o comando:

```cmd
cloudflared-windows-amd64.exe tunnel --url http://localhost:8000
```

4. Aguarde a inicialização do túnel.

5. Procure no terminal a mensagem `Your quick Tunnel has been created!`.

6. Copie o endereço gerado, que terá o formato:

```text
https://nome-aleatorio.trycloudflare.com
```

### 4. Acesso ao sistema

O endereço gerado poderá ser acessado por qualquer pessoa com o link, desde que o computador responsável pela execução do projeto permaneça ligado e conectado à internet.

Para manter o acesso disponível, os dois processos precisam continuar ativos:

- Servidor Django na porta 8000.
- Cloudflare Tunnel conectado ao servidor Django.

### 5. Encerramento

Para encerrar o acesso externo, pressione `CTRL + C` no terminal do Cloudflare Tunnel.

Para encerrar o servidor Django, pressione `CTRL + C` no terminal correspondente.

### 6. Observações

- O Cloudflare Quick Tunnel não exige cadastro ou configuração de domínio.
- O endereço gerado é temporário e pode mudar a cada inicialização.
- O computador local executa todas as operações do sistema, incluindo as inferências dos modelos YOLO.
- O desempenho depende dos recursos de hardware disponíveis.
- Essa configuração é destinada a testes e demonstrações, não sendo uma hospedagem permanente.
- Antes de disponibilizar o sistema publicamente, revise as configurações de segurança do Django.