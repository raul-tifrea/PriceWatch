import axios from 'axios';
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});
const stored = localStorage.getItem('pw_token');
if (stored) {
  api.defaults.headers.common['Authorization'] = `Bearer ${stored}`;
}
export const getProducts = async () => {
  const response = await api.get('/products');
  return response.data;
};
export const addProduct = async (name, url) => {
  const response = await api.post('/products', { name, url });
  return response.data;
};
export const removeProduct = async (id) => {
  const response = await api.delete(`/products/${id}`);
  return response.data;
};
export const refreshPrices = async () => {
  const response = await api.post('/refresh');
  return response.data;
};
export default api;