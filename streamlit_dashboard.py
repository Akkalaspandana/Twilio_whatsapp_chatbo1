import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Invock Demo Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stApp {
        background-color: #000000;
    }
    .stSidebar {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stDataFrame {
        background-color: #1A1A1A;
        color: #FFFFFF;
    }
    .stMetric {
        background-color: #1A1A1A;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 10px;
    }
    .stAlert {
        background-color: #1A1A1A;
        border: 1px solid #333333;
        color: #FFFFFF;
    }
    .stButton > button {
        background-color: #000000;
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: #1A1A1A;
        border-color: #666666;
    }
</style>
""", unsafe_allow_html=True)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'invock_db',
    'user': 'postgres',
    'password': 'spandana.45@S',
    'port': '5432'
}

def get_database_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def get_user_data():
    """Fetch all user data from database"""
    conn = get_database_connection()
    if conn is None:
        return None
    
    try:
        query = """
        SELECT 
            id,
            name,
            email,
            business_name,
            demo_date,
            demo_time,
            created_at
        FROM users 
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        conn.close()
        return None

def main():
    # Header
    st.title("📊 Invock Demo Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Dashboard Controls")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Date filter
    st.sidebar.markdown("### 📅 Date Filter")
    date_filter = st.sidebar.selectbox(
        "Filter by date range:",
        ["All Time", "Today", "Last 7 Days", "Last 30 Days", "This Month"]
    )
    
    # Fetch data
    df = get_user_data()
    
    if df is None or df.empty:
        st.warning("No data available in the database.")
        return
    
    # Apply date filter
    if date_filter != "All Time":
        today = datetime.now()
        if date_filter == "Today":
            df = df[df['created_at'].dt.date == today.date()]
        elif date_filter == "Last 7 Days":
            df = df[df['created_at'] >= today - pd.Timedelta(days=7)]
        elif date_filter == "Last 30 Days":
            df = df[df['created_at'] >= today - pd.Timedelta(days=30)]
        elif date_filter == "This Month":
            df = df[df['created_at'].dt.month == today.month]
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Users",
            value=len(df),
            delta=f"+{len(df)} total registrations"
        )
    
    with col2:
        today_users = len(df[df['created_at'].dt.date == datetime.now().date()])
        st.metric(
            label="Today's Registrations",
            value=today_users,
            delta=f"+{today_users} today"
        )
    
    with col3:
        unique_businesses = df['business_name'].nunique()
        st.metric(
            label="Unique Businesses",
            value=unique_businesses
        )
    
    with col4:
        avg_daily = len(df) / max(1, (datetime.now() - df['created_at'].min()).days)
        st.metric(
            label="Avg Daily Registrations",
            value=f"{avg_daily:.1f}"
        )
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Registration Trend")
        if len(df) > 1:
            daily_registrations = df.groupby(df['created_at'].dt.date).size().reset_index()
            daily_registrations.columns = ['Date', 'Registrations']
            
            fig = px.line(
                daily_registrations, 
                x='Date', 
                y='Registrations',
                title="Daily User Registrations",
                color_discrete_sequence=['#00FF00']
            )
            fig.update_layout(
                plot_bgcolor='#1A1A1A',
                paper_bgcolor='#1A1A1A',
                font=dict(color='#FFFFFF'),
                xaxis=dict(gridcolor='#333333'),
                yaxis=dict(gridcolor='#333333')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need more data to show trend chart")
    
    with col2:
        st.subheader("🏢 Top Business Types")
        if len(df) > 0:
            business_counts = df['business_name'].value_counts().head(10)
            
            fig = px.bar(
                x=business_counts.values,
                y=business_counts.index,
                orientation='h',
                title="Most Common Business Names",
                color_discrete_sequence=['#00FF00']
            )
            fig.update_layout(
                plot_bgcolor='#1A1A1A',
                paper_bgcolor='#1A1A1A',
                font=dict(color='#FFFFFF'),
                xaxis=dict(gridcolor='#333333'),
                yaxis=dict(gridcolor='#333333')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No business data available")
    
    st.markdown("---")
    
    # Detailed Data Table
    st.subheader("📋 User Details")
    
    # Search functionality
    search_term = st.text_input("🔍 Search by name, email, or business:", "")
    
    if search_term:
        filtered_df = df[
            df['name'].str.contains(search_term, case=False, na=False) |
            df['email'].str.contains(search_term, case=False, na=False) |
            df['business_name'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_df = df
    
    # Display data
    if not filtered_df.empty:
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Rename columns for better display
        display_df = display_df.rename(columns={
            'id': 'ID',
            'name': 'Name',
            'email': 'Email',
            'business_name': 'Business Name',
            'demo_date': 'Demo Date',
            'demo_time': 'Demo Time',
            'created_at': 'Registration Date'
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export functionality
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"invock_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.info(f"Showing {len(filtered_df)} of {len(df)} total users")
    else:
        st.warning("No users found matching your search criteria.")
    
    # Recent Activity
    st.markdown("---")
    st.subheader("🕒 Recent Activity")
    
    recent_users = df.head(5)
    for _, user in recent_users.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{user['name']}** ({user['email']})")
            with col2:
                st.write(f"🏢 {user['business_name']}")
            with col3:
                st.write(f"📅 {user['created_at'].strftime('%Y-%m-%d %H:%M')}")
            st.markdown("---")

if __name__ == "__main__":
    main()
