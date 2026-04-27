# Tencent Cloud Lighthouse Production Notes

Target host:

- domain: `medichatrd.cloud`
- public IP: `43.128.114.201`
- region: `Singapore, Zone 2`

This project currently runs best as:

- one FastAPI process
- one Nginx reverse proxy
- local persistent directories for `data/` and `.secrets/`

Current production-sensitive storage:

- SQLite patient data: `data/patient_registry.db`
- file-based SecondMe token store: `.secrets/secondme_oauth.json`
- in-memory chat sessions in `backend/main.py`

That means:

- do not scale to multiple app workers yet
- back up `/opt/medichat-rd/data` and `/opt/medichat-rd/.secrets`
- keep the app behind Nginx on `127.0.0.1:8001`

Suggested server bootstrap:

```bash
sudo apt update
sudo apt install -y git nginx python3 python3-venv python3-pip build-essential
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Suggested app install:

```bash
sudo mkdir -p /opt/medichat-rd
sudo chown -R $USER:$USER /opt/medichat-rd
cd /opt/medichat-rd
git clone https://github.com/MoKangMedical/medichat-rd.git .
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
mkdir -p data logs .secrets
```

Systemd install:

```bash
sudo cp deploy/tencentcloud/medichat-rd.service /etc/systemd/system/medichat-rd.service
sudo systemctl daemon-reload
sudo systemctl enable medichat-rd
sudo systemctl start medichat-rd
sudo systemctl status medichat-rd
```

Nginx install:

```bash
sudo cp deploy/tencentcloud/nginx-medichatrd.cloud.conf /etc/nginx/sites-available/medichatrd.cloud
sudo ln -s /etc/nginx/sites-available/medichatrd.cloud /etc/nginx/sites-enabled/medichatrd.cloud
sudo nginx -t
sudo systemctl reload nginx
```

HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d medichatrd.cloud -d www.medichatrd.cloud
```
