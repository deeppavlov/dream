#!/bin/bash

aws lambda update-function-configuration \
  --environment \
    '{"Variables":
      {
        "DP_AGENT_URL": "http://a1b4e1088651f439d9e82fce0c4533b4-501376769.us-east-1.elb.amazonaws.com",
        "TIMEOUT": "10.0",
        "DP_AGENT_PORT": "4242",
        "A_VERSION": "GOOD_NEW_BOT",
        "A_VERSION_RATIO": "1",
        "A_AGENT_URL": "http://a1b4e1088651f439d9e82fce0c4533b4-501376769.us-east-1.elb.amazonaws.com",
        "A_AGENT_PORT": "4242",
        "B_VERSION": "GOOD_OLD_BOT",
        "B_VERSION_RATIO": "1",
        "B_AGENT_URL": "http://ec2-54-145-105-62.compute-1.amazonaws.com",
        "B_AGENT_PORT": "4242"
      }
    }' \
    --function-name dp_agent_lambda_proxy_dev
