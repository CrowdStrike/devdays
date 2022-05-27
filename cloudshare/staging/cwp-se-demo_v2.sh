#!/bin/bash
DG="\033[1;30m"
RD="\033[0;31m"
NC="\033[0;0m"
LB="\033[1;34m"
env_up(){
    echo -e "$LB\n"
    echo -e "Initializing environment templates$NC"
    sudo yum -y install unzip
    BUCKET_NAME="$(cat /tmp/environment.txt | cut -c -8 | tr _ - | tr '[:upper:]' '[:lower:]')-templatebucket"
    REGION_CODE="us-west-2"
    cd /home/ec2-user
    mkdir s3bucket
    unzip -d s3bucket s3bucket.zip
    aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION_CODE --create-bucket-configuration LocationConstraint=$REGION_CODE
    cd s3bucket
    aws s3 cp . s3://$BUCKET_NAME --recursive
    echo -e "$LB\n"
    echo -e "Standing up environment$NC"
    aws cloudformation create-stack --stack-name cwp-demo-stack --template-url https://$BUCKET_NAME.s3-$REGION_CODE.amazonaws.com/cwp-lab-entrypoint.yaml --parameters  ParameterKey=FalconClientID,ParameterValue=$CLIENT_ID ParameterKey=FalconClientSecret,ParameterValue=$CLIENT_SECRET ParameterKey=S3Bucket,ParameterValue=$BUCKET_NAME  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --region $REGION_CODE
    echo -e "The Cloudformation stack will take 20-30 minutes to complete$NC"
    echo -e "\n\nCheck the status at any time with the command \n\naws cloudformation describe-stacks --stack-name cwp-demo-stack --region $REGION_CODE$NC\n\n"
    sleep 5
    id=$(aws ec2 describe-instances --region us-west-2 --filters "Name=tag:Name,Values=Startup" --query "Reservations[0].Instances[].InstanceId" --output text)
    aws ec2 terminate-instances --region us-west-2 --instance-ids $id
}
env_down(){
    echo -e "$RD\n"
    echo -e "Tearing down environment$NC"
    aws cloudformation delete-stack --stack-name horizon-demo-stack --region $REGION_CODE
    env_destroyed
}
help(){
    echo "./demo {up|down|help}"
}
all_done(){
    echo -e "$LB"
    echo '  __                        _'
    echo ' /\_\/                   o | |             |'
    echo '|    | _  _  _    _  _     | |          ,  |'
    echo '|    |/ |/ |/ |  / |/ |  | |/ \_|   |  / \_|'
    echo ' \__/   |  |  |_/  |  |_/|_/\_/  \_/|_/ \/ o'
    echo -e "$NC"
}
api_keys(){
    echo -e "$NC"
    echo ''
    echo ' Create an OAuth2 key pair with permissions for the Streaming API and Hosts API' 
    echo '     | Service                           | Read | Write |'
    echo '     | -------                           |----- | ----- |'
    echo '     | Sensor Download                   | x    |       |'
    echo '     | Falcon Images Download            | x    |       |'
    echo '     | Falcon Falcon Container Image     | x    |   x   |'
    echo '     | -------                           |----- | ----- |'
    echo ''
    echo ' CS_CLOUD Should be one of the following us1, us2 or eu'
    echo -e "$NC"
}
env_destroyed(){
    echo -e "$RD"
    echo ' ___                              __,'
    echo '(|  \  _  , _|_  ,_        o     /  |           __|_ |'
    echo ' |   ||/ / \_|  /  | |  |  |    |   |  /|/|/|  |/ |  |'
    echo '(\__/ |_/ \/ |_/   |/ \/|_/|/    \_/\_/ | | |_/|_/|_/o'
    echo -e "$NC"
}
if [ -z $1 ]
then
    echo "You must specify an action."
    help
    exit 1
fi
if [[ "$1" == "up" || "$1" == "reload" ]]

then
    api_keys
    for arg in "$@"
    do
        if [[ "$arg" == *--client_id=* ]]
        then
            CLIENT_ID=${arg/--client_id=/}
        fi
        if [[ "$arg" == *--client_secret=* ]]
        then
            CLIENT_SECRET=${arg/--client_secret=/}
        fi
        if [[ "$arg" == *--cs_cloud=* ]]
        then
            CS_CLOUD=${arg/--cs_cloud=/}
        fi
        if [[ "$arg" == *--unique_id=* ]]
        then
            UNIQUE_ID=${arg/--unique_id=/}
        fi
        if [[ "$arg" == *--owner=* ]]
        then
            OWNER_ID="${arg/--owner=/}"
        fi
        if [[ "$arg" == *--trusted=* ]]
        then
            TRUSTED_IP="${arg/--trusted=/}"
        fi
        if [[ "$arg" == *--baseurl=* ]]
        then
            BASE_URL="${arg/--baseurl=/}"
        fi
    done
    if [ -z "$CLIENT_ID" ]
    then
        read -p "Falcon API Client ID: " CLIENT_ID
    fi
    if [ -z "$CLIENT_SECRET" ]
    then
        read -p "Falcon API Client SECRET: " CLIENT_SECRET
    fi
    if [ -z "$CS_CLOUD" ]
    then
        read -p "CrowdStrike Cloud: us1, us2 or eu  " CS_CLOUD
    fi
    if [ -z "$UNIQUE_ID" ]
    then
        read -p "Unique Identifier: " UNIQUE_ID
    fi
    # if [ -z "$OWNER_ID" ]
    # then
    #     read -p "Presenter name: " OWNER_ID
    # fi
    if [ -z "$TRUSTED_IP" ]
    then
        read -p "Your external IP Address (for SSH connection, CIDR format): " TRUSTED_IP
    fi
    if [ -z "$BASE_URL" ]
    then
        BASE=""
    else
        BASE=" -var falcon_base_url='$BASE_URL'"
    fi
fi
if [[ "$1" == "up" ]]
then
    env_up
elif [[ "$1" == "down" ]]
then
    env_down
elif [[ "$1" == "help" ]]
then
    help
else
    echo "Invalid action specified"
fi
