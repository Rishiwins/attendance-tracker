#!/usr/bin/env python3
"""
Camera simulator for testing the attendance system without real cameras.
This creates a virtual camera feed that generates frames with simulated faces.
"""

import cv2
import numpy as np
import threading
import time
import socket
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class CameraSimulator:
    def __init__(self, port=8080, width=640, height=480):
        self.port = port
        self.width = width
        self.height = height
        self.running = False
        self.current_frame = None
        self.face_present = False
        self.employee_name = "Test Employee"
        self.server = None
        self.server_thread = None

    def generate_frame(self):
        """Generate a test frame with optional simulated face"""
        # Create a blue background
        frame = np.full((self.height, self.width, 3), (100, 150, 200), dtype=np.uint8)

        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Simulator - {timestamp}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Add simulated face rectangle if employee is "present"
        if self.face_present:
            # Draw a rectangle representing a face
            face_x, face_y = self.width // 2 - 75, self.height // 2 - 75
            face_w, face_h = 150, 150

            cv2.rectangle(frame, (face_x, face_y), (face_x + face_w, face_y + face_h), (0, 255, 0), 3)
            cv2.putText(frame, self.employee_name, (face_x, face_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Add face features (eyes, nose, mouth) for realism
            # Eyes
            cv2.circle(frame, (face_x + 40, face_y + 40), 8, (0, 0, 0), -1)
            cv2.circle(frame, (face_x + 110, face_y + 40), 8, (0, 0, 0), -1)

            # Nose
            cv2.circle(frame, (face_x + 75, face_y + 70), 5, (0, 0, 0), -1)

            # Mouth
            cv2.ellipse(frame, (face_x + 75, face_y + 100), (20, 10), 0, 0, 180, (0, 0, 0), 2)

        else:
            cv2.putText(frame, "No employee detected", (self.width // 2 - 120, self.height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Add status indicators
        status_color = (0, 255, 0) if self.face_present else (0, 0, 255)
        status_text = "EMPLOYEE PRESENT" if self.face_present else "NO DETECTION"
        cv2.putText(frame, status_text, (10, self.height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        return frame

    def simulate_employee_presence(self):
        """Simulate employee coming and going"""
        while self.running:
            # Employee present for 30 seconds
            print("🟢 Simulating employee arrival...")
            self.face_present = True
            time.sleep(30)

            if not self.running:
                break

            # Employee absent for 10 seconds
            print("🔴 Simulating employee departure...")
            self.face_present = False
            time.sleep(10)

    def start(self):
        """Start the camera simulator"""
        print(f"🎥 Starting camera simulator on port {self.port}")

        self.running = True

        # Start employee presence simulation
        presence_thread = threading.Thread(target=self.simulate_employee_presence, daemon=True)
        presence_thread.start()

        # Start HTTP server for video stream
        self.start_http_server()

    def start_http_server(self):
        """Start HTTP server to serve video frames"""
        class VideoHandler(BaseHTTPRequestHandler):
            def __init__(self, simulator, *args, **kwargs):
                self.simulator = simulator
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/video':
                    self.serve_video_stream()
                elif self.path == '/frame':
                    self.serve_single_frame()
                elif self.path == '/':
                    self.serve_status_page()
                else:
                    self.send_error(404)

            def serve_video_stream(self):
                """Serve MJPEG video stream"""
                self.send_response(200)
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                self.end_headers()

                while self.simulator.running:
                    frame = self.simulator.generate_frame()
                    _, buffer = cv2.imencode('.jpg', frame)

                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(buffer))
                    self.end_headers()
                    self.wfile.write(buffer.tobytes())
                    self.wfile.write(b'\r\n')

                    time.sleep(1/30)  # 30 FPS

            def serve_single_frame(self):
                """Serve a single frame"""
                frame = self.simulator.generate_frame()
                _, buffer = cv2.imencode('.jpg', frame)

                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(buffer))
                self.end_headers()
                self.wfile.write(buffer.tobytes())

            def serve_status_page(self):
                """Serve status page"""
                html = f"""
                <html>
                <head><title>Camera Simulator</title></head>
                <body>
                    <h1>Camera Simulator Status</h1>
                    <p>Port: {self.simulator.port}</p>
                    <p>Running: {self.simulator.running}</p>
                    <p>Employee Present: {self.simulator.face_present}</p>
                    <p>Employee: {self.simulator.employee_name}</p>
                    <hr>
                    <p><a href="/video">Video Stream</a></p>
                    <p><a href="/frame">Single Frame</a></p>
                    <img src="/frame" alt="Current Frame" style="max-width: 640px;">
                </body>
                </html>
                """
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(html))
                self.end_headers()
                self.wfile.write(html.encode())

            def log_message(self, format, *args):
                pass  # Suppress HTTP server logs

        # Create handler with simulator reference
        def handler(*args, **kwargs):
            VideoHandler(self, *args, **kwargs)

        try:
            self.server = HTTPServer(('localhost', self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            print(f"✅ Camera simulator running at http://localhost:{self.port}")
            print(f"📹 Video stream: http://localhost:{self.port}/video")
            print(f"🖼️  Single frame: http://localhost:{self.port}/frame")
            print(f"📊 Status page: http://localhost:{self.port}/")

        except Exception as e:
            print(f"❌ Failed to start HTTP server: {e}")
            self.running = False

    def stop(self):
        """Stop the camera simulator"""
        print("🛑 Stopping camera simulator...")
        self.running = False

        if self.server:
            self.server.shutdown()
            self.server.server_close()

        if self.server_thread:
            self.server_thread.join(timeout=5)

        print("✅ Camera simulator stopped")

    def toggle_employee_presence(self):
        """Manually toggle employee presence for testing"""
        self.face_present = not self.face_present
        status = "present" if self.face_present else "absent"
        print(f"🔄 Employee status changed to: {status}")

def main():
    print("Camera Simulator for Attendance Tracking System")
    print("=" * 50)

    simulator = CameraSimulator(port=8080)

    try:
        simulator.start()

        print("\n📝 Commands:")
        print("  't' - Toggle employee presence")
        print("  'q' - Quit simulator")
        print("  'h' - Show help")

        while simulator.running:
            try:
                cmd = input("\nCommand: ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 't':
                    simulator.toggle_employee_presence()
                elif cmd == 'h':
                    print("\n📝 Available commands:")
                    print("  't' - Toggle employee presence")
                    print("  'q' - Quit simulator")
                    print("  'h' - Show this help")
                else:
                    print("❓ Unknown command. Type 'h' for help.")

            except KeyboardInterrupt:
                break

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        simulator.stop()

if __name__ == "__main__":
    main()