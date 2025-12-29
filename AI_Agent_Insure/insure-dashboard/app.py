"""
AI Agent Insure: Systems Dashboard
Comprehensive monitoring dashboard for all services in the AI Agent Insure platform
"""
import streamlit as st
import requests
import os
import psycopg2
from pymongo import MongoClient
from typing import Dict, Any, Optional

# Page config
st.set_page_config(
    page_title="AI Agent Insure: Systems Dashboard",
    page_icon="static/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Configuration - Use Docker service names when running in container
ENV = os.getenv("ENVIRONMENT", "container")

# Service URLs - Use Docker service names in container, localhost on host
if ENV == "container":
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb")
    ADMIN_BACKEND_URL = os.getenv("ADMIN_BACKEND_URL", "http://admin-backend:3001")
    CLIENT_BACKEND_URL = os.getenv("CLIENT_BACKEND_URL", "http://client-backend:8001")
    AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://ai-agent:8002")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    CHROMADB_BASE_URL = os.getenv("CHROMADB_BASE_URL", "http://chromadb:8000")
else:
    POSTGRES_HOST = "localhost"
    MONGODB_HOST = "localhost"
    ADMIN_BACKEND_URL = "http://localhost:3001"
    CLIENT_BACKEND_URL = "http://localhost:8001"
    AI_AGENT_URL = "http://localhost:8002"
    OLLAMA_BASE_URL = "http://localhost:11434"
    CHROMADB_BASE_URL = "http://localhost:8000"

# Database credentials
POSTGRES_DB = os.getenv("POSTGRES_DB", "insurance_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "insure_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "insure_secure_pass_2025")
MONGO_USER = os.getenv("MONGO_ROOT_USER", "mongo_admin")
MONGO_PASSWORD = os.getenv("MONGO_ROOT_PASSWORD", "mongo_secure_pass_2025")
MONGO_DB = os.getenv("MONGO_INITDB_DATABASE", "insurance_users")

OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api"
CHROMADB_API_URL = f"{CHROMADB_BASE_URL}/api/v2"

# Hide Streamlit menu and footer, remove top padding
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp > header {
        padding-top: 0 !important;
    }
    div[data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0 !important;
    }
    /* Make tab headings larger */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
    }
    /* Change selected tab color to green */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #4ade80 !important;
        border-bottom-color: #4ade80 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"]:hover {
        color: #4ade80 !important;
    }
    /* Change hover color to green for all tabs */
    button[data-baseweb="tab"]:hover {
        color: #4ade80 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Display shield icon and title
col1, col2 = st.columns([0.05, 0.95])
with col1:
    st.image("static/shield.png", width=50)
with col2:
    st.markdown("<h1 style='margin: 0; padding: 0; line-height: 50px;'>AI Agent Insure: Systems Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("Comprehensive monitoring dashboard for all platform services")

# Helper functions
def format_deployment_log(log_content: str) -> str:
    """
    Format deployment log with HTML styling for better readability.
    Adds color coding for success, errors, warnings, and steps.
    """
    lines = log_content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if not line.strip():
            formatted_lines.append('<br>')
            continue
        
        # Escape HTML special characters
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Color code based on content
        if '✅' in line or 'success' in line.lower() or 'ready' in line.lower():
            formatted_lines.append(f'<span style="color: #4ade80;">{escaped_line}</span>')
        elif '❌' in line or 'error' in line.lower() or 'failed' in line.lower():
            formatted_lines.append(f'<span style="color: #f87171;">{escaped_line}</span>')
        elif '⚠️' in line or 'warning' in line.lower():
            formatted_lines.append(f'<span style="color: #fbbf24;">{escaped_line}</span>')
        elif '🚀' in line or ('Step' in line and ':' in line):
            # Step headers - make them bold and slightly larger
            formatted_lines.append(f'<span style="color: #60a5fa; font-weight: bold;">{escaped_line}</span>')
        elif '🧪' in line or '🐘' in line or '🍃' in line or '📚' in line or '⚙️' in line or '🖥️' in line or '🤖' in line or '📊' in line or '📄' in line or '⏳' in line or '🌐' in line:
            # Step indicators - blue color
            formatted_lines.append(f'<span style="color: #60a5fa;">{escaped_line}</span>')
        elif '🔍' in line or '📥' in line:
            # Info/check indicators - cyan color
            formatted_lines.append(f'<span style="color: #22d3ee;">{escaped_line}</span>')
        elif '🔥' in line or '🛑' in line or '🧹' in line:
            # Destruction/cleanup indicators - orange color
            formatted_lines.append(f'<span style="color: #fb923c;">{escaped_line}</span>')
        else:
            # Default text color
            formatted_lines.append(f'<span style="color: #e5e7eb;">{escaped_line}</span>')
    
    return '<br>'.join(formatted_lines)


def format_deployment_log_with_search(log_content: str, search_query: str, case_sensitive: bool = False) -> str:
    """
    Format deployment log with HTML styling and highlight search terms.
    """
    import re
    
    lines = log_content.split('\n')
    formatted_lines = []
    
    # Escape search query for regex
    escaped_query = re.escape(search_query)
    
    for line in lines:
        if not line.strip():
            formatted_lines.append('<br>')
            continue
        
        # Escape HTML special characters
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Highlight search term
        if case_sensitive:
            pattern = re.compile(f'({escaped_query})', re.IGNORECASE)
        else:
            pattern = re.compile(f'({escaped_query})', re.IGNORECASE)
        
        # Replace matches with highlighted version
        highlighted_line = pattern.sub(
            r'<mark style="background-color: #fbbf24; color: #1e1e1e; padding: 2px 4px; border-radius: 2px; font-weight: bold;">\1</mark>',
            escaped_line
        )
        
        # Color code based on content (apply after highlighting)
        if '✅' in line or 'success' in line.lower() or 'ready' in line.lower():
            formatted_lines.append(f'<span style="color: #4ade80;">{highlighted_line}</span>')
        elif '❌' in line or 'error' in line.lower() or 'failed' in line.lower():
            formatted_lines.append(f'<span style="color: #f87171;">{highlighted_line}</span>')
        elif '⚠️' in line or 'warning' in line.lower():
            formatted_lines.append(f'<span style="color: #fbbf24;">{highlighted_line}</span>')
        elif '🚀' in line or ('Step' in line and ':' in line):
            formatted_lines.append(f'<span style="color: #60a5fa; font-weight: bold;">{highlighted_line}</span>')
        elif '🧪' in line or '🐘' in line or '🍃' in line or '📚' in line or '⚙️' in line or '🖥️' in line or '🤖' in line or '📊' in line or '📄' in line or '⏳' in line or '🌐' in line:
            formatted_lines.append(f'<span style="color: #60a5fa;">{highlighted_line}</span>')
        elif '🔍' in line or '📥' in line:
            formatted_lines.append(f'<span style="color: #22d3ee;">{highlighted_line}</span>')
        elif '🔥' in line or '🛑' in line or '🧹' in line:
            formatted_lines.append(f'<span style="color: #fb923c;">{highlighted_line}</span>')
        else:
            formatted_lines.append(f'<span style="color: #e5e7eb;">{highlighted_line}</span>')
    
    return '<br>'.join(formatted_lines)


def check_service_health(url: str, timeout: int = 5) -> Dict[str, Any]:
    """Check HTTP service health"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            # For AI Agent, check the JSON response status field
            if "/health" in url and "ai-agent" in url:
                try:
                    health_data = response.json()
                    # Use the status from JSON response if available
                    json_status = health_data.get("status", "healthy")
                    return {
                        "status": json_status,  # Can be "healthy" or "degraded"
                        "status_code": response.status_code,
                        "error": None,
                        "health_data": health_data
                    }
                except:
                    # If JSON parsing fails, fall back to HTTP status
                    pass
            return {
                "status": "healthy",
                "status_code": response.status_code,
                "error": None
            }
        else:
            return {
                "status": "unhealthy",
                "status_code": response.status_code,
                "error": None
            }
    except requests.exceptions.ConnectionError:
        return {"status": "unreachable", "status_code": None, "error": "Connection refused"}
    except Exception as e:
        return {"status": "error", "status_code": None, "error": str(e)}

def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL connection and data"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=5432,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()
        
        # Get table counts
        cursor.execute("SELECT COUNT(*) FROM insureds")
        insureds_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM policies")
        policies_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM claims_history")
        claims_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "status": "connected",
            "insureds": insureds_count,
            "policies": policies_count,
            "claims": claims_count,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "insureds": 0,
            "policies": 0,
            "claims": 0,
            "error": str(e)
        }

def check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connection and data"""
    try:
        client = MongoClient(
            f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGODB_HOST}:27017/",
            authSource="admin"
        )
        db = client[MONGO_DB]
        
        # Get collection counts
        user_profiles_count = db.user_profiles.count_documents({})
        query_history_count = db.query_history.count_documents({})
        
        client.close()
        
        return {
            "status": "connected",
            "user_profiles": user_profiles_count,
            "query_history": query_history_count,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "user_profiles": 0,
            "query_history": 0,
            "error": str(e)
        }

def check_chromadb() -> Dict[str, Any]:
    """Check ChromaDB connection and stats"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Connect to ChromaDB
        client = chromadb.HttpClient(
            host=CHROMADB_BASE_URL.replace("http://", "").split(":")[0],
            port=int(CHROMADB_BASE_URL.split(":")[-1]),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Check heartbeat
        client.heartbeat()
        
        # Get collections
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        
        # Get stats for each collection
        collection_stats = {}
        total_documents = 0
        for col_name in collection_names:
            try:
                collection = client.get_collection(col_name)
                count = collection.count()
                collection_stats[col_name] = count
                total_documents += count
            except:
                collection_stats[col_name] = 0
        
        return {
            "status": "connected",
            "collections": len(collection_names),
            "collection_names": collection_names,
            "collection_stats": collection_stats,
            "total_documents": total_documents,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "collections": 0,
            "collection_names": [],
            "collection_stats": {},
            "total_documents": 0,
            "error": str(e)
        }

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📊 Overview",
    "🐘 PostgreSQL",
    "🍃 MongoDB",
    "📚 ChromaDB",
    "⚙️ Admin Backend",
    "📊 Admin Frontend",
    "⚙️ Client Backend",
    "🌐 Client Frontend",
    "🤖 Ollama",
    "🤖 AI Agent",
    "📋 Deployment Logs"
])

# Tab 1: Overview
with tab1:
    st.header("📊 System Overview")
    
    # Check all services
    with st.spinner("Checking services..."):
        postgres_status = check_postgres()
        mongo_status = check_mongodb()
        admin_backend_status = check_service_health(f"{ADMIN_BACKEND_URL}/health")
        client_backend_status = check_service_health(f"{CLIENT_BACKEND_URL}/health")
        admin_frontend_status = check_service_health("http://admin-frontend:3000" if ENV == "container" else "http://localhost:3000")
        client_frontend_status = check_service_health("http://client-frontend:5000" if ENV == "container" else "http://localhost:5001")
        chromadb_status = check_chromadb()
        ollama_status = check_service_health(f"{OLLAMA_API_URL}/tags")
        ai_agent_status = check_service_health(f"{AI_AGENT_URL}/health")
    
    # Calculate overall health
    services = [
        ("PostgreSQL", postgres_status["status"] == "connected"),
        ("MongoDB", mongo_status["status"] == "connected"),
        ("ChromaDB", chromadb_status["status"] == "connected"),
        ("Admin Backend", admin_backend_status["status"] == "healthy"),
        ("Client Backend", client_backend_status["status"] == "healthy"),
        ("Admin Frontend", admin_frontend_status["status"] == "healthy"),
        ("Client Frontend", client_frontend_status["status"] == "healthy"),
        ("Ollama", ollama_status["status"] == "healthy"),
        ("AI Agent", ai_agent_status["status"] == "healthy"),
    ]
    
    healthy_count = sum(1 for _, is_healthy in services if is_healthy)
    total_services = len(services)
    health_percentage = int((healthy_count / total_services) * 100) if total_services > 0 else 0
    
    # Overall Health Gauge Section
    st.markdown("### 🎯 Overall System Health")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Health percentage with color coding
        if health_percentage == 100:
            health_color = "🟢"
            health_label = "All Systems Operational"
        elif health_percentage >= 70:
            health_color = "🟡"
            health_label = "Degraded Performance"
        else:
            health_color = "🔴"
            health_label = "Critical Issues Detected"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     border-radius: 15px; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 48px;">{health_percentage}%</h1>
            <p style="margin: 5px 0; font-size: 18px;">{health_color} {health_label}</p>
            <p style="margin: 5px 0; font-size: 14px; opacity: 0.9;">{healthy_count} of {total_services} services healthy</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        st.progress(health_percentage / 100)
    
    st.divider()
    
    # Service Status Cards
    st.markdown("### 🔍 Service Status")
    
    # Define service info with icons
    service_info = [
        ("🐘", "PostgreSQL", postgres_status["status"] == "connected", postgres_status),
        ("🍃", "MongoDB", mongo_status["status"] == "connected", mongo_status),
        ("📚", "ChromaDB", chromadb_status["status"] == "connected", chromadb_status),
        ("⚙️", "Admin Backend", admin_backend_status["status"] == "healthy", admin_backend_status),
        ("⚙️", "Client Backend", client_backend_status["status"] == "healthy", client_backend_status),
        ("📊", "Admin Frontend", admin_frontend_status["status"] == "healthy", admin_frontend_status),
        ("🌐", "Client Frontend", client_frontend_status["status"] == "healthy", client_frontend_status),
        ("🤖", "Ollama", ollama_status["status"] == "healthy", ollama_status),
        ("🤖", "AI Agent", ai_agent_status["status"] == "healthy", ai_agent_status),
    ]
    
    # Display service cards in a grid
    cols = st.columns(4)
    for idx, (icon, name, is_healthy, status_data) in enumerate(service_info):
        col = cols[idx % 4]
        
        with col:
            # Determine status color and text
            if is_healthy:
                status_color = "#10b981"  # Green
                status_text = "Healthy"
                status_icon = "✅"
            else:
                status_color = "#ef4444"  # Red
                status_text = "Unhealthy"
                status_icon = "❌"
            
            # Determine icon color (blue for Ollama, default for others)
            icon_color = "#3b82f6" if name == "Ollama" else "inherit"
            
            # Create status card
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 10px; border-left: 4px solid {status_color}; 
                         background-color: #f8f9fa; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 24px; color: {icon_color};">{icon}</span>
                        <strong style="font-size: 16px; color: #1f2937;">{name}</strong>
                    </div>
                    <div style="color: {status_color}; font-weight: bold; font-size: 20px;">
                        {status_icon}
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: #6b7280; margin-left: 34px;">
                    {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quick Stats Summary
    st.markdown("### 📈 Quick Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Services", total_services)
    
    with col2:
        st.metric("Healthy Services", healthy_count, delta=f"{health_percentage}%", delta_color="normal" if health_percentage == 100 else "off")
    
    with col3:
        unhealthy_count = total_services - healthy_count
        st.metric("Unhealthy Services", unhealthy_count, delta=f"{100 - health_percentage}%", delta_color="inverse" if unhealthy_count > 0 else "off")
    
    with col4:
        # Calculate total data records
        total_records = 0
        if postgres_status["status"] == "connected":
            total_records += postgres_status.get("insureds", 0) + postgres_status.get("policies", 0) + postgres_status.get("claims", 0)
        if mongo_status["status"] == "connected":
            total_records += mongo_status.get("user_profiles", 0)
        st.metric("Total Records", f"{total_records:,}")
    
    st.divider()
    
    # Data summary
    st.subheader("📊 Data Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if postgres_status["status"] == "connected":
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6; 
                         background-color: #f8f9fa; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">🐘 PostgreSQL</h3>
                <p style="margin: 5px 0; color: #4b5563;"><strong>Insureds:</strong> {postgres_status['insureds']:,}</p>
                <p style="margin: 5px 0; color: #4b5563;"><strong>Policies:</strong> {postgres_status['policies']:,}</p>
                <p style="margin: 5px 0; color: #4b5563;"><strong>Claims:</strong> {postgres_status['claims']:,}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; 
                         background-color: #fef2f2; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">🐘 PostgreSQL</h3>
                <p style="margin: 5px 0; color: #dc2626;">Error: {postgres_status.get('error', 'Unknown error')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if mongo_status["status"] == "connected":
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #10b981; 
                         background-color: #f8f9fa; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">🍃 MongoDB</h3>
                <p style="margin: 5px 0; color: #4b5563;"><strong>User Profiles:</strong> {mongo_status['user_profiles']:,}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; 
                         background-color: #fef2f2; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">🍃 MongoDB</h3>
                <p style="margin: 5px 0; color: #dc2626;">Error: {mongo_status.get('error', 'Unknown error')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if chromadb_status["status"] == "connected":
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #8b5cf6; 
                         background-color: #f8f9fa; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">📚 ChromaDB</h3>
                <p style="margin: 5px 0; color: #4b5563;"><strong>Collections:</strong> {chromadb_status['collections']:,}</p>
                <p style="margin: 5px 0; color: #4b5563;"><strong>Total Documents:</strong> {chromadb_status['total_documents']:,}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; 
                         background-color: #fef2f2; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #1f2937;">📚 ChromaDB</h3>
                <p style="margin: 5px 0; color: #dc2626;">Error: {chromadb_status.get('error', 'Unknown error')}</p>
            </div>
            """, unsafe_allow_html=True)

# Tab 2: PostgreSQL
with tab2:
    st.header("🐘 PostgreSQL Database")
    
    postgres_status = check_postgres()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if postgres_status["status"] == "connected":
            st.success("✅ Connected")
            st.code(f"Host: {POSTGRES_HOST}:5432\nDatabase: {POSTGRES_DB}\nUser: {POSTGRES_USER}")
        else:
            st.error("❌ Connection failed")
            st.error(f"Error: {postgres_status.get('error', 'Unknown error')}")
    
    with col2:
        st.subheader("📊 Data Statistics")
        if postgres_status["status"] == "connected":
            st.metric("Insureds", f"{postgres_status['insureds']:,}")
            st.metric("Policies", f"{postgres_status['policies']:,}")
            st.metric("Claims", f"{postgres_status['claims']:,}")
        else:
            st.warning("Unable to fetch statistics")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Host:** `{POSTGRES_HOST}:5432`")
    st.markdown(f"- **Database:** `{POSTGRES_DB}`")
    st.markdown(f"- **User:** `{POSTGRES_USER}`")

# Tab 3: MongoDB
with tab3:
    st.header("🍃 MongoDB Database")
    
    mongo_status = check_mongodb()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if mongo_status["status"] == "connected":
            st.success("✅ Connected")
            st.code(f"Host: {MONGODB_HOST}:27017\nDatabase: {MONGO_DB}\nUser: {MONGO_USER}")
        else:
            st.error("❌ Connection failed")
            st.error(f"Error: {mongo_status.get('error', 'Unknown error')}")
    
    with col2:
        st.subheader("📊 Data Statistics")
        if mongo_status["status"] == "connected":
            st.metric("User Profiles", f"{mongo_status['user_profiles']:,}")
        else:
            st.warning("Unable to fetch statistics")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Host:** `{MONGODB_HOST}:27017`")
    st.markdown(f"- **Database:** `{MONGO_DB}`")
    st.markdown(f"- **User:** `{MONGO_USER}`")

# Tab 4: ChromaDB
with tab4:
    st.header("📚 ChromaDB Vector Store")
    
    chromadb_status = check_chromadb()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if chromadb_status["status"] == "connected":
            st.success("✅ Connected")
            st.code(f"URL: {CHROMADB_BASE_URL}")
        else:
            st.error("❌ Connection failed")
            st.error(f"Error: {chromadb_status.get('error', 'Unknown error')}")
    
    with col2:
        st.subheader("📊 Statistics")
        if chromadb_status["status"] == "connected":
            st.metric("Collections", chromadb_status["collections"])
            st.metric("Total Documents", f"{chromadb_status['total_documents']:,}")
        else:
            st.warning("Unable to fetch statistics")
    
    st.divider()
    
    if chromadb_status["status"] == "connected":
        st.subheader("📚 Collections")
        if chromadb_status["collections"] > 0:
            for col_name, doc_count in chromadb_status["collection_stats"].items():
                with st.expander(f"📁 {col_name} ({doc_count:,} documents)"):
                    st.write(f"**Collection Name:** `{col_name}`")
                    st.write(f"**Document Count:** {doc_count:,}")
        else:
            st.info("No collections found. Ingest PDFs to create collections.")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Health Check:** [http://localhost:8000/api/v2/heartbeat](http://localhost:8000/api/v2/heartbeat)")
    
    st.subheader("🧪 Test Connection")
    if st.button("Test ChromaDB Connection"):
        try:
            # Use v2 API endpoint
            test_url = f"{CHROMADB_BASE_URL}/api/v2/heartbeat"
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                st.success("✅ ChromaDB is accessible and responding!")
                st.json(response.json())
            else:
                st.error(f"❌ ChromaDB returned status code: {response.status_code}")
                st.text(response.text)
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to ChromaDB. Is it running?")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Tab 5: Admin Backend
with tab5:
    st.header("⚙️ Admin Backend API")
    
    health_status = check_service_health(f"{ADMIN_BACKEND_URL}/health")
    ready_status = check_service_health(f"{ADMIN_BACKEND_URL}/health/ready")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if health_status["status"] == "healthy":
            st.success("✅ Service is running")
            st.code(f"URL: {ADMIN_BACKEND_URL}")
        else:
            st.error("❌ Service unreachable")
            if health_status.get("error"):
                st.error(f"Error: {health_status['error']}")
    
    with col2:
        st.subheader("📊 Status")
        if ready_status["status"] == "healthy":
            st.success("✅ Service is ready")
        else:
            st.warning("⚠️ Service may not be ready")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Health Check:** [http://localhost:3001/health](http://localhost:3001/health)")
    st.markdown(f"- **API Documentation:** [http://localhost:3001/docs](http://localhost:3001/docs)")

# Tab 6: Admin Frontend
with tab6:
    st.header("📊 Admin Frontend")
    
    frontend_url = "http://admin-frontend:3000" if ENV == "container" else "http://localhost:3000"
    frontend_status = check_service_health(frontend_url)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if frontend_status["status"] == "healthy":
            st.success("✅ Service is running")
            st.code(f"URL: {frontend_url}")
        else:
            st.error("❌ Service unreachable")
            if frontend_status.get("error"):
                st.error(f"Error: {frontend_status['error']}")
    
    with col2:
        st.subheader("📊 Status")
        if frontend_status["status"] == "healthy":
            st.success("✅ Frontend is accessible")
        else:
            st.warning("⚠️ Frontend may not be accessible")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Frontend URL:** [http://localhost:3000](http://localhost:3000)")

# Tab 7: Client Backend
with tab7:
    st.header("⚙️ Client Backend API")
    
    health_status = check_service_health(f"{CLIENT_BACKEND_URL}/health")
    ready_status = check_service_health(f"{CLIENT_BACKEND_URL}/health/ready")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if health_status["status"] == "healthy":
            st.success("✅ Service is running")
            st.code(f"URL: {CLIENT_BACKEND_URL}")
        else:
            st.error("❌ Service unreachable")
            if health_status.get("error"):
                st.error(f"Error: {health_status['error']}")
    
    with col2:
        st.subheader("📊 Status")
        if ready_status["status"] == "healthy":
            st.success("✅ Service is ready")
        else:
            st.warning("⚠️ Service may not be ready")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Health Check:** [http://localhost:8001/health](http://localhost:8001/health)")
    st.markdown(f"- **API Documentation:** [http://localhost:8001/docs](http://localhost:8001/docs)")

# Tab 8: Client Frontend
with tab8:
    st.header("🌐 Client Frontend")
    
    frontend_url = "http://client-frontend:5000" if ENV == "container" else "http://localhost:5001"
    frontend_status = check_service_health(frontend_url)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Connection")
        if frontend_status["status"] == "healthy":
            st.success("✅ Service is running")
            st.code(f"URL: {frontend_url}")
        else:
            st.error("❌ Service unreachable")
            if frontend_status.get("error"):
                st.error(f"Error: {frontend_status['error']}")
    
    with col2:
        st.subheader("📊 Status")
        if frontend_status["status"] == "healthy":
            st.success("✅ Frontend is accessible")
        else:
            st.warning("⚠️ Frontend may not be accessible")
    
    st.divider()
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Frontend URL:** [http://localhost:5001](http://localhost:5001)")

# Tab 9: Ollama (preserving original content)
with tab9:
    st.header("🤖 Ollama LLM Service")
    st.markdown("Test interface for Ollama LLM service")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔗 Connection")
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected")
                st.code(f"URL: {OLLAMA_BASE_URL}")
            else:
                st.error("❌ Connection failed")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    with col2:
        st.subheader("📦 Models")
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                st.metric("Available Models", len(models))
                
                if models:
                    st.markdown("**Model List:**")
                    for model in models:
                        st.markdown(f"- `{model['name']}`")
                        with st.expander(f"Details: {model['name']}"):
                            st.json(model)
                else:
                    st.warning("No models found. Pull a model first.")
            else:
                st.warning("Could not fetch models")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    st.divider()
    
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Ollama API:** [http://localhost:11434](http://localhost:11434)")
    st.markdown(f"- **List Models:** [http://localhost:11434/api/tags](http://localhost:11434/api/tags)")

    st.subheader("📚 API Endpoints")
    st.markdown("""
    **Available Endpoints:**
    - `GET /api/tags` - List available models
    - `POST /api/generate` - Generate text
    - `POST /api/chat` - Chat interface
    - `POST /api/pull` - Pull/download a model
    """)

    st.divider()

    st.subheader("🧪 Test Connection")
    if st.button("Test Ollama Connection"):
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=5)
            if response.status_code == 200:
                st.success("✅ Ollama is accessible and responding!")
                st.json(response.json())
            else:
                st.error(f"❌ Ollama returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to Ollama. Is it running?")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Tab 10: AI Agent
with tab10:
    st.header("🤖 AI Agent Intelligent Query API")
    
    health_status = check_service_health(f"{AI_AGENT_URL}/health")
    
    st.subheader("🔗 Connection")
    if health_status["status"] == "healthy":
        st.success("✅ Service is running")
        st.code(f"URL: {AI_AGENT_URL}")
    else:
        st.error("❌ Service unreachable")
        if health_status.get("error"):
            st.error(f"Error: {health_status['error']}")
    
    st.divider()
    
    st.subheader("📊 Dependencies Status")
    # Fetch detailed health information
    try:
        health_response = requests.get(f"{AI_AGENT_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Data Sources:**")
                # ChromaDB
                chromadb_status = "✅ Connected" if health_data.get("chromadb", False) else "❌ Disconnected"
                st.markdown(f"- ChromaDB (Vector Store): {chromadb_status}")
                
                # PostgreSQL
                postgres_status = "✅ Connected" if health_data.get("postgres", False) else "❌ Disconnected"
                st.markdown(f"- PostgreSQL (Structured Data): {postgres_status}")
                
                # MongoDB
                mongodb_status = "✅ Connected" if health_data.get("mongodb", False) else "❌ Disconnected"
                st.markdown(f"- MongoDB (Query History): {mongodb_status}")
            
            with col2:
                st.markdown("**AI Services:**")
                # Ollama
                ollama_status = "✅ Connected" if health_data.get("ollama", False) else "❌ Disconnected"
                st.markdown(f"- Ollama (LLM): {ollama_status}")
                
                # Overall status
                overall_status = health_data.get("status", "unknown")
                status_icon = "✅" if overall_status == "healthy" else "⚠️" if overall_status == "degraded" else "❌"
                st.markdown(f"- **Overall Status:** {status_icon} {overall_status.capitalize()}")
        else:
            st.warning("⚠️ Could not fetch detailed health information")
    except Exception as e:
        st.warning(f"⚠️ Could not fetch dependency status: {str(e)}")
    
    st.divider()
    
    st.subheader("🔗 Quick Links")
    st.markdown(f"- **Health Check:** [http://localhost:8002/health](http://localhost:8002/health)")
    st.markdown(f"- **API Documentation:** [http://localhost:8002/docs](http://localhost:8002/docs)")
    
    st.divider()
    
    st.subheader("📚 API Endpoints")
    st.markdown("""
    **Available Endpoints:**
    - `POST /api/agent/chat/stream` - Streaming chat interface with conversation history and intelligent routing
    - `GET /api/agent/history/{user_id}` - Get user query history
    - `GET /health` - Health check with dependency status
    - `GET /docs` - OpenAPI documentation
    """)
    
    st.divider()
    
    st.subheader("🎯 Query Routing Capabilities")
    st.markdown("""
    The AI Agent intelligently routes queries to the appropriate data source:
    
    - **SQL Queries**: Structured data queries (insureds, policies, claims, statistics)
    - **RAG Queries**: Document-based queries (company info, products, procedures)
    - **Hybrid Queries**: Combines SQL and RAG for comprehensive answers
    """)
    
    st.divider()
    
    st.subheader("🧪 Test Connection")
    if st.button("Test AI Agent Connection"):
        try:
            response = requests.get(f"{AI_AGENT_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ AI Agent is accessible and responding!")
                health_data = response.json()
                st.json(health_data)
            else:
                st.error(f"❌ AI Agent returned status code: {response.status_code}")
                st.text(response.text)
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to AI Agent. Is it running?")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Tab 11: Deployment Logs
with tab11:
    # Clear any potential content overlap
    st.empty()
    st.header("📋 Deployment Logs")
    
    # Log file path - adjust based on environment
    if ENV == "container":
        LOG_FILE = "/app/logs/deploy.log"
    else:
        LOG_FILE = "logs/deploy.log"
    
    # Check if log file exists
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            if log_content.strip():
                # Initialize session state for search if not exists
                if "log_search" not in st.session_state:
                    st.session_state.log_search = ""
                if "log_case_sensitive" not in st.session_state:
                    st.session_state.log_case_sensitive = False
                
                # Search functionality
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    search_query = st.text_input("🔍 Search in log", value=st.session_state.log_search, placeholder="Enter search term...", key="log_search")
                with col2:
                    st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)  # Align checkbox with input bottom
                    case_sensitive = st.checkbox("Case sensitive", value=st.session_state.log_case_sensitive, key="log_case_sensitive")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)  # Align button with input bottom
                    if st.button("Clear", key="clear_search"):
                        # Clear search by deleting the session state key and rerunning
                        del st.session_state.log_search
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Use the search query from the widget
                search_query = st.session_state.get("log_search", "")
                
                # Filter log content based on search
                if search_query:
                    lines = log_content.split('\n')
                    matching_lines = []
                    match_count = 0
                    
                    for line in lines:
                        if case_sensitive:
                            if search_query in line:
                                matching_lines.append(line)
                                match_count += line.count(search_query)
                        else:
                            if search_query.lower() in line.lower():
                                matching_lines.append(line)
                                match_count += line.lower().count(search_query.lower())
                    
                    if matching_lines:
                        filtered_content = '\n'.join(matching_lines)
                        st.success(f"✅ Found {len(matching_lines)} matching line(s) with {match_count} occurrence(s)")
                        
                        # Format filtered content with search term highlighting
                        formatted_log = format_deployment_log_with_search(filtered_content, search_query, case_sensitive)
                    else:
                        st.warning(f"⚠️ No matches found for '{search_query}'")
                        formatted_log = ""
                else:
                    # No search - show full log
                    formatted_log = format_deployment_log(log_content)
                
                st.subheader("Latest Deployment Log")
                
                # Display in a scrollable container with syntax highlighting
                if formatted_log:
                    st.markdown(
                        f'<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 0.5rem; max-height: 600px; overflow-y: auto; font-family: monospace; font-size: 0.9rem;">{formatted_log}</div>',
                        unsafe_allow_html=True
                    )
                
                # Add spacing before download button
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="📥 Download Log File",
                    data=log_content,
                    file_name="deploy.log",
                    mime="text/plain"
                )
            else:
                st.info("📝 Log file exists but is empty. No deployment has been run yet.")
        except Exception as e:
            st.error(f"❌ Error reading log file: {str(e)}")
    else:
        st.info("📝 No deployment log found. Run `./deploy.sh` to create a deployment log.")
        st.markdown("""
        **Note:** The deployment log will be created automatically when you run the deployment script.
        The log file is located at: `logs/deploy.log`
        """)
