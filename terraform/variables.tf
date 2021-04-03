variable "region" {
  default = "us-east-1"
}
variable "layer_path" {
  default = "./lambda_functions/checkReports/packages.zip"
}
variable "function_path" {
  default = "./lambda_functions/checkReports/check-report.zip"
}
variable "python_version" {
  default = "python3.8"
}

variable "lambda_env" {
  type = map
}