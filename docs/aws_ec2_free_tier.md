# AGNI on AWS Free Tier (EC2 t3.micro) — public dev server

This gives you a permanent public URL (`http://<ec2-ip>:8000`) the app reaches from any network.
Free for 12 months on the AWS Free Tier (t3.micro / t2.micro, 750 hrs/month).

It runs the **lite** build — one container, in-memory backends — which fits the 1 GB free
instance comfortably. (Postgres/Redis/Qdrant come later when you move to a bigger box.)

---

## Step 0 — Put the code on GitHub (one time, needed to get it onto the server)

Easiest with **GitHub Desktop** (no terminal):
1. Free account at **github.com**, install **GitHub Desktop**.
2. **File → Add local repository →** `D:\Agni Advance\god_mode_ai` → **Create a repository**.
3. **Publish repository** (Private is fine). Copy the repo URL (e.g.
   `https://github.com/YOURNAME/god_mode_ai`).

---

## Step 1 — Launch the EC2 instance

1. Sign in to the **AWS Console** → search **EC2** → **Launch instance**.
2. **Name:** `agni`.
3. **AMI:** Ubuntu Server 24.04 LTS (Free tier eligible).
4. **Instance type:** **t3.micro** (or t2.micro) — must say *Free tier eligible*.
5. **Key pair:** Create one, download the `.pem` (or choose "Proceed without" and use browser
   connect later).
6. **Network settings → Edit → Security group**, allow these inbound rules:
   - **SSH** TCP 22 — Source: My IP
   - **Custom TCP** 8000 — Source: Anywhere (0.0.0.0/0)  ← this is the API port
7. **Launch instance.** Open it and copy the **Public IPv4 address** (e.g. `13.234.x.x`).

---

## Step 2 — Connect to the server

EC2 console → select the instance → **Connect** → **EC2 Instance Connect** → **Connect**
(opens a browser terminal, no key needed). You're now on the server.

---

## Step 3 — Install Docker, get the code, run it

Paste these in the EC2 terminal (replace the GitHub URL with yours):

```bash
sudo apt-get update -y
curl -fsSL https://get.docker.com | sudo sh

git clone https://github.com/YOURNAME/god_mode_ai.git
cd god_mode_ai

# Build the image and run the lite (in-memory) API on port 8000:
sudo docker build -f docker/Dockerfile -t agni-api .
sudo docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET=change-me-to-something-random \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

If the GitHub repo is **private**, `git clone` will ask for a username + a Personal Access Token
(GitHub → Settings → Developer settings → Tokens). Or make the repo public for simplicity.

Check it's up:
```bash
curl http://localhost:8000/health     # -> {"status":"ok",...}
```

---

## Step 4 — Use it in the app

- Test from any browser/phone: `http://<EC2-PUBLIC-IP>:8000/health`
- In the app's **Server URL** field: `http://<EC2-PUBLIC-IP>:8000` → Create account.

Works from office Wi-Fi, 5G, anywhere. No tunnel, no laptop needed.

---

## Notes

- **The public IP changes if you stop/start the instance.** To keep it fixed, allocate a free
  **Elastic IP** (EC2 → Elastic IPs → Allocate → Associate to the instance) — free while attached
  to a running instance.
- **HTTPS later:** to get `https://`, point a domain at the IP and run Caddy
  (see `deployment/budget/`), or front it with the Phase 12 ALB + ACM when you scale up.
- **Stay in the Free Tier:** keep ONE t3.micro running; stop it when not needed. Watch the AWS
  Billing dashboard.
- **Updating the code:** on the server, `cd god_mode_ai && git pull && sudo docker build -f
  docker/Dockerfile -t agni-api . && sudo docker rm -f agni && <the docker run command again>`.
