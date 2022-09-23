# zap-lambda
What if you could run ZAP in a lambda? That would be cool? This PoC spiders a site and spits out the URLs and alerts. The original PoC is in `v1` if you wanna take a look. It will be killed in the near future.


## Now
Now that AWS Lambda supports custom images, there is no need to have a hacky build script. There is now a custom Dockerfile found here `terraform/modules/zap_image/code/Dockerfile` that you can deploy using terraform. 

## Requirements
These requirements are to run use terraform to deploy an image to AWS.

- docker
- terraform
- AWS
  - `aws` cli


### Terraform
Deploying the ZAP lambda base image to ECR, simply define a module with the source of this repo following the example below. For a fully fleshed out example checkout `terraform/envs/test`
```
module "zap_image" {
  source = "git::https://github.com/rezen/zap-lambda.git//terraform/modules/zap_image"
  image_name = "zap-lambda"
}
```

### Lambda
This is a sample of the event data you can invoke the lambda with.

**event**  
```json
{
	"target": "https://ahermosilla.com",
	"timeout": 1,
	"ignore_alert_ids": [
		50003, 60000, 60001
	]
}
```