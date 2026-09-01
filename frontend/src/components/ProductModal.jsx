import React, { useState, useMemo } from 'react';
import { X, TrendingDown, TrendingUp, DollarSign, Target, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
const ProductModal = ({ product, onClose }) => {
  const [timeRange, setTimeRange] = useState('1M'); 
  const filteredHistory = useMemo(() => {
    if (!product.history || product.history.length === 0) return [];
    const now = new Date();
    let cutoffDate = new Date();
    switch (timeRange) {
      case '1W':
        cutoffDate.setDate(now.getDate() - 7);
        break;
      case '1M':
        cutoffDate.setMonth(now.getMonth() - 1);
        break;
      case '6M':
        cutoffDate.setMonth(now.getMonth() - 6);
        break;
      case 'MAX':
      default:
        cutoffDate = new Date(0); 
        break;
    }
    return product.history.filter(pt => new Date(pt.date) >= cutoffDate);
  }, [product.history, timeRange]);
  const stats = useMemo(() => {
    if (!product.history || product.history.length === 0) return null;
    const prices = product.history.map(pt => pt.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    return {
      min: minPrice,
      max: maxPrice,
      avg: avgPrice
    };
  }, [product.history]);
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ marginBottom: 0 }}>{product.name}</h2>
            <div className="text-muted text-small" style={{ marginTop: '0.2rem' }}>
              Added on {product.created_at}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        <div className="modal-body">
          {}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="toggle-group">
              {['1W', '1M', '6M', 'MAX'].map(range => (
                <button 
                  key={range}
                  className={`toggle-btn ${timeRange === range ? 'active' : ''}`}
                  onClick={() => setTimeRange(range)}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
          {}
          <div style={{ height: '300px', width: '100%' }}>
            {filteredHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredHistory} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-border)" vertical={false} />
                  <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickFormatter={(tick) => tick.split(' ')[0]} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} domain={['auto', 'auto']} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--surface-color)', borderColor: 'var(--surface-border)', color: 'var(--text-main)' }}
                    itemStyle={{ color: 'var(--primary-color)' }}
                    formatter={(value) => [`${value} RON`, 'Price']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="var(--primary-color)" 
                    strokeWidth={3}
                    dot={{ r: 4, fill: 'var(--surface-color)', stroke: 'var(--primary-color)', strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: 'var(--primary-color)' }}
                    animationDuration={1500}
                    animationEasing="ease-in-out"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--surface-border)', borderRadius: '6px' }}>
                <span className="text-muted">No data in this timeframe</span>
              </div>
            )}
          </div>
          {}
          {stats && (
            <div className="stats-grid">
              <div className="stat-box">
                <div className="stat-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                  <TrendingDown size={14} /> Lowest Price
                </div>
                <div className="stat-box-value" style={{ color: 'var(--success-color)' }}>
                  {stats.min.toLocaleString()} RON
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                  <TrendingUp size={14} /> Highest Price
                </div>
                <div className="stat-box-value">
                  {stats.max.toLocaleString()} RON
                </div>
              </div>
              <div className="stat-box">
                <div className="stat-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                  <DollarSign size={14} /> Average Price
                </div>
                <div className="stat-box-value text-muted">
                  {stats.avg.toFixed(2)} RON
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default ProductModal;