import axios from 'axios';
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});
export const getProducts = async () => {
  const response = await api.get('/products');
  return response.data;
};
export const addProduct = async (name, url) => {
  const payload = { name, url };
  const response = await api.post('/products', payload);
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