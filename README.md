# InDigital

## SOBRE

O InDigital é um sistema web desenvolvido para o gerenciamento e otimização do uso dos laboratórios de informática do IFRN Campus São Paulo do Potengi. O projeto surgiu diante da necessidade de organizar os agendamentos e o controle de uso dos laboratórios, tornando o processo mais eficiente e acessível para alunos, monitores e administradores.

O sistema conta com:

- Sistema de agendamento e gerenciamento de reservas dos laboratórios de informática do campus;

- Controle de permissões e acesso para diferentes tipos de usuários (administrador, monitor e aluno);

- Consulta de disponibilidade em tempo real, evitando conflitos de horários e otimizando o uso dos espaços;

- Histórico e fila de espera para melhor acompanhamento das reservas e utilização dos recursos.

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC), com o objetivo de aplicar, de forma prática, os conhecimentos adquiridos ao longo da formação técnica integrada.

## TECNOLOGIAS UTILIZADAS

![Django]
![Python]
![HTML]
![JavaScript]
![Bootstrap]
![CSS3]
![AJAX]

## Pré-requisitos

- Python 3.8 ou superior
- MySQL
- Git
- VS Code

## INSTALAÇÃO

### Configurando o ambiente

- Clone o repositório

```bash
git clone https://github.com/Adaylla/InDigital.git
```

- Crie um ambiente virtual

```bash
python -m venv .venv
```

- Ative o ambiente virtual

_windows_
```powershell
.venv/Scripts/activate
```

_linux, macOs_
```bash
source .venv/bin/activate
```

### Configurando sua máquina

- Instale as dependências

```bash
pip install -r requirements.txt
```

- Faça as migrações necessárias

```bash
python manage.py migrate
```

- Crie as variáveis de ambiente

```bash
.env 
```

> Crie um arquivo `.env` na raiz do projeto, baseado no exemplo `.env exemplo`.

### Autenticação com SUAP

```bash
O InDigital utiliza o SUAP (Sistema Unificado de Administração Pública) do IFRN como provedor de autenticação OAuth2.
Isso permite que os usuários acessem o sistema com suas credenciais institucionais.
```

- Como configurar 

```bash
Acesse o painel de administração do SUAP:

https://suap.ifrn.edu.br/admin/api/aplicacaooauth2/
```

```bash
Crie uma nova Aplicação OAuth2 com os seguintes dados:

Nome: InDigital
Cliente tipo: Confidencial
Tipo de autorização: Authorization Code
URI de redirecionamento: 
http://127.0.0.1:8000/accounts/suap/login/callback/
```

```bash
Copie o Client ID e o Client Secret gerados.
```

```bash
Clique em salvar.
```

```bash
Adicione-os ao seu .env:

SUAP_CLIENT_ID=<seu_client_id>
SUAP_CLIENT_SECRET=<seu_client_secret>
```

### Rodando o servidor

- Rode o servidor

```bash
python manage.py runserver
```

- Acesse a aplicação localmente

```bash
http://127.0.0.1:8000
```

## Estrutura do projeto

```
InDigital/
│
├── config/                      # Configurações principais do Django (settings, urls, wsgi, asgi)
│
├── docs/                        # Documentação do projeto
│
├── indigital/                   # Aplicação principal do sistema
│
├── usuarios/                    # App responsável pelos usuários
│
├── venv/                        # Ambiente virtual Python (NÃO vai para o Git)
│
├── manage.py                    # Script principal do Django
├── requirements.txt             # Dependências do projeto
├── .env exemplo                 # Modelo de variáveis de ambiente
├── .env                         # Variáveis de ambiente reais (NÃO vai para o Git)
├── .gitignore                   # Arquivos ignorados pelo Git
├── README.md                    # Documentação inicial do projeto

```

## Funcionalidades
- consulte o [Manual do Usuário](docs/manual/index.html)

## Autores

- Adaylla Alannis
- Giulliana Beatriz

## Orientador

- Prof. Diego Cirilo