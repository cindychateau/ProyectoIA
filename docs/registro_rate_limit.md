## Registro del ensayo de rate limit
 
- Fecha: 2026-09-09
- Peticiones enviadas: 10
- Petición donde apareció el primer 429: la número 6
- Esperas observadas: 2.1s, 4.3s, 8.2s (backoff exponencial con jitter, correcto)
- Costo total del ensayo: $0.00042
- Resultado: todas las peticiones terminaron con éxito tras reintentar