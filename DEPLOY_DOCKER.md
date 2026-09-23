# Implantação do PetSUS com Docker

Esta configuração executa o Streamlit atrás do Caddy. O Caddy publica as portas
80 e 443, emite o certificado HTTPS e encaminha as requisições para a aplicação.
O banco SQLite e `usuarios.secret` ficam no volume nomeado `petsus_sqlite`.

## 1. Preparar o servidor

Use Ubuntu ou Debian com pelo menos 2 CPUs, 4 GB de RAM, 20 GB de disco e um IP
público. Instale Docker Engine com o plugin Docker Compose conforme a documentação
oficial do Docker. No firewall, libere somente SSH, TCP 80, TCP 443 e UDP 443.

Crie um registro DNS do tipo A, por exemplo `petsus.exemplo.com.br`, apontando
para o IP público do servidor. Se houver IPv6, configure também o registro AAAA.

## 2. Configurar a aplicação

No servidor, clone o repositório e entre na pasta:

```bash
git clone URL_DO_REPOSITORIO /opt/petsus
cd /opt/petsus
cp .env.example .env
nano .env
```

Preencha o domínio, o primeiro gestor e o SMTP. O arquivo `.env` é ignorado pelo
Git e não deve ser enviado ao repositório. Restrinja sua leitura:

```bash
chmod 600 .env
chmod +x scripts/backup.sh
```

Se `PETSUS_CPF_PEPPER` permanecer vazio, a aplicação cria `usuarios.secret` no
volume persistente. Esse arquivo é indispensável para localizar CPFs e validar
datas de nascimento. Não o perca nem o substitua depois de cadastrar usuários.

## 3. Construir e iniciar

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Veja os registros da aplicação e do proxy com:

```bash
docker compose logs -f app
docker compose logs -f caddy
```

Quando o DNS estiver propagado, acesse `https://SEU_DOMINIO`. O certificado é
emitido e renovado automaticamente pelo Caddy.

## 4. Trazer o banco local existente (opcional)

Faça backup antes. Pare a aplicação, copie os dois arquivos e corrija a propriedade
dos arquivos no volume para o usuário não privilegiado do contêiner:

```bash
docker compose stop app
docker compose cp usuarios.db app:/app/data/usuarios.db
docker compose cp usuarios.secret app:/app/data/usuarios.secret
docker compose run --rm --user root app chown 10001:10001 /app/data/usuarios.db /app/data/usuarios.secret
docker compose start app
```

Os dois arquivos devem sempre ser migrados juntos. Caso o ambiente anterior use
`PETSUS_CPF_PEPPER`, preserve exatamente o mesmo valor no novo `.env`.

## 5. Atualizar o sistema

Crie um backup e só então atualize:

```bash
./scripts/backup.sh
git pull --ff-only
docker compose build
docker compose up -d
docker compose ps
```

Não execute `docker compose down -v`: a opção `-v` remove o volume com as contas.

## 6. Backup automático

O script usa a API de backup do SQLite para produzir uma cópia consistente e
inclui `usuarios.secret` no mesmo arquivo compactado:

```bash
./scripts/backup.sh
```

Agende diariamente no `crontab -e` do servidor:

```cron
0 2 * * * cd /opt/petsus && ./scripts/backup.sh >> /var/log/petsus-backup.log 2>&1
```

Copie periodicamente a pasta `backups/` para outro servidor ou armazenamento.
Os arquivos contêm dados de autenticação e devem ser criptografados e protegidos.

## 7. Restauração

Pare a aplicação, extraia um backup e copie os dois arquivos de volta:

```bash
docker compose stop app
mkdir -p /tmp/petsus-restore
tar -xzf backups/petsus-AAAAMMDDTHHMMSSZ.tar.gz -C /tmp/petsus-restore
docker compose cp /tmp/petsus-restore/usuarios.db app:/app/data/usuarios.db
if [ -f /tmp/petsus-restore/usuarios.secret ]; then
  docker compose cp /tmp/petsus-restore/usuarios.secret app:/app/data/usuarios.secret
fi
docker compose run --rm --user root app chown -R 10001:10001 /app/data
docker compose start app
```

Confira o login antes de apagar os arquivos extraídos. Se um pepper foi definido
no `.env`, restaure também o mesmo valor usado quando o backup foi criado.

## 8. Operações úteis

```bash
# Estado e saúde dos serviços
docker compose ps

# Reiniciar somente a aplicação
docker compose restart app

# Parar sem excluir dados
docker compose down

# Conferir o volume persistente
docker volume inspect petsus_petsus_sqlite
```

O Streamlit não publica a porta 8501 no host; ele só é acessível pela rede interna
do Compose. Todo acesso externo passa pelo Caddy e pelo HTTPS.
