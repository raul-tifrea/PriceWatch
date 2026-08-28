import React, { useState, useEffect } from 'react';
import { getProducts, removeProduct, refreshPrices } from '../api';
import { RefreshCw } from 'lucide-react';
import ProductCard from '../components/ProductCard';
function Dashboard() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState('newest'); 
  const fetchProducts = async () => {
    try {
      const data = await getProducts();
      setProducts(data);
    } catch (error) {
      console.error("Failed to fetch products", error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchProducts();
    const interval = setInterval(() => {
      fetchProducts();
    }, 60000);
    return () => clearInterval(interval);
  }, []);
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshPrices();
      await fetchProducts();
    } catch (error) {
      console.error("Failed to refresh prices", error);
    } finally {
      setRefreshing(false);
    }
  };
  const handleRemove = async (id) => {
    if (!window.confirm("Are you sure you want to stop tracking this product?")) return;
    try {
      await removeProduct(id);
      setProducts(products.filter(p => p.id !== id));
    } catch (error) {
      console.error("Failed to remove product", error);
    }
  };
  const sortedProducts = [...products].sort((a, b) => {
    if (sortBy === 'newest') {
      return new Date(b.created_at) - new Date(a.created_at);
    }
    if (sortBy === 'price-asc') {
      return (a.current_price || 0) - (b.current_price || 0);
    }
    if (sortBy === 'price-desc') {
      return (b.current_price || 0) - (a.current_price || 0);
    }
    if (sortBy === 'drop') {
      const dropA = a.initial_price && a.current_price ? ((a.current_price - a.initial_price) / a.initial_price) : 0;
      const dropB = b.initial_price && b.current_price ? ((b.current_price - b.initial_price) / b.initial_price) : 0;
      return dropA - dropB; 
    }
    return 0;
  });
  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading products...</div>;
  }
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Tracked Products</h2>
        <button 
          className="btn btn-primary" 
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={18} className={refreshing ? "spinner" : ""} />
          {refreshing ? "Scraping..." : "Refresh Prices Now"}
        </button>
      </div>
      {products.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <p className="text-muted" style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>You aren't tracking any products yet.</p>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <span className="text-muted text-small">Sort by:</span>
            <div className="toggle-group">
              <button className={`toggle-btn ${sortBy === 'newest' ? 'active' : ''}`} onClick={() => setSortBy('newest')}>Newest</button>
              <button className={`toggle-btn ${sortBy === 'drop' ? 'active' : ''}`} onClick={() => setSortBy('drop')}>Biggest Drop</button>
              <button className={`toggle-btn ${sortBy === 'price-asc' ? 'active' : ''}`} onClick={() => setSortBy('price-asc')}>Price: Low</button>
              <button className={`toggle-btn ${sortBy === 'price-desc' ? 'active' : ''}`} onClick={() => setSortBy('price-desc')}>Price: High</button>
            </div>
          </div>
          <div className="products-grid">
            {sortedProducts.map(product => (
            <ProductCard 
              key={product.id} 
              product={product} 
              onRemove={handleRemove} 
            />
          ))}
        </div>
        </>
      )}
    </div>
  );
}
export default Dashboard;