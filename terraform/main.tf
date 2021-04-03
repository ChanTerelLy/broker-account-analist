provider "aws" {
  region = var.region
}

//resource "aws_s3_bucket" "terraform_state" {
//  bucket = "terraform-baa-system"
//  versioning {
//    enabled = true
//  }
//  server_side_encryption_configuration {
//    rule {
//      apply_server_side_encryption_by_default {
//        sse_algorithm = "AES256"
//      }
//    }
//  }
//}
//
//resource "aws_dynamodb_table" "terraform_locks" {
//  name         = "terraform-up-and-running-locks"
//  billing_mode = "PAY_PER_REQUEST"
//  hash_key     = "LockID"
//  attribute {
//    name = "LockID"
//    type = "S"
//  }
//}
//
//terraform {
//  backend "s3" {
//    bucket         = "terraform-up-and-running-state"
//    key            = "global/s3/terraform.tfstate"
//    region         = "us-east-1"
//    dynamodb_table = "terraform-up-and-running-locks"
//    encrypt        = true
//  }
//}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_lambda_layer_version" "packages" {
  filename   = var.layer_path
  layer_name = "packages"

  compatible_runtimes = [var.python_version]
  source_code_hash = filebase64sha256(var.layer_path)
}

resource "aws_lambda_function" "check_reports" {
  function_name = "checkReports"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = var.python_version
  timeout       = 300
  layers        = [aws_lambda_layer_version.packages.arn]
  environment {
    variables = var.lambda_env
  }
  filename      = var.function_path
  source_code_hash = filebase64sha256(var.function_path)
}

resource "aws_cloudwatch_event_rule" "every_half_day" {
    name = "every-half-day"
    description = "Fires every half day"
    schedule_expression = "rate(12 hours)"
}

resource "aws_cloudwatch_event_target" "check_reports_every_half_day" {
    rule = aws_cloudwatch_event_rule.every_half_day.name
    target_id = "check_reports"
    arn = aws_lambda_function.check_reports.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check_reports" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.check_reports.function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.every_half_day.arn
}