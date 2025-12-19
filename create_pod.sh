podman run -d \
  -p 8000:8000 \
  --name twflagdesign \
  --env-file .env \
  -v $(pwd)/src/instance:/app/src/instance \
  -v $(pwd)/log:/app/log \
  localhost/twflagdesign