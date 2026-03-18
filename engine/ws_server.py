"""
WebSocket server for live molecular evolution streaming.

Broadcasts generation-by-generation evolution data to connected
web clients. Pattern matches antenna-evolution/engine/ws_server.py.

HTTP API on port 8790, WebSocket on port 8791.
"""

import asyncio
import json
import threading
import traceback
from http.server import HTTPServer

from .evolver import EvolutionConfig, run_evolution, save_results, GenerationStats
from .serve import CORSHandler, PORT as HTTP_PORT

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

WS_PORT = 8791


class EvolutionManager:
    """Manages a running evolution job and broadcasts to WS clients."""

    def __init__(self):
        self.clients = set()
        self.running = False
        self.config = None
        self.thread = None
        self.loop = None

    def register(self, ws):
        self.clients.add(ws)

    def unregister(self, ws):
        self.clients.discard(ws)

    def broadcast(self, message: dict):
        if not self.clients or self.loop is None:
            return
        data = json.dumps(message, default=str)
        for ws in list(self.clients):
            try:
                asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)
            except Exception:
                self.clients.discard(ws)

    def start_evolution(self, config: EvolutionConfig):
        if self.running:
            self.broadcast({'type': 'error', 'message': 'Evolution already running'})
            return

        self.config = config
        self.running = True
        self.broadcast({'type': 'status', 'status': 'starting', 'config': config.to_dict()})

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop_evolution(self):
        self.running = False
        self.broadcast({'type': 'status', 'status': 'stopped'})

    def _run(self):
        try:
            def on_generation(gen, stats):
                if not self.running:
                    raise StopIteration("Evolution stopped by user")
                self.broadcast({
                    'type': 'generation',
                    'generation': gen,
                    **stats,
                })

            history = run_evolution(self.config, callback=on_generation)
            save_results(self.config, history)

            # Send completion
            if history:
                last = history[-1]
                self.broadcast({
                    'type': 'complete',
                    'generations': len(history),
                    'best_fitness': last.best_fitness,
                    'best_molecule': last.best_molecule,
                    'best_properties': last.best_properties,
                })
        except StopIteration:
            pass
        except Exception as e:
            self.broadcast({
                'type': 'error',
                'message': str(e),
                'traceback': traceback.format_exc(),
            })
        finally:
            self.running = False


manager = EvolutionManager()


async def ws_handler(websocket, path=None):
    """Handle a WebSocket connection."""
    manager.register(websocket)
    try:
        # Send current status
        await websocket.send(json.dumps({
            'type': 'status',
            'status': 'running' if manager.running else 'idle',
        }))

        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get('action')

            if action == 'start':
                config_data = msg.get('config', {})
                config = EvolutionConfig.from_dict(config_data)
                if config.run_name == 'default':
                    import time
                    config.run_name = f"run_{int(time.time())}"
                manager.start_evolution(config)

            elif action == 'stop':
                manager.stop_evolution()

            elif action == 'status':
                await websocket.send(json.dumps({
                    'type': 'status',
                    'status': 'running' if manager.running else 'idle',
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        manager.unregister(websocket)


async def main_async():
    """Run both HTTP and WebSocket servers."""
    # HTTP server in a thread
    http_server = HTTPServer(('', HTTP_PORT), CORSHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    print(f"HTTP API server on http://localhost:{HTTP_PORT}")

    # WebSocket server
    manager.loop = asyncio.get_event_loop()
    async with websockets.serve(ws_handler, '', WS_PORT):
        print(f"WebSocket server on ws://localhost:{WS_PORT}")
        print("Ready. Connect from the web dashboard to start evolution.")
        await asyncio.Future()  # run forever


def main():
    if not HAS_WEBSOCKETS:
        print("ERROR: websockets package required. Install with:")
        print("  pip install websockets")
        return
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
