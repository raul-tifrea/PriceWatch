"""Streamlit dashboard for PriceWatch."""
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

from pricewatch.infrastructure.db.engine import SessionLocal
from pricewatch.application.use_cases import AddProduct, RefreshPrices, GetPriceHistory
from pricewatch.infrastructure.db.repositories import ProductRepository, PriceRepository
from pricewatch.infrastructure.scrapers.factory import ScraperFactory
from pricewatch.domain.events import PriceEventBus

# --- Page Config ---
st.set_page_config(
    page_title="PriceWatch Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Modern, sleek typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Make the title pop with a gradient */
    h1 {
        background: -webkit-linear-gradient(45deg, #FF416C, #FF4B2B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 0rem;
    }
    
    /* Subtle card styling for product items */
    .product-card {
        padding: 1.5rem;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s, background 0.2s;
    }
    .product-card:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# --- Dependencies ---
@st.cache_resource
def get_event_bus():
    # In a real app, we'd wire up the real Notifiers here, or rely on the background APScheduler.
    # For the UI's manual refresh, we can just use a dummy bus or the real one.
    return PriceEventBus()

@st.cache_resource
def get_factory():
    return ScraperFactory()

def get_session():
    return SessionLocal()


# --- UI ---

st.title("PriceWatch")
st.markdown("Track prices across top retailers and get notified on drops.")

# 1. Add Product Form
with st.container():
    st.markdown("### 🛍️ Track a new product")
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("What are you looking for?", placeholder="e.g. iPhone 15 Pro 256GB")
        with col2:
            target = st.number_input("Target Price Drop (Optional)", min_value=0.0, step=100.0, format="%.2f")
            
        submit = st.form_submit_button("Start Tracking", type="primary")
        
        if submit and query:
            with st.spinner("Adding product..."):
                session = get_session()
                try:
                    use_case = AddProduct(session)
                    use_case.execute(
                        name=query,  # We just use the query as the name for simplicity
                        search_query=query,
                        target_price=target if target > 0 else None
                    )
                    st.toast(f"Successfully tracking: {query}", icon="✅")
                finally:
                    session.close()


# 2. Controls
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🔄 Refresh All Prices Now", type="primary"):
        with st.spinner("Scraping active retailers..."):
            session = get_session()
            try:
                RefreshPrices(session, get_factory(), get_event_bus()).execute()
                st.toast("Prices refreshed!", icon="🎉")
            except Exception as e:
                st.error(f"Error during refresh: {e}")
            finally:
                session.close()

st.divider()

# 3. Product Dashboard
st.markdown("### 📊 Your Tracked Products")

session = get_session()
try:
    product_repo = ProductRepository(session)
    price_repo = PriceRepository(session)
    history_use_case = GetPriceHistory(session)
    
    products = product_repo.list_all()
    
    if not products:
        st.info("You aren't tracking any products yet. Add one above!")
    else:
        for product in products:
            with st.container():
                st.markdown(f"#### {product.name}")
                st.caption(f"Added: {product.created_at.strftime('%Y-%m-%d')} | ID: {product.id}")
                
                # Fetch history
                history = history_use_case.execute(product.id)
                # history is dict[retailer_id, list[PricePoint]]
                
                if not history:
                    st.warning("No price data yet. Try refreshing prices.")
                    st.divider()
                    continue
                
                # Build a dataframe for Plotly
                rows = []
                current_prices = {}
                
                for retailer_id, points in history.items():
                    if points:
                        current_prices[retailer_id] = points[-1].price
                    for pt in points:
                        rows.append({
                            "Retailer": retailer_id,
                            "Price": float(pt.price),
                            "Date": pt.recorded_at
                        })
                
                df = pd.DataFrame(rows)
                
                col1, col2 = st.columns([1, 3])
                
                # Left column: Current prices
                with col1:
                    for retailer_id, price in current_prices.items():
                        st.metric(label=retailer_id, value=f"{price:,.2f} RON")
                
                # Right column: Plotly Chart
                with col2:
                    if not df.empty:
                        fig = px.line(
                            df, 
                            x="Date", 
                            y="Price", 
                            color="Retailer",
                            markers=True,
                            title="Price History",
                            template="plotly_dark",
                        )
                        fig.update_layout(
                            xaxis_title="", 
                            yaxis_title="Price (RON)",
                            margin=dict(l=0, r=0, t=40, b=0),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        # Make line shape step-like to represent price changes accurately
                        fig.update_traces(line_shape='vh') 
                        st.plotly_chart(fig, width='stretch')
                    else:
                        st.info("Not enough data to plot.")
                        
                st.divider()

finally:
    session.close()
