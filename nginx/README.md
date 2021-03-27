# Nginx as a Reverse Proxy

Nginx is used as a reverse proxy for the API and for accessing the network from external locations (should not be required for local setups) 
In `nginx.conf`
- Replace {HOST_...} placeholders with your hostnames
- Create Nginx ssl certificates if needed and replace the paths [/path/to/ssl/] in Nginx.conf with your paths

These steps (with described environment variables) are required for full replication of our testnet, otherwise the testnet will run without external access and the discord bot