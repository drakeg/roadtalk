terraform {
  backend "s3" {
    bucket       = "roadtalk-state-configure-me"
    key          = "field-test/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
