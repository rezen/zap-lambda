**local-dev**  
```sh
docker build -t zap-lambda . 
docker run -it --entrypoint bash -v $(pwd)/app.py:/function/app.py   zap-lambda
```