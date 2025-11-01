

# Core features - streamlined and focused
FEATURE_ICONS = {
    "News Verification": "📰",
    "Live News Feed": "📡", 
    "Article Summary": "📋",
    "URL Analysis": "🔗",
    "Geographic News Map": "�️",
    "Translation": "🌐",
    "Source Checker": "🏛️"
}

# Custom CSS styling
CUSTOM_CSS = """
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2E86C1;
        --secondary-color: #1ABC9C;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2E86C1 100%);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Sidebar text color */
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Sidebar selectbox styling */
    [data-testid="stSidebar"] .stSelectbox label {
        font-size: 1.1em;
        font-weight: 600;
        color: #ffffff !important;
    }
    
    /* Main content area - cleaner, more spacious */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }
    
    /* Headers - more subtle styling */
    h1 {
        color: #1a365d;
        font-weight: 600;
        font-size: 2.2rem;
        margin-bottom: 1rem;
    }
    
    h2, h3 {
        color: #2d3748;
        font-weight: 500;
        margin-bottom: 0.8rem;
    }
    
    /* Cards - cleaner design */
    .content-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    /* Buttons - less flashy */
    .stButton>button {
        background-color: #3182ce;
        color: white;
        font-weight: 500;
        border: none;
        border-radius: 4px;
        padding: 0.6rem 1.5rem;
        transition: background-color 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #2c5282;
        transform: none;
        box-shadow: none;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Success/Warning/Error boxes */
    .stSuccess {
        background-color: #D5F4E6;
        border-left: 4px solid #28B463;
    }
    
    .stWarning {
        background-color: #FCF3CF;
        border-left: 4px solid #F39C12;
    }
    
    .stError {
        background-color: #FADBD8;
        border-left: 4px solid #E74C3C;
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 2px solid #E8E8E8;
        padding: 0.75rem;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #2E86C1;
        box-shadow: 0 0 0 0.2rem rgba(46,134,193,0.25);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #F0F2F6;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar header */
    .sidebar-header {
        padding: 1rem 0;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Content sections */
    .content-section {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    /* Info boxes */
    .info-box {
        background: #E8F4FD;
        border-left: 4px solid #2E86C1;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
"""
