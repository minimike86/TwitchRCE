resource "aws_iam_role" "StoreOAuth2AuthorizeCode_role" {
  name = "StoreOAuth2AuthorizeCode-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "StoreOAuth2AuthorizeCode_policy" {
  name = "StoreOAuth2AuthorizeCode_policy"
  role = aws_iam_role.StoreOAuth2AuthorizeCode_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ],
        Effect   = "Allow"
        Resource = "arn:aws:dynamodb:*:*:table/MSecBot_User"
      }
    ]
  })
}

resource "aws_lambda_function" "StoreOAuth2AuthorizeCode" {
  function_name = "StoreOAuth2AuthorizeCode"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  architectures = ["x86_64"]
  role          = aws_iam_role.StoreOAuth2AuthorizeCode_role.arn
  memory_size   = 128
  timeout       = 10

  environment {
    variables = {
      DYNAMODB_USER_TABLE_NAME = "MSecBot_User"
    }
  }

  layers = [
    "arn:aws:lambda:eu-west-2:133256977650:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11"
  ]

  # Assuming the source code is directly provided, not from S3
  filename         = data.archive_file.StoreOAuth2AuthorizeCode_lambda_zip.output_path
  source_code_hash = data.archive_file.StoreOAuth2AuthorizeCode_lambda_zip.output_base64sha256

  description = "Twitch OAuth2 redirect URI to capture authorization code"

  tags = {
    "lambda-console:blueprint" = "microservice-http-endpoint-python"
  }
}
