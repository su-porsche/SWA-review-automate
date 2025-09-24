#
# Array element 1 points to a specific Gitlab repository to a specific branch. Element 2 uses a wildcard for the branches. Both is valid.
# It's not valid to restrict the IAM role only to a Gitlab group. It must be limited to a specific repository.
# You need to create the AWS IAM policies first on your own and in line with the principle of least privilege.
#
module "aws_oidc_complete" {
  source = "../terraform/"
  iam_roles = [
    {
      role_name             = "custom-t-gitlab-aws-oidc"
      gitlab_path           = ["project_path:porsche/cloud/shared-tooling/oidc-gitlab/aws-oidc:ref_type:branch:ref:main"]
      policy_arns_to_attach = ["arn:aws:iam::aws:policy/custom-t-gitlab-aws-oidc-policy"]
    },
    {
      role_name             = "custom-t-gitlab-azure-oidc"
      gitlab_path           = ["project_path:porsche/cloud/shared-tooling/oidc-gitlab/azure-oidc:ref_type:branch:ref:*"]
      policy_arns_to_attach = ["arn:aws:iam::aws:policy/custom-t-gitlab-azure-oidc-policy"]
    }
  ]
}

output "oidc_provider_arn" {
  description = "OIDC provider ARN"
  value       = module.aws_oidc_complete.oidc_provider_arn
}

output "oidc_role_arns" {
  description = "ARNs of the IAM roles created"
  value       = module.aws_oidc_complete.oidc_role_arns
}
