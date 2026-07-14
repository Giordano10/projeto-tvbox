# Projeto TV Box - Sinalizacao Digital Isolada

Sistema local-first para reaproveitar TV Box com Armbian como sinalizacao digital em escolas, APAEs e centros comunitarios. A ideia central e ter um Gestor central que controla o conteudo das telas, um Exibidor leve para cada TV e o PicoClaw como motor principal de interpretacao de comandos, inclusive dentro de mensageiros.

## Proposta

O projeto foi desenhado para funcionar assim:

- a entrega de conteudo para as telas acontece 100% em rede local;
- o operador ou gestor pode usar um painel local;
- o gestor tambem pode enviar imagem e instrucoes por chat;
- o PicoClaw interpreta a intencao, inclusive comandos administrativos;
- o Gestor valida tudo antes de publicar;
- os Exibidores apenas consultam o Gestor e mostram o que foi aprovado.

## O que o sistema faz

- publica imagens e slides em telas especificas;
- gera cartazes/slides a partir de texto;
- mantém whitelist segura de usuarios autorizados;
- registra auditoria de comandos, autorizacoes e revogacoes;
- opera sem internet para a entrega de conteudo;
- permite linguagem natural como fluxo principal de operacao assistida.

## Arquitetura atual

### Gestor

O Gestor fica em `sinalizacao/server/` e concentra a logica principal.

Responsabilidades:

- painel web e API local;
- validacao de comandos;
- integracao com PicoClaw;
- gerenciamento de whitelist;
- geracao de slides;
- registro de logs e auditoria.

### Exibidor

O Exibidor fica em `exibidor/` e e o player local de cada tela.

Responsabilidades:

- consultar o Gestor periodicamente;
- baixar apenas a midia aprovada;
- exibir a imagem ou slide em tela cheia;
- degradar com seguranca se o Gestor estiver indisponivel.

### Mensageiro + PicoClaw

O fluxo de chat e tratado como canal principal de entrada assistida.

O gestor pode:

- enviar uma imagem no chat;
- mandar a instrucao de destino;
- autorizar ou revogar outros usuarios;
- consultar usuarios autorizados e historico.

### Telas nomeadas

Cada TV Box do parque tem um nome canonico fixo, como `tv_saguao`, `tv_sala` ou `tv_diretoria`.

O PicoClaw usa esse catalogo de telas e seus aliases para interpretar comandos do tipo:

- "coloque a imagem xyz.png na tv da sala";
- "mande o aviso para a tv do saguao";
- "publique o cartaz na tv da diretoria".

O Gestor aplica a acao apenas na tela identificada, sem afetar as demais.

### Equipamentos por IP

Cada TV Box do parque deve ser cadastrada no Gestor com:

- nome canonico da tela;
- IP fixo da rede interna;
- token de dispositivo;
- status ativo ou inativo.

O Exibidor envia heartbeat para o Gestor com esse token. Se o IP nao responder, o token nao bater ou o equipamento nao estiver cadastrado, o Gestor recusa o envio com a mensagem `TV nao encontrada/cadastrada`.

O catalogo oficial fica em `config/dispositivos.json` e o estado do ultimo heartbeat em `state/dispositivos.json`.

## Status atual

O repositorio ja contem uma base funcional com:

- Gestor Flask com API local;
- armazenamento atomico em JSON;
- whitelist com papel de usuario;
- registros de autorizacao e auditoria;
- interpretacao basica do PicoClaw;
- player local do Exibidor com polling;
- testes automatizados para o Gestor e o Exibidor.

## Estrutura do projeto

- `sinalizacao/server/`: nucleo do Gestor.
- `exibidor/`: player local da tela.
- `config/`: settings, whitelist e mapa de telas.
- `state/`: estado persistente do sistema.
- `content/`: biblioteca de midias e conteudos gerados.
- `logs/`: auditoria e historico.
- `scripts/`: instaladores e automacao.
- `tests/`: testes automatizados.
- `SPEC_TVBox_PicoClaw_v2.md`: contrato funcional do projeto.
- `FLUXO_PicoClaw_Mensageiro.md`: fluxo de operacao por chat e autorizacao.
- `INSTALACAO_NO_TVBox_e_PicoClaw.md`: guia de instalacao no TV Box.

## Como rodar no desenvolvimento

1. Ative o ambiente virtual.
2. Instale as dependencias do `requirements.txt`.
3. Execute o Gestor com:

```bash
python -m sinalizacao.server.app
```

4. Em outra instalacao ou maquina de teste, execute o Exibidor com:

```bash
python -m exibidor.main
```

## Configuracao do Gestor

Arquivos principais:

- `config/settings.yml`: porta, modo, polling e configuracao do PicoClaw.
- `config/whitelist.json`: usuarios do painel e do mensageiro.
- `config/telas.map.json`: mapeamento e aliases de telas.
- `config/dispositivos.json`: catalogo de TVs por IP fixo e token.
- `state/dispositivos.json`: ultimo heartbeat e disponibilidade de cada TV.

Rotas principais da API:

- `GET /api/tela/<id>`: estado de uma tela.
- `GET /conteudo/<src>`: entrega da midia aprovada.
- `POST /api/login`: autentica no painel.
- `POST /api/logout`: encerra sessao.
- `GET /api/config`: configuracao, estado e midias.
- `POST /api/comando`: comando estruturado ou texto livre.
- `POST /api/mensagem`: entrada intermediaria de mensageiro.
- `GET /api/dispositivos`: lista os dispositivos cadastrados.
- `POST /api/dispositivos`: cadastra ou atualiza um dispositivo por tela canonica.
- `POST /api/dispositivos/heartbeat`: confirma a presenca do Exibidor na rede.
- `GET /api/autorizados`: usuarios atualmente autorizados.
- `GET /api/autorizacoes`: historico de liberacoes e revogacoes.

## Modelo de autorizacao

O sistema usa uma whitelist segura para controlar quem pode falar com o PicoClaw via chat.

Cada usuario do mensageiro pode ter:

- `canal`;
- `user_id` ou `chat_id`;
- `telegram_username` ou alias equivalente;
- `role`;
- `ativo`;
- `autorizado_em`;
- `autorizado_por`;
- `revogado_em` e `revogado_por` quando necessario.

Somente usuarios com papel de `gestor` podem conceder ou revogar permissao de outros usuarios via chat.

## Modelo de telas

As telas tambem seguem um catalogo nomeado:

- identificador canonico como `tv_sala`;
- label legivel;
- aliases que o PicoClaw reconhece em linguagem natural;
- estado persistente por tela no Gestor.

Isso permite que a instrucao em chat seja focada em apenas uma TV, mesmo quando o parque tiver varias telas simultaneas.

## Como instalar no TV Box

Para uso em campo, o fluxo recomendado e:

1. subir o codigo para o GitHub;
2. clonar o repositorio no TV Box;
3. rodar `scripts/install-gestor.sh`;
4. configurar o Exibidor com `exibidor/scripts/instalar-exibidor.sh`;
5. registrar os servicos `systemd`.

O guia completo esta em `INSTALACAO_NO_TVBox_e_PicoClaw.md`.

## Testes

Rode a suite com:

```bash
python -m unittest discover -s tests -p 'test*.py'
```

## Inconsistencias e pendencias conhecidas

Estas sao as principais diferencas entre a proposta da spec e o que ainda falta fechar ou integrar totalmente:

- ainda nao existe um conector real de Telegram ou WhatsApp; hoje o projeto tem o contrato de entrada em `POST /api/mensagem`, mas nao o webhook/bot final de cada mensageiro;
- a selecao do canal de mensageiro ainda esta em fase de integracao, entao a logica de autorizacao esta pronta no Gestor, mas o adaptador externo ainda precisa ser ligado;
- o player do Exibidor usa `fbi` como caminho padrao, mas ele depende da disponibilidade do binario no sistema alvo;
- a whitelist padrao ainda contem credenciais de demo no ambiente de desenvolvimento e isso precisa ser substituido por hash forte antes de producao.

## Observacao final

Este README descreve a direcao real do projeto e o que ja existe no codigo. Se alguma parte da spec, do fluxo ou da implementacao nao bater com essa descricao, o ponto a corrigir deve aparecer em uma das secoes de inconsistencias acima.
