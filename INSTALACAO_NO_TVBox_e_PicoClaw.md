# Como instalar o projeto no TV Box com PicoClaw

## Resumo

Como o TV Box já está com Armbian instalado e o PicoClaw já existe nele, o caminho mais simples e correto não é criar um executável único agora. O melhor fluxo é subir o projeto para o GitHub, clonar o repositório no TV Box e executar um script de instalação que prepara o ambiente, instala dependências e registra o serviço do sistema.

## Resposta curta

Sim, `git clone` resolve a base da instalação, mas sozinho ele não fecha o processo inteiro.

Para funcionar de forma limpa no TV Box, o projeto deve incluir:

- o código-fonte do Gestor e/ou Exibidor;
- um script de instalação;
- a configuração do serviço `systemd`;
- a integração com o PicoClaw já instalado.

## Fluxo recomendado

1. Publicar o projeto no GitHub.
2. No TV Box, fazer `git clone` do repositório.
3. Rodar um script de instalação, por exemplo `install.sh`.
4. Esse script deve:
   - criar o ambiente virtual de Python;
   - instalar dependências;
   - gerar ou copiar os arquivos de configuração;
   - criar o catálogo inicial de TVs em `config/dispositivos.json`;
   - criar o estado inicial de heartbeat em `state/dispositivos.json`;
   - registrar e habilitar o serviço `systemd`;
   - apontar o sistema para o PicoClaw local.

## Por que não começar com executável

Para esse tipo de projeto, empacotar tudo em um executável único não é a melhor primeira opção porque:

- o projeto tende a evoluir bastante durante o desenvolvimento;
- o uso de Python facilita ajustes rápidos;
- o script de instalação é mais transparente e fácil de depurar;
- a integração com o PicoClaw fica mais simples de manter;
- o sistema pode ser atualizado via `git pull` sem reinstalação completa.

## Como o PicoClaw entra nisso

O PicoClaw não deve ser tratado como o local onde o projeto inteiro é instalado. Ele funciona como uma dependência ou serviço já presente no TV Box, que o seu projeto vai chamar.

Na prática:

- o seu projeto fica em uma pasta própria, por exemplo `/home/admin/sinalizacao`;
- o script de instalação configura o caminho do PicoClaw;
- o código do projeto chama o PicoClaw quando precisar interpretar comandos em linguagem natural;
- se o PicoClaw falhar ou estiver indisponível, o sistema continua funcionando no modo estruturado.

## Quando faria sentido criar um executável

Um executável empacotado só passa a valer a pena se você quiser:

- distribuir para máquinas sem Python instalado;
- reduzir dependências locais ao máximo;
- entregar uma versão mais fechada para terceiros;
- simplificar instalação em um cenário de produção muito controlado.

Mesmo assim, isso pode ficar para uma fase posterior. Para começar, o modelo `git clone + install.sh + systemd` é mais adequado.

## Conclusão

Para o seu cenário, o melhor caminho é:

- GitHub como origem do projeto;
- `git clone` no TV Box;
- script de instalação para preparar o ambiente;
- serviço `systemd` para manter o sistema ativo;
- PicoClaw usado como componente externo já instalado.

Isso resolve instalação, manutenção e evolução do projeto de forma mais simples do que começar com executável.