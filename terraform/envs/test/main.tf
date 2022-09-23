data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  region    = data.aws_region.current.name
  partition = data.aws_partition.current.partition
  acct_id   = data.aws_caller_identity.current.account_id
}

module "zap_image" {
  source = "git::https://github.com/rezen/zap-lambda.git//terraform/modules/zap_image"
}

resource "aws_s3_bucket" "data" {
  bucket = "owasp-zap-lambda--${local.acct_id}"
}

resource "aws_s3_bucket_public_access_block" "block" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "zap" {
  name = "OwaspZapLambda"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "iam_role_policy_attachment_lambda_basic_execution" {
  role       = aws_iam_role.zap.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "iam_role_policy_attachment_lambda_vpc_access_execution" {
  role       = aws_iam_role.zap.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}


resource "aws_iam_role_policy" "zap" {
  name = "OwaspZapLambdaPolicy"
  role = aws_iam_role.zap.id
  policy = jsonencode({
    "Version" : "2012-10-17"
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : [
          "*"
        ]
      },
      {
        "Sid" : "UseBucket"
        "Action" : [
          "s3:Put*",
          "s3:Get*",
          "s3:List*"
        ],
        "Resource" : [
          "arn:aws:s3:::${aws_s3_bucket.data.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.data.bucket}/*",
        ],
        "Effect" : "Allow"

      }
    ]
  })
}

resource "aws_lambda_function" "zap" {
  function_name = "zap-lambda"
  role          = aws_iam_role.zap.arn
  package_type  = "Image"
  timeout       = 900
  memory_size   = 4096
  image_uri     = module.zap_image.ecr_ref

  environment {
    variables = {
      PYTHONUNBUFFERED = "1"
      JAVA_OPTS        = "-Djava.util.prefs.systemRoot=/tmp -Djava.util.prefs.userRoot=/tmp"
      HOME             = "/tmp"
      S3_BUCKET        = aws_s3_bucket.data.bucket
    }
  }
}
