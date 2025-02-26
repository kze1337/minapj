FROM python:3.11-alpine
WORKDIR /app
RUN apk add --no-cache gcc git bash musl-dev linux-headers ffmpeg
COPY . .
RUN git clean -Xdf
RUN mv lavalink-docker.ini lavalink.ini || echo ""
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
