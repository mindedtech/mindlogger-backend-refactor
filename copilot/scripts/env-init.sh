#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. ${SCRIPT_DIR}/funcs.sh

#Create environment only once
if copilot env ls -a "$APP_NAME" | grep -q "$ENV_NAME"; then
    echo "Environment already exists"
#    exit 0
else
    if [ "$ENV_NAME" == 'feature' ]; then
        echo "You must create feature from bootstrap script locally"
        exit 1
    fi
    echo "Creating preview environment $ENV_NAME..."
fi

get_public_subnets "$VPC_ID"
export PUBLIC_SUBNETS="$retval"

get_private_subnets "$VPC_ID"
export PRIVATE_SUBNETS="$retval"

echo "PUBLIC_SUBNETS: $PUBLIC_SUBNETS"
echo "PRIVATE_SUBNETS: $PRIVATE_SUBNETS"


# Only run this during a GHA run.  copilot requires a profile during env creation.
if [[ ! -z "$CI" ]]; then
  echo "Writing out credentials"
  mkdir -p $HOME/.aws
  echo "[default]" > $HOME/.aws/credentials
  echo "aws_access_key_id=$AWS_ACCESS_KEY_ID" >> $HOME/.aws/credentials
  echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY" >> $HOME/.aws/credentials
  echo "aws_session_token=$AWS_SESSION_TOKEN" >> $HOME/.aws/credentials
  PROFILE="default"
else
  PROFILE=$AWS_PROFILE
fi

echo "Using profile $PROFILE"

# Create a new environment
copilot env init \
  --app "$APP_NAME" \
  --name "$ENV_NAME" \
  --import-vpc-id "$VPC_ID" \
  --import-public-subnets "$PUBLIC_SUBNETS" \
  --import-private-subnets "$PRIVATE_SUBNETS" \
  --profile "$PROFILE" --container-insights