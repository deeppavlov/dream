#!/bin/bash

aws lambda update-function-configuration \
  --environment \
    '{"Variables":
      {
        "DP_AGENT_URL": "http://ab61c7a0598e44dcbab6b2c216e108de-1052105272.us-east-1.elb.amazonaws.com",
        "TIMEOUT": "10.0",
        "DP_AGENT_PORT": "4242"
      }
    }' \
    --function-name dream_staging
