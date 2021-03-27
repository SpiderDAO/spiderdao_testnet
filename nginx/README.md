# Nginx as a Reverse Proxy

Nginx is used as a reverse proxy for the API and for accessing the network from external locations (should not be required for local setups) 
In `nginx.conf`
- Replace {HOST_...} placeholders with your hostnames
- Create Nginx ssl certificates if needed and replace the paths [/path/to/ssl/] in Nginx.conf with your paths

Copy the generated `nginx.conf` and SSL certificate to the Docker mounted volumes

    #Ubuntu
    cp nginx.conf /var/lib/docker/volumes/nginxconf/_data/
    cp dhparam.pem /var/lib/docker/volumes/certs/_data/certs/
    cp nginx-selfsigned.crt /var/lib/docker/volumes/certs/_data/certs/
    cp nginx-selfsigned.key /var/lib/docker/volumes/certs/_data/private/

These steps (with described environment variables) are required for full replication of our testnet, otherwise the testnet will run without external access and the discord bot