# Romskjema Generator - Deployment Guide

## Overview

This guide covers deployment options for the Romskjema Generator, including standalone applications, Docker containers, and cloud deployment.

## Deployment Options

### 1. Standalone Application

#### Windows Deployment

**Prerequisites:**
- Windows 10/11 (64-bit)
- .NET Framework 4.7.2 or higher
- Visual C++ Redistributable

**Steps:**
1. **Build executable**:
   ```bash
   python build_executable.py
   ```

2. **Create installer**:
   ```bash
   python setup.py bdist_msi
   ```

3. **Distribute**:
   - Share the generated installer
   - Include user documentation
   - Provide system requirements

**Installation:**
- Run the installer as administrator
- Follow the installation wizard
- Verify installation with test IFC file

#### Linux Deployment

**Prerequisites:**
- Ubuntu 18.04+ or CentOS 7+
- Python 3.8+
- Required system libraries

**Steps:**
1. **Install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv
   ```

2. **Create application directory**:
   ```bash
   sudo mkdir -p /opt/romskjema-generator
   sudo chown $USER:$USER /opt/romskjema-generator
   ```

3. **Deploy application**:
   ```bash
   cp -r . /opt/romskjema-generator/
   cd /opt/romskjema-generator
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/romskjema-generator.service
   ```

   ```ini
   [Unit]
   Description=Romskjema Generator
   After=network.target

   [Service]
   Type=simple
   User=romskjema
   WorkingDirectory=/opt/romskjema-generator
   ExecStart=/opt/romskjema-generator/venv/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**:
   ```bash
   sudo systemctl enable romskjema-generator
   sudo systemctl start romskjema-generator
   ```

### 2. Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 romskjema && chown -R romskjema:romskjema /app
USER romskjema

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["python", "main.py"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  romskjema-generator:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
      - ./logs:/app/logs
    environment:
      - CACHE_MEMORY_MB=512
      - CACHE_DISK_MB=1024
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - romskjema-generator
    restart: unless-stopped
```

#### Build and Run

```bash
# Build image
docker build -t romskjema-generator .

# Run container
docker run -d \
  --name romskjema-generator \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  romskjema-generator

# Using Docker Compose
docker-compose up -d
```

### 3. Cloud Deployment

#### AWS Deployment

**EC2 Instance:**
1. **Launch EC2 instance**:
   - AMI: Ubuntu Server 20.04 LTS
   - Instance type: t3.medium or larger
   - Storage: 20GB EBS volume

2. **Configure security group**:
   - HTTP: 80
   - HTTPS: 443
   - SSH: 22

3. **Install application**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv nginx
   
   git clone https://github.com/your-org/romskjema-generator.git
   cd romskjema-generator
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Nginx**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Set up SSL**:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

**ECS Deployment:**
1. **Create ECS cluster**
2. **Define task definition**
3. **Create service**
4. **Configure load balancer**

#### Azure Deployment

**Azure App Service:**
1. **Create App Service**:
   - Runtime: Python 3.9
   - Operating System: Linux
   - Pricing Tier: Basic or higher

2. **Configure deployment**:
   - Source: GitHub
   - Branch: main
   - Build command: `pip install -r requirements.txt`

3. **Set environment variables**:
   - `CACHE_MEMORY_MB`: 512
   - `CACHE_DISK_MB`: 1024
   - `LOG_LEVEL`: INFO

**Azure Container Instances:**
1. **Build and push image**:
   ```bash
   az acr build --registry myregistry --image romskjema-generator .
   ```

2. **Deploy container**:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name romskjema-generator \
     --image myregistry.azurecr.io/romskjema-generator \
     --ports 8000 \
     --memory 2 \
     --cpu 1
   ```

#### Google Cloud Deployment

**Cloud Run:**
1. **Build and push image**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/romskjema-generator
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy romskjema-generator \
     --image gcr.io/PROJECT-ID/romskjema-generator \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

**Compute Engine:**
1. **Create VM instance**:
   - Machine type: e2-medium or larger
   - Boot disk: Ubuntu 20.04 LTS
   - Firewall: Allow HTTP and HTTPS

2. **Install application**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv nginx
   
   git clone https://github.com/your-org/romskjema-generator.git
   cd romskjema-generator
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

```bash
# Cache settings
CACHE_MEMORY_MB=512
CACHE_DISK_MB=1024
CACHE_DIRECTORY=/app/cache

# Performance settings
BATCH_CHUNK_SIZE=100
MAX_MEMORY_MB=1024
NUM_THREADS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost/romskjema

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### Configuration Files

**config.yaml:**
```yaml
cache:
  memory_mb: 512
  disk_mb: 1024
  directory: /app/cache

performance:
  batch_chunk_size: 100
  max_memory_mb: 1024
  num_threads: 4

logging:
  level: INFO
  file: /app/logs/app.log
  max_size: 10MB
  backup_count: 5

export:
  default_profile: production
  output_directory: /app/output
  auto_validate: true

security:
  secret_key: your-secret-key
  allowed_hosts:
    - localhost
    - 127.0.0.1
    - your-domain.com
```

## Monitoring and Maintenance

### Health Checks

**Application Health:**
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    }
```

**System Health:**
```python
@app.route('/health/detailed')
def detailed_health():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'memory_usage': get_memory_usage(),
        'disk_usage': get_disk_usage(),
        'cache_stats': get_cache_stats()
    }
```

### Logging

**Log Configuration:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Monitoring

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')
```

**Grafana Dashboard:**
- Request rate and duration
- Memory and CPU usage
- Cache hit rates
- Error rates
- Export success rates

## Security

### Authentication

**JWT Authentication:**
```python
import jwt
from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'message': 'Token is missing'}, 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user_id']
        except:
            return {'message': 'Token is invalid'}, 401
        
        return f(current_user, *args, **kwargs)
    return decorated
```

### Authorization

**Role-based Access:**
```python
def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if current_user.role != role:
                return {'message': 'Insufficient permissions'}, 403
            return f(*args, **kwargs)
        return decorated
    return decorator
```

### Data Protection

**Input Validation:**
```python
from marshmallow import Schema, fields, validate

class IFCFileSchema(Schema):
    file = fields.Raw(required=True, validate=validate.Length(min=1))
    max_size = fields.Int(validate=validate.Range(min=1, max=100*1024*1024))  # 100MB max
```

**Output Sanitization:**
```python
def sanitize_output(data):
    # Remove sensitive information
    if 'password' in data:
        del data['password']
    
    # Sanitize file paths
    if 'file_path' in data:
        data['file_path'] = os.path.basename(data['file_path'])
    
    return data
```

## Backup and Recovery

### Data Backup

**Automated Backup:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/romskjema-generator"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup application data
cp -r /app/data $BACKUP_DIR/$DATE/
cp -r /app/cache $BACKUP_DIR/$DATE/
cp -r /app/logs $BACKUP_DIR/$DATE/

# Backup configuration
cp /app/config.yaml $BACKUP_DIR/$DATE/

# Compress backup
tar -czf $BACKUP_DIR/romskjema-generator_$DATE.tar.gz -C $BACKUP_DIR $DATE

# Remove uncompressed backup
rm -rf $BACKUP_DIR/$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "romskjema-generator_*.tar.gz" -mtime +7 -delete
```

**Cron Job:**
```bash
# Add to crontab
0 2 * * * /app/backup.sh
```

### Recovery

**Restore from Backup:**
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
BACKUP_DIR="/backup/romskjema-generator"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Extract backup
tar -xzf $BACKUP_DIR/$BACKUP_FILE -C /tmp/

# Restore data
cp -r /tmp/*/data/* /app/data/
cp -r /tmp/*/cache/* /app/cache/
cp -r /tmp/*/logs/* /app/logs/
cp /tmp/*/config.yaml /app/config.yaml

# Clean up
rm -rf /tmp/*

echo "Restore completed"
```

## Troubleshooting

### Common Issues

**Memory Issues:**
- Check memory usage: `free -h`
- Adjust cache settings
- Use batch processing
- Monitor swap usage

**Performance Issues:**
- Check CPU usage: `top`
- Monitor disk I/O: `iostat`
- Review cache hit rates
- Optimize batch size

**Storage Issues:**
- Check disk space: `df -h`
- Clean up old logs
- Clear cache if needed
- Monitor backup storage

### Log Analysis

**Error Patterns:**
```bash
# Find errors in logs
grep -i error /app/logs/app.log | tail -20

# Find memory issues
grep -i "memory\|oom" /app/logs/app.log

# Find performance issues
grep -i "slow\|timeout" /app/logs/app.log
```

**Performance Analysis:**
```bash
# Analyze request patterns
awk '{print $1}' /app/logs/access.log | sort | uniq -c | sort -nr

# Find slow requests
grep "duration" /app/logs/app.log | awk '$NF > 5.0'
```

## Updates and Maintenance

### Application Updates

**Zero-downtime Deployment:**
1. **Blue-green deployment**
2. **Rolling updates**
3. **Health checks**
4. **Rollback capability**

**Update Process:**
```bash
# 1. Backup current version
cp -r /app /app.backup

# 2. Pull latest code
git pull origin main

# 3. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations (if applicable)
python manage.py migrate

# 5. Restart application
sudo systemctl restart romskjema-generator

# 6. Verify deployment
curl http://localhost:8000/health
```

### System Maintenance

**Regular Tasks:**
- **Log rotation**: Weekly
- **Cache cleanup**: Daily
- **Backup verification**: Weekly
- **Security updates**: Monthly
- **Performance review**: Monthly

**Maintenance Script:**
```bash
#!/bin/bash
# maintenance.sh

# Log rotation
logrotate /etc/logrotate.d/romskjema-generator

# Cache cleanup
find /app/cache -type f -mtime +30 -delete

# Backup verification
ls -la /backup/romskjema-generator/

# Security updates
sudo apt-get update && sudo apt-get upgrade -y

# Performance review
echo "=== System Status ==="
free -h
df -h
ps aux --sort=-%mem | head -10
```

## Support and Monitoring

### Monitoring Tools

**Application Monitoring:**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **AlertManager**: Alerting

**System Monitoring:**
- **Nagios**: System health
- **Zabbix**: Performance monitoring
- **ELK Stack**: Log analysis

### Alerting

**Critical Alerts:**
- Application down
- High memory usage (>90%)
- Disk space low (<10%)
- High error rate (>5%)

**Warning Alerts:**
- High CPU usage (>80%)
- Slow response time (>5s)
- Cache hit rate low (<70%)
- Backup failure

### Support Contacts

**Technical Support:**
- Email: support@romskjema-generator.com
- Phone: +47 123 456 78
- Hours: 9:00-17:00 CET

**Emergency Support:**
- Email: emergency@romskjema-generator.com
- Phone: +47 123 456 79
- Hours: 24/7

## Conclusion

This deployment guide provides comprehensive instructions for deploying the Romskjema Generator in various environments. Choose the deployment option that best fits your needs and follow the configuration and maintenance guidelines for optimal performance and reliability.
