import React, { useState } from 'react';
import { Trash2, ExternalLink } from 'lucide-react';
import ProductModal from './ProductModal';

const ProductCard = ({ product, onRemove }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Calculate percentage change since first added (overall savings)
  let percentageChange = 0;
  if (product.initial_price && product.current_price) {
    percentageChange = ((product.current_price - product.initial_price) / product.initial_price) * 100;
  }

  let badgeClass = "badge-neutral";
  let badgeText = "0%";
  
  if (percentageChange < -0.1) {
    badgeClass = "badge-success";
    badgeText = `${percentageChange.toFixed(1)}% (Drop)`;
  } else if (percentageChange > 0.1) {
    badgeClass = "badge-danger";
    badgeText = `+${percentageChange.toFixed(1)}% (Up)`;
  }

  const isGreatDeal = percentageChange <= -10; // 10% or more drop

  let retailerName = 'Unknown';
  let retailerBadgeClass = 'badge-unknown';
  try {
    const urlObj = new URL(product.url);
    const hostname = urlObj.hostname.toLowerCase();
    if (hostname.includes('cel.ro')) {
      retailerName = 'CEL.ro';
      retailerBadgeClass = 'badge-celro';
    } else if (hostname.includes('altex.ro')) {
      retailerName = 'Altex';
      retailerBadgeClass = 'badge-altex';
    } else {
      retailerName = hostname.replace('www.', '');
    }
  } catch (e) {
    // Ignore
  }

  const handleCardClick = (e) => {
    // Prevent opening modal if clicking on the remove button or the link
    if (e.target.closest('button') || e.target.closest('a')) {
      return;
    }
    setIsModalOpen(true);
  };

  return (
    <>
      <div 
        className="card" 
        onClick={handleCardClick}
        style={{ 
          cursor: 'pointer', 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          position: 'relative',
          ...(isGreatDeal ? { boxShadow: '0 0 20px rgba(63, 185, 80, 0.3)', borderColor: 'rgba(63, 185, 80, 0.5)' } : {})
        }}
      >
        <div className="card-header" style={{ alignItems: 'flex-start' }}>
          <div>
            <div style={{ marginBottom: '0.5rem' }}>
              <span className={`badge ${retailerBadgeClass}`} style={{ padding: '0.1rem 0.5rem', fontSize: '0.75rem' }}>
                {retailerName}
              </span>
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.2rem', lineHeight: '1.3' }}>{product.name}</h3>
            <a 
              href={product.url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-muted text-small" 
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}
              onClick={e => e.stopPropagation()}
            >
              View on Retailer <ExternalLink size={12} />
            </a>
          </div>
          <button 
            className="btn btn-danger" 
            style={{ padding: '0.4rem' }}
            onClick={(e) => { e.stopPropagation(); onRemove(product.id); }}
            title="Remove product"
          >
            <Trash2 size={16} />
          </button>
        </div>
        
        <div style={{ marginTop: 'auto', paddingTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <div className="text-muted text-small" style={{ marginBottom: '0.2rem' }}>Current Price</div>
            <span className="price-tag">
              {product.current_price ? `${product.current_price.toLocaleString()} RON` : 'N/A'}
            </span>
          </div>
          <div>
            <span className={`badge ${badgeClass}`}>
              {badgeText}
            </span>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <ProductModal 
          product={product} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </>
  );
};

export default ProductCard;
