resource "aws_iam_openid_connect_provider" "this" {
  client_id_list  = var.aud_value
  thumbprint_list = ["${reverse(data.tls_certificate.gitlab.certificates).0.sha1_fingerprint}"]
  url             = var.url
}

resource "aws_iam_role" "this" {
  count = length(var.iam_roles)

  name                 = var.iam_roles[count.index].role_name
  description          = var.iam_roles[count.index].role_description
  max_session_duration = var.iam_roles[count.index].max_session_duration
  assume_role_policy   = data.aws_iam_policy_document.this[count.index].json
  tags                 = var.tags

  depends_on = [aws_iam_openid_connect_provider.this]
}

resource "aws_iam_role_policy_attachments_exclusive" "this" {
  count = length(var.iam_roles)

  role_name   = var.iam_roles[count.index].role_name
  policy_arns = var.iam_roles[count.index].policy_arns_to_attach

  depends_on = [
    aws_iam_role.this,
    aws_iam_openid_connect_provider.this
  ]
}