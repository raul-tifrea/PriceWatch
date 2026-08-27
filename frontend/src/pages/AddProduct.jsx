import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addProduct } from '../api';
import { PlusCircle, Link as LinkIcon, Tag, Bell } from 'lucide-react';

function AddProduct() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    targetPrice: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const target = parseFloat(formData.targetPrice);
      await addProduct(
        formData.name, 
        formData.url, 
        isNaN(target) || target <= 0 ? null : target
      );
      navigate('/');
    } catch (err) {
      console.error(err);
      setError("Failed to add product. Make sure the backend is running and the URL is valid.");
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Track a New Product</h2>
      
      <div className="card">
        {error && (
          <div style={{ backgroundColor: 'rgba(248, 81, 73, 0.1)', color: 'var(--danger-color)', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem', border: '1px solid rgba(248, 81, 73, 0.4)' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Tag size={16} /> Product Name
            </label>
            <input 
              type="text" 
              className="form-control"
              name="name"
              placeholder="e.g. iPhone 15 Pro Max"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <LinkIcon size={16} /> Retailer URL
            </label>
            <input 
              type="url" 
              className="form-control"
              name="url"
              placeholder="https://www.cel.ro/..."
              value={formData.url}
              onChange={handleChange}
              required
            />
            <small className="text-muted" style={{ display: 'block', marginTop: '0.4rem' }}>Currently supported: cel.ro</small>
          </div>
          
          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Bell size={16} /> Alert Threshold (RON)
            </label>
            <input 
              type="number" 
              className="form-control"
              name="targetPrice"
              placeholder="e.g. 5000"
              min="0"
              step="0.01"
              value={formData.targetPrice}
              onChange={handleChange}
            />
            <small className="text-muted" style={{ display: 'block', marginTop: '0.4rem' }}>Optional. We'll alert you if the price drops below this amount.</small>
          </div>
          
          <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 1, padding: '0.8rem' }}>
              {loading ? (
                <>Adding...</>
              ) : (
                <><PlusCircle size={18} /> Start Tracking</>
              )}
            </button>
            <button type="button" className="btn btn-outline" onClick={() => navigate('/')} disabled={loading} style={{ padding: '0.8rem' }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddProduct;
