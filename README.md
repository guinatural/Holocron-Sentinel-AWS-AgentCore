# Holocron Sentinel - AWS AgentCore Environment

Este repositorio contem a base de codigo oficial para o Holocron Sentinel V2, um orquestrador autonomo focado em compliance com a Lei Geral de Protecao de Dados (LGPD) no Brasil.

A motivacao principal para a criacao deste projeto e democratizar e escalar o acesso a seguranca da informacao. Muitas empresas brasileiras nao possuem orcamentos milionarios para contratar Data Protection Officers (DPO) ou auditorias constantes. O Holocron atua como um DPO virtual que entende e aplica a lei de forma automatizada.

## Arquitetura e Decisoes Tecnicas

Nesta segunda versao do projeto, migramos de um modelo de chat reativo simples para uma arquitetura autonoma, segura e corporativa na Amazon Web Services (AWS). O codigo aqui presente demonstra como instanciar e monitorar esse agente.

As pecas centrais desta arquitetura sao:

1. Amazon Bedrock AgentCore Runtime: O agente e executado de forma isolada em conteineres serverless. Isso garante que os dados de uma empresa jamais vazem ou interajam com o ambiente de outra empresa.
2. Anthropic Claude 3: Utilizamos essa familia de modelos (Haiku e Sonnet) devido a sua capacidade massiva de leitura de contexto. Ele e capaz de ler dezenas de contratos juridicos de uma so vez sem sofrer de injecoes de prompt, um fator critico para seguranca de dados.
3. Model Context Protocol (MCP) e AWS Gateway: Em vez de o agente apenas responder perguntas, ele recebe permissoes para agir ativamente. O protocolo permite buscar artigos da LGPD em tempo real ou analisar planilhas de logs para buscar tentativas de vazamento de dados.
4. Identidade e Memoria: A aplicacao retem o contexto do usuario, lembrando-se de consultadas passadas (como foco no artigo 7 da lei) atraves da injecao de ganchos de memoria (Memory Hooks), e todo o trafego e autenticado via tokens JWT gerados por camadas de seguranca da nuvem.

## Como o codigo esta organizado

O codigo reflete uma transicao clara de laboratorios de aprendizado padrao para regras rigidas de negocios juridicos.
Dentro dos tutoriais integrados, adaptamos e substituimos as lógicas das funcoes e ferramentas:
As camadas de teste contam com validadores de consentimento e ferramentas de anonimizacao de dados sensiveis (como CPFs e emails) antes de registrar qualquer evento de log no CloudWatch.

## Executando o Projeto

Para executar qualquer etapa deste projeto localmente:

1. O projeto requer Python 3.10 ou superior e credenciais ativas da AWS.
2. Inicie o ambiente virtual que ja foi configurado na raiz executando no terminal o script local de ativacao da sua pasta venv.
3. Instale as dependencias minimas listadas nos respectivos arquivos requirements.txt com o comando de instalacao do pip.
4. O ambiente suporta tanto ferramentas interativas de notebook para demonstracao (como Jupyter) quanto execucao direta de scripts modulares.

## Status

Este ambiente se encontra em fase de producao controlada e desenvolvimento paralelo de lambdas para o Gateway de acesso a dados. Todos os experimentos de execucao foram validados para o mercado corporativo.
