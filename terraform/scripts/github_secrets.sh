gh secret set AWS_ACCESS_KEY_ID -b $(echo $AWS_ACCESS_KEY_ID)
gh secret set AWS_SECRET_ACCESS_KEY -b $(echo $AWS_SECRET_ACCESS_KEY)
gh secret set AWS_REGION -b $(echo $AWS_DEFAULT_REGION)
gh secret set DOCKERHUB_USERNAME -b $(echo $DOCKERHUB_USERNAME)
gh secret set DOCKERHUB_TOKEN -b $(echo $DOCKERHUB_TOKEN)
gh secret set TASK_DEFENITION -b $(terraform output -raw aws_ecs_task_definition)
gh secret list