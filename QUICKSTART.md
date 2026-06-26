# Quick Start Guide: Credit Risk Underwriting System

**Get the system running in under 10 minutes!**

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11+** installed
- ✅ **Node.js 18+** and npm installed
- ✅ **AWS Account** with Bedrock access
- ✅ **AWS CLI** configured with credentials
- ✅ **Docker & Docker Compose** (optional, for containerized setup)

---

## Option 1: Docker Setup (Recommended)

### Step 1: Configure AWS Credentials

```bash
# Create .env file in project root
cat > .env << EOF
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
EOF
```

### Step 2: Start All Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 3: Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Step 4: Test the System

```bash
# Test API health
curl http://localhost:8000/health

# Test agent status
curl http://localhost:8000/api/v1/agents/status
```

---

## Option 2: Local Development Setup

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# Start backend server
python main.py
```

Backend will start on **http://localhost:8000**

### Step 2: Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```

Frontend will start on **http://localhost:5173**

---

## Testing the System

### 1. Submit a Test Application

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "555-1234",
    "loan_amount": 50000,
    "loan_purpose": "Debt Consolidation",
    "loan_term": 60,
    "age": 35,
    "annual_income": 85000,
    "employment_status": "Employed",
    "years_employed": 5,
    "home_ownership": "Mortgage",
    "credit_score": 720,
    "years_credit_history": 10,
    "num_credit_lines": 6,
    "dti_ratio": 28.0,
    "delinquencies_2yrs": 0,
    "public_records": 0,
    "savings": 25000,
    "monthly_debt": 2000
  }'
```

**Response:**
```json
{
  "application_id": "APPXXXX",
  "status": "pending",
  "submitted_at": "2026-01-31T...",
  "message": "Application submitted successfully"
}
```

### 2. Process the Application

```bash
# Replace APPXXXX with the application_id from above
curl -X POST http://localhost:8000/api/v1/underwrite/APPXXXX
```

**Response:** Complete underwriting decision with all agent results

### 3. View the Decision

```bash
curl http://localhost:8000/api/v1/decisions/APPXXXX
```

---

## Using the Frontend

1. **Open Browser:** Navigate to http://localhost:5173

2. **Submit Application:**
   - Fill out the loan application form
   - Upload required documents (optional)
   - Click "Submit Application"

3. **Process Application:**
   - Click "Process Application" button
   - Watch real-time agent progress
   - View decision in ~30 seconds

4. **Review Decision:**
   - See final decision (Approve/Deny/Conditional)
   - Review risk assessment
   - Read customer explanation
   - Check all agent results

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'langgraph'`

**Solution:**
```bash
pip install langgraph langchain langchain-aws
```

**Problem:** `boto3.exceptions.NoCredentialsError`

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

### Frontend Issues

**Problem:** `Cannot connect to backend`

**Solution:**
- Ensure backend is running on port 8000
- Check VITE_API_URL in frontend/.env
- Verify CORS settings in backend

**Problem:** `npm install fails`

**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Docker Issues

**Problem:** `docker-compose up fails`

**Solution:**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Next Steps

### 1. Explore the Documentation

- **[README.md](README.md)** - Complete project overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - API reference
- **[AGENT_SPECIFICATIONS.md](docs/AGENT_SPECIFICATIONS.md)** - Agent details

### 2. Customize the System

- Modify agent prompts in `backend/agents/`
- Adjust risk thresholds in `quantitative_risk_agent.py`
- Customize UI in `frontend/src/components/`
- Update design system in `tailwind.config.js`

### 3. Deploy to Production

See **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** for:
- AWS infrastructure setup
- CI/CD pipeline configuration
- Production environment variables
- Monitoring and logging

### 4. Integrate with Your Systems

- Connect to your database
- Integrate credit bureau APIs
- Add authentication/authorization
- Configure document storage (S3)

---

## Common Commands

### Docker

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Rebuild
docker-compose build

# Reset everything
docker-compose down -v
docker-compose up -d --build
```

### Backend

```bash
# Run tests
pytest tests/ -v

# Format code
black .

# Type checking
mypy .

# Run specific agent
python -m agents.chief_underwriter_agent
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Format
npm run format
```

---

## Performance Tips

1. **Enable Redis Caching:**
   - Uncomment Redis configuration in docker-compose.yml
   - Set REDIS_URL in backend/.env

2. **Use Production Build:**
   ```bash
   cd frontend
   npm run build
   # Serve with nginx or similar
   ```

3. **Optimize Database:**
   - Add indexes for frequently queried fields
   - Use connection pooling
   - Enable query caching

4. **Scale with Docker:**
   ```bash
   docker-compose up -d --scale backend=3
   ```

---

## Support

For issues or questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [full documentation](README.md)
3. Check agent logs for error details
4. Verify AWS Bedrock access and quotas

---

**You're all set! 🚀**

The system is now running and ready to process loan applications. Start by submitting a test application through the UI or API.
