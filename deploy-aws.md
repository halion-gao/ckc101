# AWS Container Deployment Guide (AWS 容器部署指南)

This guide provides step-by-step instructions to build, run, and deploy the SRE Monitor Dashboard container on Amazon Web Services (AWS).

---

## 🛠️ 1. Local Testing (本地測試)

Before deploying to AWS, verify the Docker container works locally:

1. **Build the Docker image**:
   ```bash
   docker build -t ckc101-app .
   ```

2. **Run the container**:
   ```bash
   docker run -d -p 19191:19191 --name ckc101-container ckc101-app
   ```

3. **Verify locally**:
   - Open your browser and navigate to `http://localhost:19191/`
   - Access `http://localhost:19191/api/metrics` to verify that the API serves CORS headers successfully.

4. **Stop the container**:
   ```bash
   docker stop ckc101-container
   docker rm ckc101-container
   ```

---

## ☁️ 2. AWS App Runner Deployment (推薦方案：AWS App Runner 部署)

AWS App Runner is a fully managed service that makes it easy for developers to quickly deploy containerized web applications.

### Method A: Build from GitHub (推薦)
1. **Push your code**: Make sure your repository on GitHub is up-to-date (containing the `Dockerfile` and `src/` folder).
2. **Open AWS Console**: Navigate to **AWS App Runner** > **Create service**.
3. **Source and deployment**:
   - Source: Choose **Source code repository**.
   - Connect your GitHub account and select the `ckc101` repository and `main` branch.
   - Deployment settings: Choose **Automatic** (so it deploys automatically every time you push to `main`).
4. **Configure build**:
   - Configuration file: Choose **Configure all settings here**.
   - Runtime: Choose **Python 3**.
   - Build command: `pip install -r requirements.txt && pip install gunicorn`
   - Start command: `gunicorn --bind 0.0.0.0:19191 src.app:app`
   - Port: `19191` (or change to standard `8080` if needed).
5. **Review and deploy**: Click **Create & deploy**. App Runner will provision the environment, generate an SSL certificate, and give you a public HTTPS URL (e.g. `https://xxxxxx.us-east-1.awsapprunner.com`).

---

## 🖥️ 3. AWS EC2 Deployment (輕量方案：AWS EC2 手動部署)

For simple, cost-efficient (Free Tier eligible) single-instance hosting:

### Step 1: Launch an EC2 Instance
1. Go to the **EC2 Console** > **Launch instance**.
2. Select **Amazon Linux 2023 AMI** (Free Tier eligible).
3. Choose instance type (e.g. `t3.micro` or `t2.micro`).
4. Select or create a **Key Pair** to SSH into the instance.
5. In **Network Settings** (Security Group):
   - Allow SSH (port 22) from your IP.
   - Allow HTTP (port 80) and custom TCP port **19191** from Anywhere (`0.0.0.0/0`).

### Step 2: Install Docker on the EC2 Instance
SSH into your instance and run:
```bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
# Allow ec2-user to run Docker commands without sudo
sudo usermod -aG docker ec2-user
```
*(Log out and log back in for the group permissions to take effect)*

### Step 3: Run the App
Clone the repository and run:
```bash
git clone https://github.com/halion-gao/ckc101.git
cd ckc101
docker build -t ckc101-app .
docker run -d -p 19191:19191 --name ckc101-container --restart always ckc101-app
```
Access the dashboard via `http://<your-ec2-public-ip>:19191/`.

---

## 📦 4. Pushing Image to Amazon ECR (推送至 Amazon ECR)

If deploying to **AWS ECS (Fargate)**, you must first host the image in Amazon ECR:

1. **Create an ECR Repository**:
   ```bash
   aws ecr create-repository --repository-name ckc101 --region <your-region>
   ```

2. **Authenticate Docker to ECR**:
   ```bash
   aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com
   ```

3. **Tag your image**:
   ```bash
   docker tag ckc101-app:latest <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com/ckc101:latest
   ```

4. **Push the image**:
   ```bash
   docker push <aws_account_id>.dkr.ecr.<your-region>.amazonaws.com/ckc101:latest
   ```
