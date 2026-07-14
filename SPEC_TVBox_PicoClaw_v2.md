# Spec Driven - Sistema de Sinalizacao Digital Isolada (PicoClaw)

## 1. Objetivo

Transformar TV Box reaproveitadas e descaracterizadas em um sistema de sinalizacao digital local-first para escolas, APAEs e centros comunitarios, com um Gestor central e multiplos Exibidores.

O sistema deve:

- Operar 100% em rede local para entrega de conteudo.
- Permitir comando estruturado sem internet.
- Tratar o PicoClaw como a camada central de interpretacao e orquestracao de comandos, inclusive via mensageiro.
- Permitir que o usuario gestor envie imagem e instrucao em um chat e receba a automacao do destino como fluxo principal de operacao assistida.
- Garantir que Exibidores nunca tenham dependencia de nuvem ou credenciais externas.
- Minimizar escrita em eMMC e suportar queda de energia sem corromper estado.

## 2. Escopo

### 2.1 Em escopo

- Painel web para operador.
- API local para controle de telas.
- Exibidores leves que consultam o Gestor periodicamente.
- Biblioteca de midias aprovadas.
- Geracao de cartazes/slides a partir de texto.
- Integracao do PicoClaw com mensageiro para recebimento de imagem + comando de destino.
- Auditar comandos aceitos e recusados.
- Instaladores para Gestor e Exibidor.
- Persistencia em JSON com escrita atomica.

### 2.2 Fora de escopo inicial

- Video em tempo real.
- Navegador no Exibidor.
- Dependencia obrigatoria de internet.
- Chatbot publico ou atendimento aberto para usuarios finais.
- Multi-tenant com perfis complexos.
- Conteudo editavel diretamente no Exibidor.

## 3. Principios de arquitetura

### 3.1 Malhas separadas

O sistema deve separar claramente duas responsabilidades:

- Entrega de conteudo: Gestor -> Exibidores, sempre local.
- Ingestao de comando: Operador -> PicoClaw -> Gestor, local por padrao quando possivel; mensageiro como canal principal de entrada assistida.

### 3.2 Regras estruturais

- Exibidores nao acessam internet.
- Exibidores nao armazenam credenciais externas.
- Exibidores nao decidem o que exibir.
- O Gestor valida toda acao antes de aplicar.
- Toda mudanca de estado relevante deve ser auditada.
- Toda escrita persistente deve ser atomica.

## 4. Arquitetura logica

### 4.1 Nodo Gestor

Responsavel por:

- Servir painel e API.
- Manter estado da sinalizacao.
- Validar comandos.
- Gerar slides e cartazes.
- Integrar com PicoClaw como motor central de interpretacao e roteamento.
- Receber e processar mensagens de Telegram ou WhatsApp quando habilitado.
- Publicar midias e estados para os Exibidores.

Componentes sugeridos:

- `app.py`: rotas, autenticacao, orquestracao e validacao.
- `store.py`: leitura e escrita atomica de JSON.
- `auth.py`: login, sessoes e whitelist.
- `picoclaw_bridge.py`: adaptacao da linguagem natural e extracao de intencao.
- `messenger_bridge.py`: ingestao de mensagens e anexos vindos de Telegram ou WhatsApp.
- `render.py`: geracao de imagens de cartazes/slides.
- `content/`: biblioteca e artefatos gerados.
- `state/`: estado persistente do sistema.
- `config/`: configuracao e whitelist.
- `logs/`: auditoria.

### 4.2 Nodo Exibidor

Responsavel por:

- Consultar o Gestor em intervalos regulares.
- Baixar apenas o conteudo aprovado.
- Exibir imagem ou slide em tela cheia.
- Entrar em estado de reconexao quando o Gestor estiver indisponivel.

O Exibidor deve permanecer simples e previsivel, sem navegador e sem interface interativa local.

## 5. Requisitos funcionais

### 5.1 Gestao de telas

- O operador deve conseguir associar uma midia a uma tela.
- O operador deve conseguir limpar uma tela.
- O operador deve conseguir rotacionar uma playlist, se habilitada.
- O sistema deve suportar adicionar e remover telas por configuracao.
- Cada tela deve ter um nome canonico estavel no tipo `tv_sala`, `tv_saguao`, `tv_diretoria` ou equivalente.
- O PicoClaw deve conseguir resolver esse nome canonico e seus aliases em linguagem natural, para afetar somente a tela solicitada.
- Cada tela deve ser mapeada a um IP fixo no parque, com token de dispositivo e estado de atividade.
- Se o IP nao responder, ou se o dispositivo não apresentar heartbeat e token validos, o Gestor deve recusar a publicacao com `TV nao encontrada/cadastrada`.

### 5.2 Gestao de midias

- Somente arquivos presentes na biblioteca aprovada podem ser exibidos.
- O sistema deve aceitar imagens nos formatos PNG e JPG/JPEG no MVP.
- O sistema deve validar nome, caminho e tipo do arquivo.
- O sistema deve rejeitar path traversal e arquivos fora da biblioteca.

### 5.3 Geracao de conteudo

- O operador pode solicitar geracao de slide/cartaz a partir de titulo e corpo.
- O sistema deve gerar um PNG pronto para exibicao.
- O Exibidor nao deve interpretar HTML.

### 5.4 Comando estruturado

- O painel deve aceitar comandos estruturados offline.
- Os comandos estruturados devem funcionar sem internet.
- O sistema deve validar existencia de acao, tela e midia antes de aplicar.

### 5.5 Linguagem natural

- O sistema deve interpretar comandos em linguagem natural via PicoClaw.
- O fluxo primario pode acontecer dentro de um mensageiro, com envio de imagem e texto na mesma conversa.
- O usuario gestor pode enviar uma imagem e, em seguida, indicar a tela de destino em linguagem natural ou estruturada.
- O usuario gestor pode tambem autorizar ou revogar outros usuarios do mensageiro usando linguagem natural, informando chat_id ou @usuario quando o canal suportar.
- Apenas usuarios com papel de gestor podem conceder ou retirar permissao de outros usuarios para conversar com o PicoClaw via chat.
- Se o mensageiro ou o uplink estiverem indisponiveis, o sistema deve degradar para o painel local estruturado.

### 5.6 Auditoria

- Todo comando aceito ou recusado deve ser registrado.
- O registro deve incluir data/hora, usuario ou origem, acao, resultado e motivo de recusa quando houver.
- O registro deve indicar se a origem foi painel local, Telegram, WhatsApp ou outro canal habilitado.
- O registro deve incluir eventos de autorizacao e revogacao de usuarios do mensageiro.

## 6. Requisitos nao funcionais

### 6.1 Confiabilidade

- O sistema deve sobreviver a queda de energia sem corromper JSONs persistentes.
- O sistema deve manter o estado consistente apos reinicio.
- A entrega de conteudo deve continuar funcionando mesmo sem internet.

### 6.2 Desempenho

- O Exibidor deve verificar atualizacoes em intervalo curto e previsivel.
- A troca visual deve ocorrer em poucos segundos apos alteracao no Gestor.
- O Gestor deve ser leve o suficiente para funcionar em TV Box de baixo custo.

### 6.3 Durabilidade de armazenamento

- O sistema deve minimizar escrita no eMMC.
- Logs persistentes devem ser reduzidos no Exibidor.
- Estados devem ser gravados de forma atomica com arquivo temporario e renomeacao segura.

### 6.4 Operacao offline

- A operacao normal nao pode depender de nuvem.
- A ausencia de internet nao pode impedir o uso da biblioteca e do painel local.

## 7. Contrato de API

### 7.1 Base

- Base URL: `http://gestor.local:8080`
- Formato: JSON
- Autenticacao: sessao local no painel

### 7.2 Rotas principais

- `GET /api/tela/<id>`: estado atual de uma tela.
- `GET /conteudo/<src>`: entrega de midia aprovada.
- `POST /api/login`: cria sessao.
- `POST /api/logout`: encerra sessao.
- `GET /api/config`: retorna configuracao autorizada.
- `POST /api/comando`: aplica comando estruturado ou texto livre.
- `POST /api/mensagem`: recebe evento intermediario de mensageiro, quando o canal externo for habilitado.
- `GET /api/dispositivos`: lista o catalogo de TVs e o ultimo heartbeat conhecido.
- `POST /api/dispositivos`: cadastra ou atualiza um dispositivo associado a uma tela canonica.
- `POST /api/dispositivos/heartbeat`: confirma presenca do Exibidor e atualiza o estado de disponibilidade.
- `GET /api/autorizados`: lista usuarios de mensageiro atualmente autorizados.
- `GET /api/autorizacoes`: lista historico de autorizacoes e revogacoes.
- `GET /`: painel do operador.

### 7.3 Comportamento esperado

- `200`: sucesso.
- `400`: requisicao invalida ou comando inconsistente.
- `401`: nao autenticado.
- `403`: autenticado, mas sem permissao.
- `404`: tela ou midia inexistente.
- `409`: conflito de estado.
- `503`: recurso indisponivel, como linguagem natural sem uplink.
- `500`: erro interno nao esperado.

### 7.4 Regras de resposta

- A API deve responder com mensagens claras e previsiveis.
- Erros devem conter `code`, `message` e, quando possivel, `details`.
- A camada de comando nao deve aplicar mutacoes sem validacao previa.
- Quando a tela alvo nao estiver cadastrada, estiver inativa, sem heartbeat valido ou com IP divergente, a resposta deve recusar a acao com `TV nao encontrada/cadastrada`.

### 7.5 Timeout e retry

- Consultas dos Exibidores devem ter timeout curto e definido.
- O Exibidor deve repetir a requisicao apos falha, sem bloquear a exibicao indefinidamente.
- O Gestor deve responder rapidamente mesmo quando o canal de mensageiro ou o motor de interpretacao estiverem indisponiveis.

### 7.6 Comandos aceitos

Exemplos de payload:

```json
{ "acao": "exibir", "midia": "biblioteca/reuniao_pais.png", "tela": "tv_saguao" }
```

```json
{ "acao": "gerar_slide", "titulo": "Aviso", "corpo": "Reuniao amanha", "tela": "tv_sala" }
```

```json
{ "acao": "rotacionar", "tela": "tv_saguao" }
```

```json
{ "acao": "limpar", "tela": "tv_saguao" }
```

```json
{ "texto": "coloca o aviso da reuniao de pais na tv_saguao" }
```

## 8. Modelo de dados

### 8.1 Estado das telas

Arquivo: `state/telas.json`

Exemplo:

```json
{
  "tv_saguao": {
    "tipo": "imagem",
    "src": "biblioteca/reuniao_pais.png",
    "desde": "2026-07-13T14:03:00Z"
  },
  "tv_sala": {
    "tipo": "slide",
    "src": "gerado/slide_1783721755.png",
    "desde": "2026-07-13T13:50:00Z"
  }
}
```

Tipos permitidos:

- `imagem`
- `slide`
- `playlist`
- `vazio`

### 8.2 Biblioteca autorizada

- A biblioteca de midias deve ser descoberta a partir de pasta controlada.
- Apenas essa biblioteca pode gerar URL publica de conteudo.
- O sistema deve ignorar arquivos temporarios e rotinas de edicao.

### 8.3 Whitelist

Arquivo: `config/whitelist.json`

Deve conter dois conjuntos principais:

- `painel_local`: usuarios que podem entrar no painel web.
- `mensageiro`: usuarios e canais autorizados a conversar com o PicoClaw.

Cada entrada do `mensageiro` deve suportar, no minimo:

- `canal` (`telegram`, `whatsapp` ou outro canal habilitado).
- `user_id` ou `chat_id` como identificador primario quando disponivel.
- `telegram_username` ou alias equivalente, quando o canal permitir.
- `nome` legivel do usuario.
- `role` (`gestor` ou `operador`).
- `ativo` (`true` ou `false`).
- `autorizado_em` com data e hora da liberacao.
- `autorizado_por` com o usuario que concedeu a permissao.
- `revogado_em` e `revogado_por` quando aplicavel.

O sistema deve tratar `user_id` e `chat_id` como equivalentes operacionais quando o mensageiro suportar esse modelo.

Somente usuarios com `role = gestor` podem incluir, ativar, revogar ou consultar a lista completa de autorizados via chat.

Nao deve conter segredo em texto puro em ambiente real.

### 8.4 Configuracao

Arquivo: `config/settings.yml`

Deve incluir:

- porta do servidor.
- modo de operacao.
- configuracao do PicoClaw.
- intervalo de polling dos Exibidores.
- caminhos da biblioteca e estado.
- tempo maximo aceitavel desde o ultimo heartbeat de cada dispositivo.

### 8.5 Registro de autorizados

O sistema deve manter um registro consultavel de usuarios autorizados, separado da whitelist bruta, para operacao e auditoria.

Esse registro deve permitir identificar:

- quais usuarios estao autorizados no momento;
- quem autorizou cada usuario;
- quando a permissao foi concedida;
- quando a permissao foi revogada, se houver;
- qual canal de mensageiro foi usado.

O historico deve ser preservado mesmo quando o usuario for desativado.

### 8.6 Catalogo de telas

O arquivo de telas deve registrar, para cada tela:

- um identificador canonico;
- um nome legivel;
- aliases de linguagem natural;
- opcionalmente a sala fisica associada.

Exemplo:

```json
{
  "tv_sala": {
    "label": "TV da Sala",
    "aliases": ["sala", "tv da sala", "sala de aula"]
  }
}
```

O PicoClaw deve usar esse catalogo para entender instrucoes como "exiba a imagem xyz.png na tv da sala" e atingir apenas a tela correspondente.

### 8.7 Cadastro de dispositivos por IP

Cada tela deve ter um dispositivo cadastrado com:

- `screen_id` canonico;
- `ip` fixo;
- `device_token`;
- `ativo`;
- `label` amigavel;
- `aliases` de linguagem natural.

O Gestor deve manter um registro de heartbeat por equipamento. Se um IP ficar sem resposta, se o token nao bater ou se o equipamento nao estiver ativo, o estado da entrega deve ser tratado como indisponivel.

O estado operacional desse cadastro deve ser persistido em `state/dispositivos.json`, e o catalogo oficial deve ficar em `config/dispositivos.json`.

Exemplo:

```json
{
  "tv_saguao": {
    "screen_id": "tv_saguao",
    "label": "TV do Saguão",
    "ip": "192.168.15.16",
    "ativo": true,
    "device_token": "trocar-este-token",
    "aliases": ["tv do saguao", "saguao"]
  }
}
```

## 9. Seguranca

### 9.1 Autenticacao

- O login padrao pode existir apenas para demo.
- Em producao, senha padrao deve ser removida.
- A aplicacao deve aceitar hash de senha forte.

### 9.2 Sessao e protecao web

- O painel deve usar cookie de sessao com flags apropriadas.
- O sistema deve considerar protecao contra CSRF para requisicoes mutaveis.
- Rotas sensiveis devem exigir autenticacao.

### 9.3 Seguranca de conteudo

- A restricao de conteudo deve ser separada da irreversibilidade do hardware.
- Apenas midias da biblioteca podem ser publicadas.
- Comandos nao podem referenciar caminhos arbitrarios.

### 9.4 Mensageiro e linguagem natural como superficie controlada

- O recurso de linguagem natural deve ser considerado superficie adicional de risco, mas tambem uma via central de produtividade.
- Em caso de indisponibilidade, o sistema deve continuar operando com comandos estruturados.
- O Gestor nao deve confiar em saida do modelo sem validacao local.
- Mensageiros conectados ao PicoClaw devem ser tratados como canais de entrada autenticados e auditaveis, nao como interfaces publicas.
- O Gestor deve ser a autoridade final para conceder ou revogar permissao de usuarios do mensageiro.

## 10. Instalacao e operacao

### 10.1 Premissas do ambiente

- TV Box rodando Armbian.
- Acesso SSH ao Gestor e aos Exibidores.
- Rede cabeada via switch ou roteador local.
- Gestor publicado como `gestor.local` via mDNS.

### 10.2 Instalacao do Gestor

O instalador deve:

- copiar arquivos para o destino padrao.
- criar ambiente de execucao.
- registrar o servico systemd.
- iniciar o painel e a API.
- configurar o hostname e o mDNS.

### 10.3 Instalacao do Exibidor

O instalador deve:

- registrar o ID da tela.
- configurar a URL do Gestor.
- instalar dependencias minimas.
- registrar o servico de exibicao.
- evitar dependencias de navegador.

### 10.4 Operacao diaria

- O operador acessa o painel local.
- O gestor de conteudo pode enviar uma imagem no chat e depois dizer para qual tela ela deve ir.
- O gestor tambem pode autorizar ou revogar usuarios no proprio chat, informando chat_id ou @usuario, desde que seja autenticado como gestor.
- O operador escolhe midia e tela ou escreve um comando natural no painel quando preferir.
- O Gestor valida e registra a acao.
- O Exibidor troca a imagem quando detecta a atualizacao.

## 11. Conteudo e pipeline

### 11.1 Entrada de midias

- O MVP deve suportar PNG e JPG/JPEG.
- O sistema deve padronizar dimensoes para a resolucao alvo quando necessario.
- Arquivos invalidos devem ser recusados com erro explicito.

### 11.2 Geracao de slides

- O gerador deve produzir imagem final pronta para exibicao.
- O layout deve ser consistente e legivel em telas simples.
- Fontes, margem e contraste devem ser tratados pelo renderizador.

### 11.3 Fallback

- Quando a geracao falhar, o sistema deve manter o estado anterior.
- Quando uma midia estiver ausente, o sistema nao deve quebrar a tela inteira.

## 12. Atualizacao e rollback

### 12.1 Atualizacao

- O Gestor e os Exibidores devem poder ser atualizados sem reinstalacao manual completa.
- A atualizacao deve preservar config, biblioteca e estado.

### 12.2 Rollback

- Deve existir caminho de reversao da ultima versao funcional.
- Se a atualizacao falhar, o servico anterior deve poder ser restaurado rapidamente.

## 13. Logs, backup e manutencao

### 13.1 Logs

- Toda acao relevante deve ser auditada.
- Logs do Exibidor devem ser reduzidos ou volateis quando possivel.

### 13.2 Backup

- Backup minimo: `config/`, `state/` e `content/`.
- Restauracao deve exigir apenas recolocar os arquivos e reiniciar os servicos.

### 13.3 Verificacao operacional

- Status dos servicos deve ser verificavel por systemd.
- Falhas de rede local devem aparecer de forma clara para o operador.

## 14. Critérios de aceite

O MVP somente sera considerado pronto quando cumprir, no minimo:

- O Gestor responde no painel local sem internet.
- Um Exibidor recebe e mostra a imagem correta via rede local.
- Um comando estruturado troca a tela sem usar nuvem.
- Um fluxo via mensageiro recebe uma imagem e um comando de destino e executa a distribuicao correta.
- Um gestor autenticado consegue autorizar e revogar usuarios do mensageiro usando chat_id ou @usuario.
- A lista de autorizados e o historico de liberacoes ficam consultaveis com data, hora e autor da concessao.
- Uma midia fora da biblioteca e rejeitada.
- Uma queda de energia nao corrompe o estado salvo.
- O modo de linguagem natural pode falhar sem derrubar o fluxo principal, e o painel local continua disponivel como fallback.
- A auditoria registra comandos aceitos e recusados.

## 15. Testes minimos

### 15.1 Testes de unidade

- validacao de caminhos e nomes.
- escrita atomica do estado.
- autenticacao e whitelist.
- parse da saida do PicoClaw.

### 15.2 Testes de integracao

- login + comando estruturado + atualizacao de tela.
- Exibidor consultando o Gestor e baixando conteudo.
- recusa de midia fora da biblioteca.
- recusa de publicacao quando a TV cadastrada nao envia heartbeat valido ou o IP nao confere.

### 15.3 Testes de resiliencia

- queda de energia durante gravacao.
- ausencia de internet.
- Gestor indisponivel por alguns ciclos.

## 16. Roadmap sugerido

### Fase 1 - MVP local

- Painel local.
- API de telas.
- Biblioteca de midias.
- Exibidor com polling.
- Escrita atomica e logs.

### Fase 2 - Conteudo gerado

- Geracao de slide/cartaz.
- Melhorias visuais do render.
- Fallbacks mais claros.

### Fase 3 - Mensageiro e PicoClaw

- Ponte com PicoClaw e mensageiros.
- Validacao forte da saida.
- Timeout, retry e modo degradado.

### Fase 4 - Operacao em escala

- Instaladores maduros.
- Rollback.
- Matriz de hardware validada.
- Documentacao de campo.

## 17. Matriz de hardware a definir

Antes da implantacao ampla, validar e registrar:

- modelo da TV Box.
- SoC.
- memoria RAM.
- resolucao de saida.
- estabilidade de video.
- versao do Armbian e kernel.
- necessidade de ajuste de framebuffer ou DRM.

## 18. Decisoes de produto

- O sistema deve priorizar previsibilidade em vez de flexibilidade visual.
- O modo local deve ser o caminho principal de uso.
- O uso de internet deve ser opcional, isolado e visivel.
- A documentacao de instalacao deve ser testada como parte da entrega.

## 19. Proximos artefatos a produzir

- Especificacao da API com exemplos completos.
- Plano de diretorios e contratos de arquivo.
- Script de instalacao do Gestor.
- Script de instalacao do Exibidor.
- Suite de testes inicial.
- Documento de hardware suportado.

## 20. Observacao final

Esta versao da spec foi ajustada para reduzir risco de implementacao, manter o caminho offline como base de entrega e tratar PicoClaw como motor central de interpretacao e orquestracao, inclusive com entrada por mensageiro.
