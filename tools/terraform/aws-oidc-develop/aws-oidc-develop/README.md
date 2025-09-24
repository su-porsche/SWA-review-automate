# Gitlab AWS OIDC Integration

This repository contains a Terraform module that can control Gitlab as a OIDC provider in Terraform and create AWS IAM roles with a provided AWS IAM policy.

A more detailed documentation on how to use the Gitlab AWS OIDC integration, can be found here: https://skyway.porsche.com/confluence/x/74ECO

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.9.8 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.73.0 |
| <a name="requirement_tls"></a> [tls](#requirement\_tls) | >= 4.0.6 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 5.73.0 |
| <a name="provider_tls"></a> [tls](#provider\_tls) | >= 4.0.6 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_openid_connect_provider.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider) | resource |
| [aws_iam_role.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachments_exclusive.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachments_exclusive) | resource |
| [aws_iam_policy_document.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [tls_certificate.gitlab](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/data-sources/certificate) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aud_value"></a> [aud\_value](#input\_aud\_value) | (Required) A list of client IDs (also known as audiences). | `list(string)` | <pre>[<br/>  "https://cicd.skyway.porsche.com"<br/>]</pre> | no |
| <a name="input_iam_roles"></a> [iam\_roles](#input\_iam\_roles) | An array that contains the AWS IAM roles to be created. One element for each AWS IAM role that needs to be created and associated with the OIDC provider. The Gitlab path must be the full path to your repository. It's not valid to work with wildcard in the Gitlab Path. It's valid to use a wildcard for the branch and it is not neccessary to point to a specific branch name. | <pre>list(object({<br/>    role_name             = string<br/>    gitlab_path           = list(string)<br/>    policy_arns_to_attach = list(string)<br/>    role_description      = optional(string, "Role to connect Gitlab repository with AWS")<br/>    max_session_duration  = optional(number, 3600)<br/>  }))</pre> | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | A mapping of tags to assign to all resources in this module | `map(string)` | `{}` | no |
| <a name="input_url"></a> [url](#input\_url) | GitLab OpenID TLS certificate URL. The address of your GitLab instance, such as https://cicd.skyway.porsche.com | `string` | `"https://cicd.skyway.porsche.com"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_oidc_provider_arn"></a> [oidc\_provider\_arn](#output\_oidc\_provider\_arn) | OIDC provider ARN |
| <a name="output_oidc_role_arns"></a> [oidc\_role\_arns](#output\_oidc\_role\_arns) | ARNs of the IAM roles created |
| <a name="output_thumbprint"></a> [thumbprint](#output\_thumbprint) | TLS endpoint certificate SHA1 Fingerprint |
<!-- END_TF_DOCS -->