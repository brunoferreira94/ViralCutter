# ViralCutter

[![Discord](https://dcbadge.limes.pink/api/server/tAdPHFAbud)](https://discord.gg/tAdPHFAbud)

**Alternativa open-source 100% gratuita, local e ilimitada ao Opus Clip**  
Transforme vídeos longos do YouTube em shorts virais otimizados para TikTok, Instagram Reels e YouTube Shorts – com IA de ponta, legendas dinâmicas, _face tracking_ preciso e tradução automática. Tudo rodando na sua máquina.

[![Stars](https://img.shields.io/github/stars/RafaelGodoyEbert/ViralCutter?style=social)](https://github.com/RafaelGodoyEbert/ViralCutter/stargazers)
[![Forks](https://img.shields.io/github/forks/RafaelGodoyEbert/ViralCutter?style=social)](https://github.com/RafaelGodoyEbert/ViralCutter/network/members)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1UZKzeqjIeEyvq9nPx7s_4mU6xlkZQn_R?usp=sharing)

[English](README_en.md) • [Português](README.md)

## Por que ViralCutter é um "Game Changer"?

Esqueça assinaturas caras e limites de minutos. O ViralCutter oferece poder ilimitado no seu hardware.

| Feature           | ViralCutter (Open-Source)                                                                 | Opus Clip / Klap / Munch (SaaS) |
| :---------------- | :---------------------------------------------------------------------------------------- | :------------------------------ |
| **Preço**         | **Gratuito e Ilimitado**                                                                  | $20–$100/mês + limites de min.  |
| **Privacidade**   | **100% Local** (Seus dados não saem do PC)                                                | Upload para nuvem de terceiros  |
| **IA & LLM**      | **Flexível**: Gemini (Free), GPT-4, **GitHub Copilot (Claude)**, **Local GGUF (Offline)** | Apenas o que eles oferecem      |
| **Face Tracking** | **Split Screen (2 faces)**, Active Speaker (Exp.), Auto                                   | Básico ou pago extra            |
| **Tradução**      | **Sim** (Traduza legendas p/ 10+ línguas)                                                 | Recursos limitados              |
| **Edição**        | **Exporta XML para Premiere Pro** (Beta)                                                  | Editor web limitado             |
| **Watermark**     | **ZERO**                                                                                  | Sim (nos planos free)           |

**Resultados profissionais, privacidade total e custo zero.**

## Funcionalidades Principais 🚀

- 🤖 **Corte Viral com IA**: Identifica automaticamente os ganchos e momentos mais engajadores usando **Gemini**, **GitHub Copilot (Claude)**, **GPT-4** ou **LLMs Locais (Llama 3, DeepSeek, etc)**.
- 🗣️ **Transcrição Ultra-Precisa**: Baseado em **WhisperX** com aceleração via GPU para legendas perfeitas.
- 🎨 **Legendas Dinâmicas**: Estilo "Hormozi" com highlight palavra por palavra, cores vibrantes, emojis e total customização.
- 🎥 **Direção de Câmera Automática**:
  - **Auto-Crop 9:16**: Transforma horizontal em vertical mantendo o foco.
  - **Split Screen Inteligente**: Detecta 2 pessoas conversando e divide a tela automaticamente.
  - **Active Speaker (Experimental)**: A câmera corta para quem está falando.
- 🌍 **Tradução de Vídeo**: Gere legendas traduzidas automaticamente (ex: Vídeo em Inglês -> Legenda em Português).
- 💾 **Qualidade & Controle**: Escolha a resolução (até 4K/Best), formate a saída e salve configurações de processamento.
- ⚡ **Performance**: Transcrição com "slicing" (processa 1x, corta N vezes) e suporte a instalação ultra-rápida via `uv`.
- 🖥️ **Interface Moderna**: WebUI em Gradio, Modo Escuro, Galeria de Projetos e Editor de Legendas integrado.

## Interface Web (Inspirada no Opus Clip)

![WebUI Home](https://github.com/user-attachments/assets/ba147149-fc5f-48fc-a03c-fc86b5dc0568)
_Painel de controle intuitivo com ajustes finos de IA e renderização._

![WebUi Library](https://github.com/user-attachments/assets/b0204e4b-0e5d-4ee4-b7b4-cac044b76c24)
_Biblioteca: Galeria estilo OpusClip e controles intuitivos_

## Instalação Local (Super Rápida ⚡)

### Pré-requisitos (Instalação "do zero")

Para rodar o ViralCutter em um computador novo, você precisa instalar os seguintes programas essenciais:

1. **Ferramentas de Build do Visual Studio (C++ Build Tools)**
   Necessário para compilar o `insightface` e evitar erros "Cpp/Visual Studio".
   - Baixe o [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
   - Abra o instalador e marque **"Desenvolvimento para Desktop com C++"** (_Desktop development with C++_).
   - Certifique-se de que _Windows 10/11 SDK_ e _MSVC v143 - VS 2022 C++_ estejam marcados à direita e instale. Reinicie o PC se necessário.

2. **Python (3.10.x ou 3.11.x recomendados)**
   - Baixe em [python.org/downloads](https://www.python.org/downloads/).
   - ⚠️ **MUITO IMPORTANTE:** Na primeira tela de instalação, marque a caixa **"Add Python to PATH"** no rodapé antes de clicar em instalar.

3. **FFmpeg** (Processamento de áudio/vídeo)
   - A forma mais rápida no Windows é abrir o terminal (PowerShell) como Administrador e digitar:
     `winget install ffmpeg`
   - Reinicie o terminal e digite `ffmpeg -version` para checar se instalou corretamente.

4. **Drivers da Placa de Vídeo (NVIDIA)**
   - Mantenha os drivers atualizados (via GeForce Experience ou site oficial) para usar a aceleração CUDA 12.4+.
   - **GPU NVIDIA** é fortemente recomendada para velocidade e IAs locais.

---

### Passo a Passo da Instalação

1. **Instale as dependências via Script**
   Acesse a pasta do ViralCutter e escolha **um dos instaladores** abaixo com duplo clique:
   - `install_dependencies.bat`: Instalação **padrão** (Recomendada). Mais rápida e à prova de falhas. Usa IAs como Gemini (Grátis) e GPT-4 pela internet.
   - `install_dependencies_advanced_LocalLLM.bat`: Instalação **avançada**. Dedicada para quem quer rodar IAs 100% offline no hardware (Llama 3, etc). Exige placa de vídeo boa e as ferramentas _C++ Build Tools_.

   _(Ambos usam o gerenciador `uv` para configurar tudo automaticamente)._

1. **Configurar IA (Opcional)**

- **Gemini (Recomendado/Free)**: Adicione sua chave em `api_config.json`.
- **GitHub Copilot (SDK oficial)**: Use OAuth App no WebUI (Start/Finish login) ou informe token compatível com Copilot SDK na seção `copilot` do `api_config.json`.
- **Local (GGUF)**: Baixe seus modelos `.gguf` favoritos e coloque na pasta `models/`. O ViralCutter irá detectá-los automaticamente.

1. **Rodar**
   - Duplo clique em `run_webui.bat` para abrir a interface no navegador.
   - Ou use `python main_improved.py` para a versão CLI.

## Ambiente Local com venv e `.env`

Se você quer manter as variáveis secretas fora do repositório e isolar o Python localmente:

1. No Windows, execute:

```bat
setup_venv.bat
```

1. Ative o ambiente virtual:

```bat
.venv\Scripts\activate
```

1. Copie o exemplo de variáveis locais:

```bat
copy .env.example .env
```

1. Preencha valores como:
   - `COPILOT_GITHUB_TOKEN`
   - `GITHUB_TOKEN` / `GH_TOKEN`
   - `COPILOT_OAUTH_CLIENT_ID`
   - `COPILOT_OAUTH_CLIENT_SECRET`

O projeto carrega automaticamente `.env` quando existe.

## GitHub Copilot SDK no ViralCutter

A integração usa cliente oficial `github-copilot-sdk` com bridge dedicado em Python.

### Setup rápido (5 minutos)

1. Configure as variáveis de OAuth App (recomendado para WebUI):

- `COPILOT_OAUTH_CLIENT_ID`
- `COPILOT_OAUTH_CLIENT_SECRET` (quando aplicável)

1. Abra o WebUI (`run_webui.bat` ou `python webui/app.py`)

- Selecione **GitHub Copilot** no backend de IA
- Clique em **Start Copilot OAuth Login** e autorize no GitHub
- Clique em **Finish Copilot OAuth Login** para salvar o token

1. Escolha um modelo compatível do Copilot SDK e processe normalmente.

Também é possível configurar pelo `api_config.json`:

```json
"copilot": {
  "github_token": "gho_ou_ghu_SEU_TOKEN_AQUI",
  "model": "gpt-4.1",
  "chunk_size": 10000
}
```

### Uso via CLI

```bash
python main_improved.py --ai-backend copilot --api-key gho_ou_ghu_SEU_TOKEN_AQUI --ai-model-name gpt-4.1
```

### Modelos

Use os modelos habilitados pela sua conta Copilot SDK (exemplo: `gpt-4.1`).

### Troubleshooting (Copilot)

- **401 / token inválido ou expirado**:
  - Gere um novo token em [github.com/settings/tokens](https://github.com/settings/tokens)
- **403 / permissões insuficientes**:
  - Gere novo token OAuth/fine-grained compatível com Copilot SDK
- **429 / rate limit**:
  - Aguarde alguns minutos; o sistema já usa retry com exponential backoff
- **Falha no bridge do SDK**:
  - Verifique `pip install -r requirements.txt` e se `github-copilot-sdk` está instalado
- **OAuth não finaliza no WebUI**:
  - Verifique `COPILOT_OAUTH_CLIENT_ID` e `COPILOT_OAUTH_CLIENT_SECRET`

### Status da implementação Copilot

- ✅ Provider dedicado (`scripts/github_copilot_provider.py`)
- ✅ Integração no pipeline principal (`scripts/create_viral_segments.py`)
- ✅ Integração WebUI com seleção dinâmica de backend/modelo
- ✅ Chaves i18n adicionadas (EN + PT-BR)
- ✅ Bridge dedicado oficial (`scripts/copilot_sdk_bridge.py`)
- ✅ Compatibilidade retroativa mantida para todos os backends existentes

### Verificação rápida da integração

```bash
python -c "import copilot; print('OK copilot-sdk')"
python -m py_compile scripts/copilot_sdk_bridge.py scripts/github_copilot_provider.py scripts/create_viral_segments.py

python main_improved.py --ai-backend gemini
```

Documentação técnica detalhada:

- `COPILOT_QUICKSTART.md`
- `IMPLEMENTATION_COPILOT.md`
- `COPILOT_IMPLEMENTATION_CHECKLIST.md`

## Docker (Windows, macOS e Linux)

Se você prefere setup reproduzível e OS agnóstico, use os artefatos Docker oficiais:

- `Dockerfile` (CPU, padrão)
- `Dockerfile.gpu` (NVIDIA GPU, opcional)
- `docker-compose.yml` (WebUI/CLI com perfis)

### Pré-requisitos

- Docker Engine + Docker Compose Plugin (`docker compose`)
- Para GPU: NVIDIA Driver + NVIDIA Container Toolkit configurados no host

### 1) Rodar WebUI (CPU)

```bash
docker compose --profile webui up --build webui
```

Abra: `http://localhost:7860`

### 2) Rodar CLI (CPU)

```bash
docker compose --profile cli run --rm cli --help
```

Exemplo com URL:

```bash
docker compose --profile cli run --rm cli --url "https://www.youtube.com/watch?v=VIDEO_ID" --segments 3 --viral
```

### 3) Rodar WebUI (GPU NVIDIA)

```bash
docker compose --profile webui-gpu up --build webui-gpu
```

### 4) Rodar CLI (GPU NVIDIA)

```bash
docker compose --profile cli-gpu run --rm cli-gpu --help
```

### Nota sobre GPUs e compatibilidade do Docker Compose

Algumas versões mais antigas do plugin `docker compose` validam a chave `gpus` no arquivo principal e podem falhar com um erro do tipo "Additional property gpus is not allowed". Para compatibilidade com máquinas que não têm a versão mais recente do Compose, o repositório inclui um arquivo de override opcional:

- `docker-compose.gpu.yml` — contém apenas a configuração `gpus: all` para os serviços GPU.

Uso recomendado:

Sem GPU (modo padrão):
```bash
docker compose --profile cli run --rm cli --help
```

Com GPU (use o override):
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml --profile cli-gpu run --rm cli-gpu --help
```

Se preferir atualizar o `docker compose` no Linux (Debian/Ubuntu), instale/atualize o plugin oficial:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl restart docker
docker compose version
```

Nota rápida para zsh: quando usar a linha que baixa a chave GPG do repositório Docker, prefira separar em duas etapas para evitar erros de parsing no zsh:

```bash
. /etc/os-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/$ID/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```


### Volumes persistentes

O `docker-compose.yml` já monta automaticamente:

- `./VIRALS` -> `/app/VIRALS`
- `./models` -> `/app/models`
- `./api_config.json` -> `/app/api_config.json`
- `./prompt.txt` -> `/app/prompt.txt`

Isso permite manter saídas, modelos e configurações entre execuções sem rebuild da imagem.

### Migração do fluxo `.bat` para Docker

- `run_webui.bat` -> `docker compose --profile webui up --build webui`
- `run.bat` (CLI) -> `docker compose --profile cli run --rm cli ...args...`

### Troubleshooting rápido

- Porta `7860` ocupada:
  - Altere o mapeamento em `docker-compose.yml` (ex: `7861:7860`).
- Erro de permissão em volume no Linux/macOS:
  - Ajuste permissões da pasta local (`VIRALS`, `models`) para seu usuário Docker.
- GPU não detectada:
  - Valide `nvidia-smi` no host e a instalação do NVIDIA Container Toolkit.
- Build demorado:
  - Primeiro build é pesado por dependências de ML; os próximos usam cache de camadas.

## Exemplos de Saída

**Clip viral com legendas highlight**
[Assistir exemplo](https://github.com/user-attachments/assets/7a32edce-fa29-4693-985f-2b12313362f3)

**Comparação direta: Opus Clip vs ViralCutter** (mesmo vídeo de entrada)
[Assistir comparação](https://github.com/user-attachments/assets/12916792-dc0e-4f63-a76b-5698946f50f4)

**Modo Split Screen (2 faces)**
[Assistir split screen](https://github.com/user-attachments/assets/f5ce5168-04a2-4c9b-9408-949a5400d020)

## Roadmap (TODO)

- [x] Lançamento do código
- [ ] Demo permanente no Hugging Face Spaces
- [x] Suporte a 2 pessoas (Split Screen)
- [x] Legendas personalizadas e renderização (Burn)
- [x] Otimização de performance (Código mais rápido)
- [x] Modelos de IA 100% locais (Ollama/Llama/GGUF)
- [x] Tradução automática de legendas
- [x] Rastreamento dinâmico de rosto (O corte segue o movimento)
- [x] Exportação de XML para Premiere Pro (Beta)
- [ ] Música de fundo automática (Auto-Duck)
- [ ] Upload direto para TikTok/YouTube/Instagram
- [ ] Mais formatos de enquadramento (além de 9:16)
- [ ] Watermark opcional

---

## Contribua

O ViralCutter é mantido pela comunidade. Junte-se a nós para democratizar a criação de conteúdo com IA!

- **Discord**: [AI Hub Brasil](https://discord.gg/aihubbrasil)
- **Github**: Dê uma ⭐ estrela se este projeto te ajudou!

**Versão Atual**: 0.8v Alpha
_ViralCutter: Porque clips virais não precisam custar uma fortuna._ 🚀
