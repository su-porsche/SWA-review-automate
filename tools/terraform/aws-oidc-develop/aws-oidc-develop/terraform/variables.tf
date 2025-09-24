variable "iam_roles" {
  description = "An array that contains the AWS IAM roles to be created. One element for each AWS IAM role that needs to be created and associated with the OIDC provider. The Gitlab path must be the full path to your repository. It's not valid to work with wildcard in the Gitlab Path. It's valid to use a wildcard for the branch and it is not neccessary to point to a specific branch name."
  type = list(object({
    role_name             = string
    gitlab_path           = list(string)
    policy_arns_to_attach = list(string)
    role_description      = optional(string, "Role to connect Gitlab repository with AWS")
    max_session_duration  = optional(number, 3600)
  }))
}

variable "url" {
  description = "GitLab OpenID TLS certificate URL. The address of your GitLab instance, such as https://cicd.skyway.porsche.com"
  type        = string
  default     = "https://cicd.skyway.porsche.com"
}

variable "aud_value" {
  description = "(Required) A list of client IDs (also known as audiences)."
  type        = list(string)
  default     = ["https://cicd.skyway.porsche.com"]
}

variable "tags" {
  description = "A mapping of tags to assign to all resources in this module"
  type        = map(string)
  default     = {}
}