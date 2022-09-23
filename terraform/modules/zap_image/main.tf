data "aws_regions" "all" {}
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

variable "image_name" {
  default = "zap-lambda"
}

locals {
  image_name   = var.image_name
  account_id   = data.aws_caller_identity.current.account_id
  partition    = data.aws_partition.current.partition
  ecr_tld      = local.partition != "aws-cn" ? "com" : "com.cn"
  region       = data.aws_region.current.name
  image_digest = data.external.image_digest.result.data # data.aws_ecr_image.lambda_image.image_digest
  image_ref    = "${aws_ecr_repository.lambda_image.repository_url}@${local.image_digest}"
  ecr_host     = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.${local.ecr_tld}"
}


resource "aws_ecr_repository" "lambda_image" {
  name = local.image_name

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository_policy" "foopolicy" {
  repository = aws_ecr_repository.lambda_image.name
  policy = jsonencode({
    "Version" : "2008-10-17",
    "Statement" : [
      {
        "Sid" : "LambdaECRImageRetrievalPolicy",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Action" : [
          "ecr:ListImages",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
        ],
        "Condition" : {
          "StringLike" : {
            "aws:sourceArn" : "arn:aws:lambda:*:${local.account_id}:function:*"
          }
        }
      }
    ]
  })
}



resource "aws_ecr_replication_configuration" "example" {
  replication_configuration {
    dynamic "rule" {
      for_each = [for r in data.aws_regions.all.names : r if length(regexall("^us\\-", r)) > 0 && r != data.aws_region.current.name]
      content {

        destination {
          region      = rule.value
          registry_id = data.aws_caller_identity.current.account_id
        }

        repository_filter {
          filter      = aws_ecr_repository.lambda_image.name
          filter_type = "PREFIX_MATCH"
        }
      }
    }
  }
}

# Get hash of lambda
data "external" "dir_hash" {
  program = ["sh", "-c", "cd ${path.module} && ./sum.sh"]
}


resource "null_resource" "ecr_push" {
  triggers = {
    # If lambda hash changes ... then rebuild
    always_run = "${lookup(data.external.dir_hash.result, "hash")}"
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/code/ && ./push.sh"

    environment = {
      ECR_HOST   = local.ecr_host
      IMAGE_PATH = "${local.image_name}:latest"
      ZAP_DOCKER_IMAGE = local.image_name
    }
  }
}





# This seems slow ...
# https://github.com/hashicorp/terraform-provider-aws/issues/12798
# data "aws_ecr_image" "lambda_image" {
#  repository_name = aws_ecr_repository.lambda_image.name
#  image_tag       = "latest"
#  depends_on      = [null_resource.ecr_push]
#}

data "external" "image_digest" {
  program = [
    "aws", "ecr", "describe-images",
    "--repository-name", aws_ecr_repository.lambda_image.name,
    "--image-ids", "imageTag=latest",
    "--query", "{\"data\": imageDetails[0].imageDigest}",
  ]
  depends_on = [null_resource.ecr_push]

}


output "image_name" {
  value = local.image_name
}
output "image_digest" {
  value = local.image_digest
}

output "ecr_ref" {
  value = local.image_ref
}
