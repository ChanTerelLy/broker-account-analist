[
  {
    "name": "django-app",
    "image": "${docker_image_url_django}",
    "essential": true,
    "cpu": 10,
    "memoryReservation": 300,
    "links": [],
    "portMappings": [
      {
        "containerPort": 80,
        "hostPort": 0,
        "protocol": "tcp"
      }
    ],
    "environment": [
      { "name" : "AWS_XRAY_DAEMON_ADDRESS", "value" : "xray-daemon:2000" },
      { "name" : "AWS_REGION", "value" : "${region}" }
    ],
    "command": ["/bin/sh", "-c", "python manage.py migrate --settings=baa.settings.aws && gunicorn -w 3 -b :80 baa.wsgi_aws:application --access-logfile -"],
    "mountPoints": [
      {
        "containerPath": "/usr/src/app/staticfiles",
        "sourceVolume": "static_volume"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/django-app",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "django-app-log-stream"
      }
    },
    "links": [
        "xray-daemon"
      ]
  },
  {
      "name": "xray-daemon",
      "image": "amazon/aws-xray-daemon",
      "cpu": 32,
      "memoryReservation": 256,
      "portMappings" : [
          {
              "hostPort": 0,
              "containerPort": 2000,
              "protocol": "udp"
          }
       ]
    }
]
