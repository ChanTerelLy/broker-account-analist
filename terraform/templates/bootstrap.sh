#!/bin/bash

echo ECS_CLUSTER='${ecs_cluster_name}-cluster' > /etc/ecs/ecs.config
cd /home/ec2-user
# install reids=cli
sudo yum update -y
sudo yum install -y gcc wget
sudo wget http://download.redis.io/redis-stable.tar.gz && tar xvzf redis-stable.tar.gz && cd redis-stable && make

# install postgresql
sudo amazon-linux-extras enable postgresql10
sudo yum clean metadata
sudo yum install -y postgresql
