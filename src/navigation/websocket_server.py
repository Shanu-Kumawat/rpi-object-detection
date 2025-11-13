#!/usr/bin/env python3
"""
WebSocket Server for Navigation System
Sends real-time alerts to connected Flutter mobile apps
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Set
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NavigationWebSocketServer:
    """WebSocket server for mobile app communication"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Initialize WebSocket server
        
        Args:
            host: Server host (0.0.0.0 = all interfaces)
            port: Server port
        """
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.loop = None
        self.server_thread = None
        self.running = False
        self._stop_event = threading.Event()
        
    async def register_client(self, websocket):
        """Register new client connection"""
        self.connected_clients.add(websocket)
        logger.info(f"📱 Mobile app connected: {websocket.remote_address}. Total: {len(self.connected_clients)}")
        
        # Send welcome message
        welcome = {
            "type": "connection",
            "status": "connected",
            "message": "Connected to Navigation System",
            "timestamp": datetime.now().isoformat()
        }
        try:
            await websocket.send(json.dumps(welcome))
        except:
            pass
    
    async def unregister_client(self, websocket):
        """Remove client connection"""
        self.connected_clients.discard(websocket)
        logger.info(f"📱 Mobile app disconnected: {websocket.remote_address}. Total: {len(self.connected_clients)}")
    
    async def handle_client(self, websocket):
        """Handle individual client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                logger.info(f"Received from app: {message}")
                
                # Handle plain text commands (like "ping")
                if isinstance(message, str) and not message.startswith('{'):
                    message_lower = message.lower().strip()
                    
                    if message_lower == "ping":
                        # Send pong response
                        await websocket.send("pong")
                        continue
                    
                    # Handle other plain text commands if needed
                    continue
                
                # Handle JSON commands
                try:
                    data = json.loads(message)
                    command = data.get("command", "")
                    
                    if command == "ping":
                        response = {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                    
                    elif command == "status":
                        response = {
                            "type": "status",
                            "clients": len(self.connected_clients),
                            "server_running": self.running,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected normally")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def broadcast_alert(self, alert_type: str, message: str, distance: float = None, object_name: str = None):
        """
        Broadcast alert to all connected mobile apps
        
        Args:
            alert_type: Type of alert ("critical", "warning", "info")
            message: Alert message text
            distance: Distance in meters (optional)
            object_name: Detected object name (optional)
        """
        if not self.connected_clients:
            return
        
        alert_data = {
            "type": "alert",
            "alert_type": alert_type,
            "message": message,
            "distance": distance,
            "object": object_name,
            "timestamp": datetime.now().isoformat(),
            "vibrate": alert_type == "critical"  # Trigger vibration for critical alerts
        }
        
        # Send to all connected clients
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(alert_data))
                logger.info(f"📤 Sent alert to {client.remote_address}: {alert_type}")
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Clean up disconnected clients
        self.connected_clients -= disconnected
    
    def broadcast_alert_sync(self, alert_type: str, message: str, distance: float = None, object_name: str = None):
        """
        Synchronous wrapper for broadcasting alerts (call from main thread)
        
        Args:
            alert_type: Type of alert ("critical", "warning", "info")
            message: Alert message text
            distance: Distance in meters (optional)
            object_name: Detected object name (optional)
        """
        if self.loop and self.running and not self._stop_event.is_set():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_alert(alert_type, message, distance, object_name),
                    self.loop
                )
            except Exception as e:
                logger.error(f"Error broadcasting alert: {e}")
    
    async def _run_server(self):
        """Internal method to run WebSocket server"""
        logger.info(f"🚀 Starting WebSocket server on {self.host}:{self.port}")
        
        try:
            async with websockets.serve(self.handle_client, self.host, self.port) as server:
                self.server = server
                self.running = True
                logger.info("✅ WebSocket server started! Waiting for mobile app connections...")
                
                # Wait until stop is requested
                while not self._stop_event.is_set():
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"❌ WebSocket server error: {e}")
        finally:
            self.running = False
    
    def start(self):
        """Start WebSocket server in background thread"""
        def run_in_thread():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self._run_server())
            except Exception as e:
                logger.error(f"Server thread error: {e}")
            finally:
                try:
                    self.loop.close()
                except:
                    pass
        
        self._stop_event.clear()
        self.server_thread = threading.Thread(target=run_in_thread, daemon=True)
        self.server_thread.start()
        logger.info("🔧 WebSocket server thread started")
    
    def stop(self):
        """Stop WebSocket server"""
        logger.info("🛑 Stopping WebSocket server...")
        self.running = False
        self._stop_event.set()
        
        # Give it time to cleanup
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        
        logger.info("🛑 WebSocket server stopped")


# Test function
async def test_server():
    """Test WebSocket server"""
    server = NavigationWebSocketServer(host="0.0.0.0", port=8765)
    
    # Start server in background
    asyncio.create_task(server._run_server())
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Simulate alerts every 3 seconds
    for i in range(5):
        await asyncio.sleep(3)
        
        if i % 2 == 0:
            await server.broadcast_alert(
                "critical",
                "Stop! Person ahead",
                distance=1.5,
                object_name="person"
            )
        else:
            await server.broadcast_alert(
                "warning",
                "Chair in front",
                distance=2.8,
                object_name="chair"
            )
    
    server.stop()


if __name__ == '__main__':
    # Test the server
    asyncio.run(test_server())
