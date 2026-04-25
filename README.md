# Clara AI - Intelligent IT Support Platform

Clara AI is a professional, high-performance IT support chat platform powered by the Gemini AI API. It features a responsive, premium UI, multi-step authentication, and secure chat history management.

## Features
- **Hacker-style UI**: Character-scramble 'decryption' animations and premium dark/light themes.
- **Multimodal AI**: Integrated Gemini AI for intelligent IT troubleshooting with file upload support.
- **Secure Auth**: Multi-step OTP authentication and password recovery systems.
- **Smart History**: Star and manage conversations with secure deletion and non-persistent error handling.
- **Modern Architecture**: Clean separation of logic (JS), styling (CSS), and backend (Python/Flask/SQLAlchemy).

## Getting Started

### Prerequisites
- Python 3.10+
- A Google Gemini API Key

### Installation
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy `.env.example` to `.env`.
   - Add your `GEMINI_TEXT_PROCESSING_API_KEY`.
5. Run the application:
   ```bash
   python app.py
   ```

## Tech Stack
- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: Vanilla HTML/JS, Tailwind CSS
- **AI**: Google Generative AI (Gemini API)
