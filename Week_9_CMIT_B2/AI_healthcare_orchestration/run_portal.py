import sys
import io
import uvicorn

# Ensure UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    print("=" * 65)
    print("Starting City Care Clinics Web Application")
    print("Patient Portal & Chat:  http://localhost:8000")
    print("Doctor Portal Login:   http://localhost:8000/doctor-login")
    print("=" * 65)
    uvicorn.run("src.server.app:app", host="127.0.0.1", port=8000, reload=False)
