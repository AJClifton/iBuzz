FROM ubuntu:latest

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

RUN apt install nginx -y
RUN apt install ufw -y
RUN ufw allow 'Nginx HTTP'
RUN mv default /etc/nginx/sites-enabled/default

RUN apt install python3.12-venv -y

RUN python3 -m venv venv

RUN . ./venv/bin/activate && pip install -r requirements.txt

EXPOSE 80/tcp
EXPOSE 587

# Set the default command to execute when the container starts
CMD ["./start.sh"]
