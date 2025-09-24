data "tls_certificate" "gitlab" {
  url = var.url
}

data "aws_iam_policy_document" "this" {
  count = length(var.iam_roles)

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringLike"
      values   = var.iam_roles[count.index].gitlab_path
      variable = "${aws_iam_openid_connect_provider.this.url}:sub"
    }

    condition {
      test     = "StringEquals"
      values   = var.aud_value
      variable = "${aws_iam_openid_connect_provider.this.url}:aud"
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.this.arn]
      type        = "Federated"
    }
  }
}