import { defineConfig } from 'vite';
export default defineConfig({ server: {port: 5178, strictPort: true, proxy: {'/api': 'http://127.0.0.1:8018'}} });
