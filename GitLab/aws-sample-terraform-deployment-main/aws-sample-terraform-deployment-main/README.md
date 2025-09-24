# Sample Repository for Terraform Deployments on AWS

You read about Architecture as Code and wonder how you can quickly get going with deploying one?

You already have access to a PoC cloud account on AWS and set up a Gitlab project to host your latest PoC endeavours.
Great, you have all that's needed to utilize this repository as a baseline for your efforts.

## Disclaimer
### Usage recommendation
This repository covers the minimal requirements for deploying terraform code to a PoC AWS account.
If you have ideas for how to improve the experience, please [let us know](https://teams.microsoft.com/l/channel/19%3Ac33a9a28e11b4d58bb2b428a7f29f117%40thread.skype/General?groupId=c5d942ff-a003-40c4-9184-b979543b1d6c&tenantId=).
However, please keep in mind, that this repository is not meant to provide means to deploy production applications to multiple environments and also does not include measures typically needed in production deployments.

Our goal is to provide an easy to use repository & pipeline and make your life easier when you need to rapidly create a PoC. 

## How-To
### Minimal Deployment
Five steps:
1. Either create a new repository in your gitlab project and copy over all files of this repository, or fork this repository.
2. Setup the IAM prerequisites for [Gitlab-based IaC deployments](https://skyway.porsche.com/confluence/x/So8HVQ).
3. Don't forget to create the CICD variable `AWS_OIDC_IAM_ROLE_ARN` as described in the [confluence page](https://skyway.porsche.com/confluence/display/FIT3A/Prerequisites+for+Gitlab-based+IaC+Deployments#PrerequisitesforGitlabbasedIaCDeployments-AdddeploymentroletoGitlab)!
4. Adjust the `TF_STATE_NAME_PREFIX` variable in `.gitlab-ci.yml` to your project's name.
5. Create a folder named `terraform` and place your terraform code inside.
6. Commit your changes. If you commit to main, the pipeline will deploy your code automatically.

### Multi-stage Deployment
To add more stages to your pipeline, you have to follow these steps:
1. In `min_terraform_pipeline.yml` add your stage to the `stages:` section. e.g. "deploy_qa":
```
stages:
...
  - deploy_dev
  - deploy_qa
...
```
2. Since your stage will be deployed to another AWS account than the dev (development) stage (stages seldom share the same AWS account), for that other AWS account, setup the IAM prerequisites for [Gitlab-based IaC deployments](https://skyway.porsche.com/confluence/x/So8HVQ). But note, that you must store the OIDC role arn in another CICD variable. The linked tutorial proposes `AWS_OIDC_IAM_ROLE_ARN`. But e.g. when your new stage is called `qa` (quality assurance), then you should store the OIDC role arn in the CICD variable called `AWS_OIDC_IAM_ROLE_ARN_QA` accordingly.

3. In `.gitlab-ci.yml`, you can now add the steps for terraform plan/apply for your new stage:
```
terraform:plan:qa:
  extends: .terraform:plan
  stage: deploy_qa
  rules:
    - if: '$PIPELINE_TYPE == "deploy"'
  variables:
    AWS_OIDC_IAM_ROLE_ARN: $AWS_OIDC_IAM_ROLE_ARN_QA
    TF_STATE_NAME: "${TF_STATE_NAME_PREFIX}-qa"
    ENV_ID: "qa"

terraform:apply:qa:
  extends: .terraform:apply
  rules:
    - if: '$PIPELINE_TYPE == "deploy"'
  stage: deploy_qa
  needs:
    - terraform:plan:qa
  variables:
    AWS_OIDC_IAM_ROLE_ARN: $AWS_OIDC_IAM_ROLE_ARN_QA
    TF_STATE_NAME: "${TF_STATE_NAME_PREFIX}-qa"
    ENV_ID: "qa"
```
4. Commit your changes. If you commit to main, the pipeline will deploy your code automatically.