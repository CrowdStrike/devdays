# DG="\033[1;30m"
# RD="\033[0;31m"
NC="\033[0;0m"
# LB="\033[1;34m"
env_up(){
   
    #git clone https://github.com/CrowdStrike/devdays.git  #NOT APPLICABLE, here for reference.

   EnvHash=$(LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c 5)
   S3Bucket=fcs-stack-${EnvHash}
   AWS_REGION='us-east-1'
   S3Prefix='templates'
   StackName=${S3Bucket}
   TemplateName='entry.yaml'

#    echo 
#    echo -e "Welcome to Dev Days$NC"
#    echo 
#    echo -e "You will asked to provide a Falcon API Key Client ID and Secret." 
#    echo -e "You can create one at https://falcon.crowdstrike.com/support/api-clients-and-keys"
#    echo 
#    echo -e "The Dev Days Workshop environment requires the following API Scope permissions:"
#    echo -e " - AWS Accounts:R"
#    echo -e " - CSPM registration:R/W"
#    echo -e " - CSPM remediation:R/W"
#    echo -e " - Customer IOA rules:R/W"
#    echo -e " - Hosts:R"
#    echo -e " - Falcon Container Image:R/W"
#    echo -e " - Falcon Images Download:R"
#    echo -e " - Kubernetes Protection Agent:W"
#    echo -e " - Sensor Download:R"
#    echo -e " - Event streams:R"
#    echo
#    read -p "Enter your Falcon API Key Client ID: " CLIENT_ID
#    read -p "Enter your Falcon API Key Client Secret: " CLIENT_SECRET
#    echo
#    echo -e "For the next variable (Falcon CID), use the entire string include the 2-character hash which you can find at https://falcon.crowdstrike.com/hosts/sensor-downloads"
#    read -p "Enter your Falcon CID: " CS_CID
#    echo
#    echo -e "You can find your Docker API Token at https://falcon.crowdstrike.com/cloud-security/registration?return_to=eks."
#    echo -e "Click 'Register new Kubernetes Cluster' > 'Self-Managed Kubernetes Service' > enter any random string in the 'Cluster Name' field > Click 'Generate'"
#    echo -e "Copy the value for 'dockerAPIToken' from the script that appears and use it below"
#    read -p "Enter your Falcon Docker API Token: " DOCKER_API_TOKEN
#    read -p "Enter your Falcon Cloud [us-1]: " CS_CLOUD
#    CS_CLOUD=${CS_CLOUD:-us-1}
#    echo
#    echo -e "Enter an existing key-pair in us-east-1 for connecting to EC2 instances. You can create one at https://us-east-1.console.aws.amazon.com/ec2#KeyPairs:"
#    read -p "Enter your EC2 key-pair name [cs-key]: " KeyPairName
#    KeyPairName=${KeyPairName:-cs-key}

   aws s3api create-bucket --bucket $S3Bucket --region $AWS_REGION
   
   cd templates
   aws s3 cp . s3://${S3Bucket}/${S3Prefix} --recursive 
   echo
   echo -e "Standing up environment...$NC"

   aws cloudformation create-stack --stack-name $StackName --template-url https://${S3Bucket}.s3.amazonaws.com/${S3Prefix}/${TemplateName} --region $AWS_REGION --disable-rollback \
   --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
   --parameters \
   ParameterKey=S3Bucket,ParameterValue=${S3Bucket} \
   ParameterKey=S3Prefix,ParameterValue=${S3Prefix} \
   ParameterKey=EnvHash,ParameterValue=$EnvHash
#    ParameterKey=KeyPairName,ParameterValue=${KeyPairName} \
#    ParameterKey=FalconClientID,ParameterValue=$CLIENT_ID \
#    ParameterKey=FalconClientSecret,ParameterValue=$CLIENT_SECRET \
#    ParameterKey=CrowdStrikeCloud,ParameterValue=$CS_CLOUD \
#    ParameterKey=FalconCID,ParameterValue=$CS_CID \
#    ParameterKey=DockerAPIToken,ParameterValue=$DOCKER_API_TOKEN \


    echo -e "The Cloudformation stack will take 20-30 minutes to complete.$NC"
    echo -e "\n\nCheck the status at any time with the command \n\naws cloudformation describe-stacks --stack-name $StackName --region $AWS_REGION$NC\n\n"
    #sleep 5
    #id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`
    #aws ec2 terminate-instances --region $AWS_REGION --instance-ids $id
}
env_up
