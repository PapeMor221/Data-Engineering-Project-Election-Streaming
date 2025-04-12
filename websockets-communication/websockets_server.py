import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

clients = set()

async def handler(websocket):
    clients.add(websocket)
    logging.info(f"Nouvelle connexion : {websocket.remote_address}")  

    try:
        async for message in websocket:
            logging.info(f"Message reçu de {websocket.remote_address} : {message}") 
        
            await asyncio.gather(*[client.send(message) for client in clients])
    
    except websockets.exceptions.ConnectionClosed as e:
        logging.warning(f"Client déconnecté : {websocket.remote_address} ({e})") 
        
    finally:
        clients.remove(websocket)
        logging.info(f"Client supprimé : {websocket.remote_address}")

# Démarrage du serveur WebSocket
async def main():
    start_server = await websockets.serve(handler, "0.0.0.0", 8765)
    logging.info("Démarrage du serveur WebSocket sur ws://0.0.0.0:8765")
    await start_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())