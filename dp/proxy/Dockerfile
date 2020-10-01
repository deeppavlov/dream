FROM nginx:latest

COPY default.conf.template /etc/nginx/templates/

#RUN echo "server {listen PORT;location / {proxy_pass http://HOST:PORT/;}}" > /etc/nginx/conf.d/nginx.conf
#ENTRYPOINT sed -i 's/PORT/'$PORT'/g' /etc/nginx/conf.d/nginx.conf && \
#           sed -i 's/HOST/'$HOST'/g' /etc/nginx/conf.d/nginx.conf && \
#           nginx -g 'daemon off;'
