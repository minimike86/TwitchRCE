resource "aws_iam_role" "RefreshTwitchAccessToken_role" {
  name = "RefreshTwitchAccessToken-role"

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

resource "aws_iam_role_policy" "RefreshTwitchAccessToken_policy" {
  name = "RefreshTwitchAccessToken_policy"
  role = aws_iam_role.RefreshTwitchAccessToken_role.id

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

resource "aws_lambda_function" "RefreshTwitchAccessToken" {
  function_name = "RefreshTwitchAccessToken"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  architectures = ["x86_64"]
  role          = aws_iam_role.RefreshTwitchAccessToken_role.arn
  memory_size   = 128
  timeout       = 3

  environment {
    variables = {
      DYNAMODB_USER_TABLE_NAME = "MSecBot_User"
    }
  }

  # Assuming the source code is directly provided, not from S3
  filename         = data.archive_file.RefreshTwitchAccessToken_lambda_zip.output_path
  source_code_hash = data.archive_file.RefreshTwitchAccessToken_lambda_zip.output_base64sha256

  description = "Use a refresh token to extend the lifetime of a given authorization after receiving a 401 Unauthorized response from Twitch."
}
