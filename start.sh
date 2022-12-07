DG="\033[1;30m"
RD="\033[0;31m"
NC="\033[0;0m"
LB="\033[1;34m"
env_up(){
    
   UNIQUE=$(cat /tmp/environment.txt | cut -c -8 | tr _ - | tr '[:upper:]' '[:lower:]')
   S3Bucket="$UNIQUE-devdays-templates"
   #S3Bucket="ee-assets-prod-us-east-1"
   #S3Prefix="modules/5c8ee49a12044f19aab31bf3f649f912/v1"
   S3Prefix="templates"  # a valid prefix must have NO leading or trailing slash
   AWS_REGION="us-east-1"	       
   #AWS_REGION=$(curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
   KeyPairName="cs-key"


   echo -e "$LB\n"
   echo -e "Welcome to DevDays$NC"
   read -p "Enter your Falcon API Key Client ID: " CLIENT_ID
   read -p "Enter your Falcon API Key Client Secret: " CLIENT_SECRET
   read -p "Enter your Falcon Cloud: " CS_CLOUD
   read -p "Enter your Falcon CID: " CS_CID
   read -p "Enter your Falcon Docker API Token: " DOCKER_API_TOKEN

    cd code
    zip -r code.zip *
    mv ./code.zip ../templates
    cd ../templates
    echo -e "$LB\n"
    echo -e "Initializing environment templates...$NC"
    
    aws s3api create-bucket --bucket ${S3Bucket} --region ${AWS_REGION} # --create-bucket-configuration LocationConstraint=${AWS_REGION} || true # comment out --create-bucket-configuration for us-east-1
    echo -e "S3 Bucket Name = ${S3Bucket} $NC"
    aws s3 cp . s3://${S3Bucket}/${S3Prefix} --recursive 
    echo -e "$LB\n"
    echo -e "Standing up environment...$NC"
    aws cloudformation create-stack --stack-name devdays-cnap-stack \
    #--template-url https://${S3Bucket}.s3-${AWS_REGION}.amazonaws.com/${S3Prefix}/entry.yaml \  # for other regions
    --template-url https://${S3Bucket}.s3.amazonaws.com/${S3Prefix}/entry.yaml \  # for us-east-1
    --parameters \
    ParameterKey=FalconClientID,ParameterValue=${CLIENT_ID} \
    ParameterKey=FalconClientSecret,ParameterValue=${CLIENT_SECRET} \
    ParameterKey=S3Bucket,ParameterValue=${S3Bucket} \
    ParameterKey=S3Prefix,ParameterValue=${S3Prefix} \
    ParameterKey=CrowdStrikeCloud,ParameterValue=${CS_CLOUD} \
    ParameterKey=FalconCID,ParameterValue=${CS_CID} \
    ParameterKey=DockerAPIToken,ParameterValue=${DOCKER_API_TOKEN} \
    ParameterKey=KeyPairName,ParameterValue=${KeyPairName} \
    --disable-rollback \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --region ${AWS_REGION}
    echo -e "The Cloudformation stack will take 20-30 minutes to complete.$NC"
    echo -e "\n\nCheck the status at any time with the command \n\naws cloudformation describe-stacks --stack-name devdays-cnap-stack --region ${AWS_REGION}$NC\n\n"
    #sleep 5
    #id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`
    #aws ec2 terminate-instances --region us-west-2 --instance-ids $id
}
env_up
