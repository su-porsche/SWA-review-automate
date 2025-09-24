output "oidc_provider_arn" {
  description = "OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.this.arn
}

output "oidc_role_arns" {
  description = "ARNs of the IAM roles created"
  value       = aws_iam_role.this[*].arn
}

output "thumbprint" {
  description = "TLS endpoint certificate SHA1 Fingerprint"
  value       = data.tls_certificate.gitlab.certificates.0.sha1_fingerprint
}
