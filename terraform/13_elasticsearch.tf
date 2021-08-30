resource "aws_elasticsearch_domain" "baa_elasticsearch" {
      domain_name           = "baa"
      elasticsearch_version = "7.10"
      access_policies       = jsonencode(
            {
              Statement = [
                  {
                      Action    = "es:*"
                      Effect    = "Allow"
                      Principal = {
                          AWS = "*"
                        }
                      Resource  = "arn:aws:es:us-west-1:115253010062:domain/baa/*"
                    },
                ]
              Version   = "2012-10-17"
            }
      )

      advanced_options      = {
          "rest.action.multi.allow_explicit_index" = "true"
      }
      tags                  = {}
      tags_all              = {}

      advanced_security_options {
          enabled                        = false
          internal_user_database_enabled = false
      }

      cluster_config {
          warm_enabled             = false
          zone_awareness_enabled   = false
          instance_type            = "t2.small.elasticsearch"
        }

      domain_endpoint_options {
          custom_endpoint_enabled         = false
          enforce_https                   = true
          tls_security_policy             = "Policy-Min-TLS-1-0-2019-07"
      }

      ebs_options {
          ebs_enabled = true
          iops        = 0
          volume_size = 10
          volume_type = "gp2"
      }

      encrypt_at_rest {
          enabled    = false
      }

      node_to_node_encryption {
          enabled = false
      }

      snapshot_options {
          automated_snapshot_start_hour = 0
      }

      timeouts {}

      vpc_options {
          availability_zones = [
            var.availability_zones[1],
          ]
          security_group_ids = [aws_security_group.elastic_search.id,]
          subnet_ids = [aws_subnet.public-subnet-2.id,]
      }
    }
