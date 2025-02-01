provider "archive" {}

data "archive_file" "RefreshTwitchAccessToken_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../aws/lambdas/refresh_twitch_access_token.py"
  output_path = "${path.module}/../aws/deploy/refresh_twitch_access_token.zip"
}

data "archive_file" "StoreOAuth2AuthorizeCode_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../aws/lambdas/store_oauth_authorize_code.py"
  output_path = "${path.module}/../aws/deploy/store_oauth_authorize_code.zip"
}
