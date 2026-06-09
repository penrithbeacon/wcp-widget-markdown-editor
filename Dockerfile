FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
RUN mkdir -p /workspace
ENV PYTHONUNBUFFERED=1
ENV WIDGET_PORT=3748
ENV CONTAINER_NAME=wcp-widget-markdown-editor
ENV AGENT_PORT=3749
EXPOSE 3748
CMD ["python", "src/app.py"]
