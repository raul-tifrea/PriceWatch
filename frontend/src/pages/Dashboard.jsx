import React, { useState, useEffect } from 'react';
import { getProducts, removeProduct, refreshPrices } from '../api';
import { RefreshCw } from 'lucide-react';
import ProductCard from '../components/ProductCard';

function Dashboard() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

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
        <div className="products-grid">
          {products.map(product => (
            <ProductCard 
              key={product.id} 
              product={product} 
              onRemove={handleRemove} 
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
