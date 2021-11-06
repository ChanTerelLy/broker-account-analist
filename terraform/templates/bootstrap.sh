#!/bin/bash

# set swap
sudo dd if=/dev/zero of=/swapfile bs=128M count=64
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# shellcheck disable=SC2024
sudo echo /swapfile swap swap defaults 0 0 >> /etc/fstab

# install cloudwatch agent
sudo yum install -y amazon-cloudwatch-agent
sudo amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:AmazonCloudWatchEc2Config -s

# ecs configuration
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

# other
sudo yum install -y nano
