provider "aws" {
  region = "us-west-1"
  version = "~> 2.1"
}

provider "aws" {
  alias  = "east"
  region = "us-east-1"
  version = "~> 2.1"
}

variable "domain" {
  type = "string"
  default = "pwshare.cuda-security.com"
}

variable "bucket" {
  type = "string"
  default = "lambda-pw"
}

variable "bucket_key" {
  type = "string"
  default = "lambda-pw-edge.zip"
}
variable "zone_id" {
  type = "string"
  default = "Z2DTV7WOQDONPV"
}

resource "aws_dynamodb_table" "secrets_table" {
  name           = "secrets"
  read_capacity  = 10
  write_capacity = 4
  hash_key       = "uuid"

  attribute {
    name = "uuid"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled = true
  }

  tags = {
    Name        = "shared-secrets"
    Environment = "production"
  }
}

data "aws_iam_policy_document" "lambda_dynamo_kms" {
  statement {
    actions = ["dynamodb:*"]
    resources = [
      "${aws_dynamodb_table.secrets_table.arn}",
      "${aws_dynamodb_table.secrets_table.arn}:*"
    ]
    effect = "Allow"
  }
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
    effect = "Allow"
  }
  
  statement {
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateRandom"
    ]
    effect = "Allow"
    resources = [
      "*",
    ]
  }
}

resource "aws_iam_role" "lambda_pw" {
  name = "LambdaSecrets"

  assume_role_policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [{
		"Action": "sts:AssumeRole",
		"Principal": {
			"Service": "lambda.amazonaws.com"
		},
		"Effect": "Allow",
		"Sid": ""
	}]
}
EOF
}

resource "aws_iam_policy" "dynamodb_kms" {
  name        = "LambdaSecrets"
  description = "..."

  policy = "${data.aws_iam_policy_document.lambda_dynamo_kms.json}"
}

resource "aws_iam_role_policy_attachment" "attach_policy_1" {
  role       = "${aws_iam_role.lambda_pw.name}"
  policy_arn = "${aws_iam_policy.dynamodb_kms.arn}"
}

resource "aws_lambda_function" "lambda_pw" {
  function_name = "LambdaSecrets"
  handler = "app.handler"
  runtime = "python2.7"
  memory_size = "500"
  s3_bucket = "${var.bucket}"
  s3_key    = "${var.bucket_key}"

  environment = {
    variables = {
        REQUIRE_PASSWORD = 0
        GENERATES_SECRET =1
        MAX_VIEWS = 10
        MAX_HOURS = 12
    }

  }
  role = "${aws_iam_role.lambda_pw.arn}"
}

resource "aws_api_gateway_rest_api" "lambda_pw" {
  name        = "LambdaSecretsAPI"
  description = "...."
  /*
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": [ "{{sourceIpOrCIDRBlock}}", "{{sourceIpOrCIDRBlock}}" ]
        }
      }
    }
  ]
}
EOF*/
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = "${aws_api_gateway_rest_api.lambda_pw.id}"
  parent_id   = "${aws_api_gateway_rest_api.lambda_pw.root_resource_id}"
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = "${aws_api_gateway_rest_api.lambda_pw.id}"
  resource_id   = "${aws_api_gateway_resource.proxy.id}"
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = "${aws_api_gateway_rest_api.lambda_pw.id}"
  resource_id = "${aws_api_gateway_method.proxy.resource_id}"
  http_method = "${aws_api_gateway_method.proxy.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${aws_lambda_function.lambda_pw.invoke_arn}"
}

resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = "${aws_api_gateway_rest_api.lambda_pw.id}"
  resource_id   = "${aws_api_gateway_rest_api.lambda_pw.root_resource_id}"
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = "${aws_api_gateway_rest_api.lambda_pw.id}"
  resource_id = "${aws_api_gateway_method.proxy_root.resource_id}"
  http_method = "${aws_api_gateway_method.proxy_root.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${aws_lambda_function.lambda_pw.invoke_arn}"
}

resource "aws_api_gateway_deployment" "lambda_pw" {
  depends_on = [
    "aws_api_gateway_integration.lambda",
    "aws_api_gateway_integration.lambda_root",
  ]

  rest_api_id = "${aws_api_gateway_rest_api.lambda_pw.id}"
  stage_name  = "live"
}

resource "aws_lambda_permission" "apigw" {

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambda_pw.arn}"
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_deployment.lambda_pw.execution_arn}/*/*"
}


resource "aws_api_gateway_base_path_mapping" "live" {
  api_id      = "${aws_api_gateway_rest_api.lambda_pw.id}"
  stage_name  = "${aws_api_gateway_deployment.lambda_pw.stage_name}"
  domain_name = "${aws_api_gateway_domain_name.lambda_pw.domain_name}"
}

resource "aws_acm_certificate" "cert" {
  domain_name       = "${var.domain}"
  validation_method = "DNS"
  # provider = "aws.east" # If using edge

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  name    = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_name}"
  type    = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_type}"
  zone_id = "${var.zone_id}"
  records = ["${aws_acm_certificate.cert.domain_validation_options.0.resource_record_value}"]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "lambda_pw" {
  # provider = "aws.east" # If using edge
  certificate_arn         = "${aws_acm_certificate.cert.arn}"
  validation_record_fqdns = ["${aws_route53_record.cert_validation.fqdn}"]
}

resource "aws_api_gateway_domain_name" "lambda_pw" {
  domain_name     = "${var.domain}"
  regional_certificate_arn = "${aws_acm_certificate_validation.lambda_pw.certificate_arn}"
  
  # If using edge computing
  # certificate_arn = "${aws_acm_certificate_validation.lambda_pw.certificate_arn}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_route53_record" "www" {
  zone_id = "${var.zone_id}"
  name    = "${aws_api_gateway_domain_name.lambda_pw.domain_name}"
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = "${aws_api_gateway_domain_name.lambda_pw.regional_domain_name}"
    zone_id                = "${aws_api_gateway_domain_name.lambda_pw.regional_zone_id}"

    # If APIGW custom domain is EDGE  
    # name                   = "${aws_api_gateway_domain_name.lambda_pw.cloudfront_domain_name}"
    # zone_id                = "${aws_api_gateway_domain_name.lambda_pw.cloudfront_zone_id}"
  }
}

output "base_url" {
  value = "${aws_api_gateway_deployment.lambda_pw.invoke_url}"
}
