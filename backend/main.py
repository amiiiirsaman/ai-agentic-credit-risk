"""
FastAPI Main Application for Credit Risk Assessment Platform
"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Set, Any
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv


class WebSocketManager:
    """Manages WebSocket connections for real-time updates with message queuing"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.message_queues: Dict[str, List] = {}  # Queue messages until client connects
        self.connection_events: Dict[str, asyncio.Event] = {}  # Signal when client connects
    
    async def connect(self, websocket: WebSocket, application_id: str):
        await websocket.accept()
        if application_id not in self.active_connections:
            self.active_connections[application_id] = set()
        self.active_connections[application_id].add(websocket)
        
        # Signal that a connection is now available
        if application_id in self.connection_events:
            self.connection_events[application_id].set()
        
        # Replay any queued messages
        if application_id in self.message_queues:
            queued = self.message_queues[application_id]
            print(f"[WebSocket] Replaying {len(queued)} queued messages for {application_id}")
            for msg in queued:
                try:
                    await websocket.send_json(msg)
                    await asyncio.sleep(0.15)  # Delay between messages for UI to update
                except Exception as e:
                    print(f"[WebSocket] Error replaying message: {e}")
            del self.message_queues[application_id]
    
    def disconnect(self, websocket: WebSocket, application_id: str):
        if application_id in self.active_connections:
            self.active_connections[application_id].discard(websocket)
            if not self.active_connections[application_id]:
                del self.active_connections[application_id]
    
    def prepare_for_processing(self, application_id: str):
        """Prepare message queue and connection event for a new application"""
        self.message_queues[application_id] = []
        self.connection_events[application_id] = asyncio.Event()
        print(f"[WebSocket] Prepared queue for {application_id}")
    
    async def wait_for_connection(self, application_id: str, timeout: float = 15.0) -> bool:
        """Wait for a WebSocket connection to be established"""
        if application_id not in self.connection_events:
            self.connection_events[application_id] = asyncio.Event()
        
        # Check if already connected
        if application_id in self.active_connections and self.active_connections[application_id]:
            print(f"[WebSocket] Already connected for {application_id}")
            return True
        
        try:
            print(f"[WebSocket] Waiting for connection for {application_id}...")
            await asyncio.wait_for(
                self.connection_events[application_id].wait(),
                timeout=timeout
            )
            print(f"[WebSocket] Connection received for {application_id}!")
            return True
        except asyncio.TimeoutError:
            print(f"[WebSocket] Timeout waiting for connection for {application_id}")
            return False
    
    async def broadcast(self, application_id: str, message: dict):
        """Broadcast message to connected clients, or queue if none connected"""
        sent = False
        
        if application_id in self.active_connections and self.active_connections[application_id]:
            dead_connections = set()
            for connection in self.active_connections[application_id]:
                try:
                    await connection.send_json(message)
                    sent = True
                except Exception:
                    dead_connections.add(connection)
            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[application_id].discard(conn)
        
        # If no active connections, queue the message
        if not sent:
            if application_id not in self.message_queues:
                self.message_queues[application_id] = []
            self.message_queues[application_id].append(message)
        
        agent_info = message.get('agent', 'N/A')
        msg_type = message.get('type', 'unknown')
        status = 'SENT' if sent else 'QUEUED'
        print(f"[WebSocket] {status}: {msg_type} for agent={agent_info}")


ws_manager = WebSocketManager()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import application modules
from models import (
    LoanApplicationRequest,
    LoanApplicationResponse,
    UnderwritingDecision,
    ApplicationStatusResponse,
    SystemHealth,
    DashboardMetrics,
)
from database import init_db, get_db, AsyncSessionLocal, ApplicationDB, DecisionDB
from orchestrator import get_orchestrator, UnderwritingOrchestrator
from synthetic_data import SyntheticDataGenerator, get_sample_application


# In-memory storage for demo (replace with database in production)
applications_store: dict = {}
decisions_store: dict = {}
processing_status: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Credit Risk Assessment Platform...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    # Initialize orchestrator
    try:
        orchestrator = get_orchestrator()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Orchestrator initialization failed: {e}")
    
    yield
    
    logger.info("Shutting down Credit Risk Assessment Platform...")


# Create FastAPI app
app = FastAPI(
    title="AI Credit Risk Assessment Platform",
    description="Enterprise-grade credit risk assessment using multi-agent AI orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoints
@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/v1/agents/status", tags=["System"])
async def get_agents_status():
    """Get status of all agents"""
    agents = [
        "DocumentIntelligence",
        "FraudDetection",
        "IncomeVerification", 
        "CreditHistory",
        "QuantitativeRisk",
        "Collateral",
        "CustomerRelationship",
        "MarketConditions",
        "Compliance",
        "ChiefUnderwriter",
        "Explainability"
    ]
    
    return {
        "status": "healthy",
        "agents": [
            {
                "name": agent,
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat()
            }
            for agent in agents
        ],
        "total_agents": len(agents)
    }


# Application Endpoints
@app.post("/api/v1/applications", response_model=LoanApplicationResponse, tags=["Applications"])
async def submit_application(
    application: LoanApplicationRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new loan application"""
    import uuid
    
    application_id = str(uuid.uuid4())
    
    # Store application
    app_data = application.model_dump()
    applications_store[application_id] = {
        "id": application_id,
        "data": app_data,
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat()
    }
    
    # Initialize processing status
    processing_status[application_id] = {
        "status": "pending",
        "current_agent": None,
        "agents_completed": [],
        "progress_percent": 0
    }
    
    # Start processing in background
    background_tasks.add_task(process_application_task, application_id, app_data)
    
    logger.info(f"Application {application_id} submitted successfully")
    
    return LoanApplicationResponse(
        application_id=application_id,
        status="pending",
        submitted_at=datetime.utcnow(),
        message="Application submitted successfully. Processing will begin shortly."
    )


async def broadcast_agent_update(application_id: str, agent_name: str, status: str, result: dict = None):
    """Broadcast agent status update via WebSocket"""
    message = {
        "type": "agent_update",
        "application_id": application_id,
        "agent": agent_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "result": result
    }
    await ws_manager.broadcast(application_id, message)


async def process_application_task(application_id: str, application_data: dict):
    """Background task to process application with real-time WebSocket updates"""
    try:
        # Prepare message queue for this application
        ws_manager.prepare_for_processing(application_id)
        
        processing_status[application_id]["status"] = "waiting_for_connection"
        print(f"[Processing] Waiting for WebSocket connection for {application_id}...")
        
        # Wait for frontend to connect via WebSocket
        connected = await ws_manager.wait_for_connection(application_id, timeout=20.0)
        
        if connected:
            print(f"[Processing] WebSocket connected! Starting processing for {application_id}")
        else:
            print(f"[Processing] No WebSocket connection, proceeding anyway for {application_id}")
        
        processing_status[application_id]["status"] = "processing"
        
        # Small delay to ensure frontend WebSocket handler is ready
        await asyncio.sleep(0.5)
        
        # Broadcast processing started
        await ws_manager.broadcast(application_id, {
            "type": "processing_started",
            "application_id": application_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        orchestrator = get_orchestrator()
        
        # Define async callback function for real-time updates
        async def agent_status_callback(agent: str, status: str, result_data: dict):
            """Async callback to broadcast agent updates via WebSocket"""
            await broadcast_agent_update(application_id, agent, status, result_data)
        
        # Process with real-time updates using the async callback
        result = await orchestrator.process_application_with_updates(
            application_data,
            agent_status_callback  # Pass the async function directly
        )
        
        # Store decision
        decisions_store[application_id] = result
        
        # Update application status
        decision = result.get("decision", {})
        final_status = "approved" if decision.get("decision") == "APPROVE" else \
                      "denied" if decision.get("decision") == "DENY" else \
                      "conditional" if decision.get("decision") == "CONDITIONAL" else "processed"
        
        applications_store[application_id]["status"] = final_status
        applications_store[application_id]["processed_at"] = datetime.utcnow().isoformat()
        
        processing_status[application_id] = {
            "status": "completed",
            "current_agent": None,
            "agents_completed": list(result.get("agent_results", {}).keys()),
            "progress_percent": 100
        }
        
        # Broadcast completion
        await ws_manager.broadcast(application_id, {
            "type": "processing_completed",
            "application_id": application_id,
            "decision": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Application {application_id} processed: {final_status}")
        
    except Exception as e:
        logger.error(f"Error processing application {application_id}: {str(e)}")
        processing_status[application_id] = {
            "status": "failed",
            "error": str(e),
            "progress_percent": 0
        }
        applications_store[application_id]["status"] = "failed"
        
        # Broadcast error
        await ws_manager.broadcast(application_id, {
            "type": "processing_failed",
            "application_id": application_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


@app.get("/api/v1/applications/{application_id}", tags=["Applications"])
async def get_application(application_id: str):
    """Get application details"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return applications_store[application_id]


@app.get("/api/v1/applications/{application_id}/status", response_model=ApplicationStatusResponse, tags=["Applications"])
async def get_application_status(application_id: str):
    """Get application processing status"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    status = processing_status.get(application_id, {})
    
    return ApplicationStatusResponse(
        application_id=application_id,
        status=status.get("status", "unknown"),
        current_agent=status.get("current_agent"),
        agents_completed=status.get("agents_completed", []),
        progress_percent=status.get("progress_percent", 0),
        estimated_completion_seconds=30 if status.get("status") == "processing" else None
    )


@app.get("/api/v1/applications", tags=["Applications"])
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all applications"""
    apps = list(applications_store.values())
    
    if status:
        apps = [a for a in apps if a.get("status") == status]
    
    # Sort by submission time (newest first)
    apps.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    
    return {
        "total": len(apps),
        "applications": apps[offset:offset + limit],
        "limit": limit,
        "offset": offset
    }


# Decision Endpoints
@app.get("/api/v1/decisions/{application_id}", tags=["Decisions"])
async def get_decision(application_id: str):
    """Get underwriting decision for an application"""
    if application_id not in decisions_store:
        if application_id in applications_store:
            status = applications_store[application_id].get("status")
            if status == "pending" or status == "processing":
                raise HTTPException(
                    status_code=202,
                    detail="Application is still being processed"
                )
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return decisions_store[application_id]


@app.get("/api/v1/decisions/{application_id}/explanation", tags=["Decisions"])
async def get_decision_explanation(application_id: str):
    """Get detailed explanation for a decision"""
    if application_id not in decisions_store:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    decision = decisions_store[application_id]
    explainability_result = decision.get("agent_results", {}).get("Explainability", {})
    
    return {
        "application_id": application_id,
        "decision": decision.get("decision", {}).get("decision"),
        "explanation": explainability_result.get("output", {})
    }


# Underwriting Endpoint
@app.post("/api/v1/underwrite/{application_id}", tags=["Underwriting"])
async def trigger_underwriting(application_id: str, background_tasks: BackgroundTasks):
    """Manually trigger underwriting for an application"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_data = applications_store[application_id]["data"]
    
    # Start processing
    background_tasks.add_task(process_application_task, application_id, app_data)
    
    return {
        "message": "Underwriting process started",
        "application_id": application_id
    }


@app.post("/api/v1/underwrite/sync", tags=["Underwriting"])
async def underwrite_sync(application: LoanApplicationRequest):
    """Synchronously process an application (for testing)"""
    import uuid
    
    application_id = str(uuid.uuid4())
    app_data = application.model_dump()
    
    orchestrator = get_orchestrator()
    result = await orchestrator.process_application(app_data)
    
    # Store results
    applications_store[application_id] = {
        "id": application_id,
        "data": app_data,
        "status": "processed",
        "submitted_at": datetime.utcnow().isoformat(),
        "processed_at": datetime.utcnow().isoformat()
    }
    decisions_store[application_id] = result
    
    return result


# Synthetic Data Endpoints
@app.get("/api/v1/synthetic/application", tags=["Testing"])
async def get_synthetic_application(
    risk_profile: str = Query("random", enum=["low_risk", "medium_risk", "high_risk", "random"])
):
    """Generate a synthetic loan application for testing"""
    return get_sample_application(risk_profile)


@app.post("/api/v1/synthetic/batch", tags=["Testing"])
async def generate_batch_applications(
    count: int = Query(10, ge=1, le=100),
    background_tasks: BackgroundTasks = None
):
    """Generate and submit multiple synthetic applications"""
    applications = SyntheticDataGenerator.generate_batch(count)
    
    submitted = []
    for app_data in applications:
        import uuid
        application_id = str(uuid.uuid4())
        
        # Create request model
        request = LoanApplicationRequest(**app_data)
        
        # Store
        applications_store[application_id] = {
            "id": application_id,
            "data": request.model_dump(),
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        processing_status[application_id] = {
            "status": "pending",
            "current_agent": None,
            "agents_completed": [],
            "progress_percent": 0
        }
        
        submitted.append({
            "application_id": application_id,
            "risk_profile": app_data.get("_metadata", {}).get("risk_profile", "unknown")
        })
    
    return {
        "message": f"Generated {count} synthetic applications",
        "applications": submitted
    }


# Analytics Endpoints
@app.get("/api/v1/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    total = len(applications_store)
    approved = sum(1 for a in applications_store.values() if a.get("status") == "approved")
    denied = sum(1 for a in applications_store.values() if a.get("status") == "denied")
    conditional = sum(1 for a in applications_store.values() if a.get("status") == "conditional")
    pending = sum(1 for a in applications_store.values() if a.get("status") in ["pending", "processing"])
    
    # Calculate metrics
    approval_rate = approved / total if total > 0 else 0
    
    # Calculate average processing time
    processing_times = []
    for decision in decisions_store.values():
        if "processing_time_ms" in decision:
            processing_times.append(decision["processing_time_ms"])
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Calculate average default probability
    default_probs = []
    for decision in decisions_store.values():
        quant_result = decision.get("agent_results", {}).get("QuantitativeRisk", {})
        if quant_result.get("output", {}).get("default_probability"):
            default_probs.append(quant_result["output"]["default_probability"])
    
    avg_default_prob = sum(default_probs) / len(default_probs) if default_probs else 0
    
    # Calculate total loan volume
    total_volume = sum(
        a.get("data", {}).get("loan", {}).get("amount", 0)
        for a in applications_store.values()
        if a.get("status") == "approved"
    )
    
    return DashboardMetrics(
        total_applications=total,
        approved_count=approved,
        denied_count=denied,
        conditional_count=conditional,
        pending_count=pending,
        approval_rate=round(approval_rate, 4),
        avg_processing_time_ms=int(avg_processing_time),
        avg_default_probability=round(avg_default_prob, 4),
        total_loan_volume=total_volume
    )


@app.get("/api/v1/analytics/agent-performance", tags=["Analytics"])
async def get_agent_performance():
    """Get performance metrics for each agent"""
    agent_metrics = {}
    
    for decision in decisions_store.values():
        for agent_name, result in decision.get("agent_results", {}).items():
            if agent_name not in agent_metrics:
                agent_metrics[agent_name] = {
                    "total_executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time_ms": 0,
                    "avg_confidence": []
                }
            
            metrics = agent_metrics[agent_name]
            metrics["total_executions"] += 1
            
            if result.get("status") == "completed":
                metrics["successful"] += 1
            else:
                metrics["failed"] += 1
            
            metrics["total_time_ms"] += result.get("processing_time_ms", 0)
            
            if result.get("confidence"):
                metrics["avg_confidence"].append(result["confidence"])
    
    # Calculate averages
    for agent_name, metrics in agent_metrics.items():
        total = metrics["total_executions"]
        metrics["avg_time_ms"] = metrics["total_time_ms"] / total if total > 0 else 0
        metrics["success_rate"] = metrics["successful"] / total if total > 0 else 0
        metrics["avg_confidence"] = (
            sum(metrics["avg_confidence"]) / len(metrics["avg_confidence"])
            if metrics["avg_confidence"] else 0
        )
        del metrics["total_time_ms"]
    
    return agent_metrics


# WebSocket Endpoint for Real-time Updates
@app.websocket("/ws/{application_id}")
async def websocket_endpoint(websocket: WebSocket, application_id: str):
    """WebSocket endpoint for real-time application processing updates"""
    await ws_manager.connect(websocket, application_id)
    logger.info(f"WebSocket connected for application {application_id}")
    
    try:
        # Send current status immediately upon connection
        if application_id in processing_status:
            await websocket.send_json({
                "type": "status_update",
                "status": processing_status[application_id],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # If decision already exists, send it
        if application_id in decisions_store:
            await websocket.send_json({
                "type": "processing_completed",
                "application_id": application_id,
                "decision": decisions_store[application_id],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Handle ping/pong or other messages
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, application_id)
        logger.info(f"WebSocket disconnected for application {application_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {application_id}: {str(e)}")
        ws_manager.disconnect(websocket, application_id)


# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") == "True" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
