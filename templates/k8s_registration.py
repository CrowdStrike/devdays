import boto3
import os
import logging
import re
import time
import json
import requests
import base64
from falconpy import KubernetesProtection
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

permissions_boundary = os.environ['permissions_boundary']
aws_region = os.environ['aws_region']
s3_staging_bucket = os.environ['s3_staging_bucket']
cs_cloud = os.environ['cs_cloud']
s3_prefix = os.environ['s3_prefix']
secret_store_name = os.environ['secret_store_name']
secret_store_region = os.environ['secret_store_region']

K8S_ROLE_TEMPLATE = 'KPRole.yaml'
K8S_STACK_NAME = 'CrowdStrike-Kubernetes-Protection-Integration'

class AccountRegistrationException(Exception):
    pass

class AccountStatusException(Exception):
    pass

def get_secret(secret_name, secret_region):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=secret_region
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )


    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']

        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return secret


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']

    json_responseBody = json.dumps(responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
    except Exception as error:
        logger.info("Error {} sending CFN reponse: ".format(error))


def get_params(url_string):
    """

    Args:
        url_string (str): String containing template url and params

    Returns:
         dict: Dictionary of key value pairs

    """
    param_list = re.split('\?|&', url_string)
    param_name_prefix = "param_"
    cft_params = []
    key_dict = {}
    for param in param_list:
        if param_name_prefix in param:
            param_key = param.split(param_name_prefix)[1].split('=')[0]
            param_value = param.split(param_name_prefix)[1].split('=')[1]
            key_dict['ParameterKey'] = param_key
            key_dict['ParameterValue'] = param_value
            cft_params.append(dict(key_dict))
    #
    # We need to add a permissions boundary for Cloudshare IAM Roles
    #
    key_dict['ParameterKey'] = 'PermissionsBoundary'
    key_dict['ParameterValue'] = permissions_boundary
    cft_params.append(dict(key_dict))
    return cft_params


def load_cft(CFT, params):
    """

    Args:
        CFT (obj): Boto3 CFN object
        params (dict): Params to apply to the template

    Returns (bool):


    """

    #
    # Delay the creation of the stack for Bucket ACL permissions to be replicated
    # We need to wait for the s3 bucket specified in the return parameters to be available
    #
    time.sleep(10)
    # path has the syntax dir/dir
    if s3_prefix == '':
        s3_path = '/'
    else:
        s3_path = '/' + s3_prefix + '/'

    cspm_template_url = 'https://' + s3_staging_bucket + '.s3.amazonaws.com' + s3_path + K8S_ROLE_TEMPLATE
    logger.info('template {}'.format(cspm_template_url))
    logger.info('params {}'.format(params))
    try:
        stack_info = CFT.create_stack(
            StackName=K8S_STACK_NAME,
            TemplateURL=cspm_template_url,
            Parameters=params,
            TimeoutInMinutes=5,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            # RoleARN='string',
            Tags=[
                {
                    'Key': 'Vendor',
                    'Value': 'CrowdStrike'
                },
            ],
        )
        if stack_info.get('StackId'):
            return True
        else:
            return False
    except Exception as e:
        logger.info('Exception creating K8s role template')
        return False


def delete_cft(CFT):
    """

    Args:
        CFT (obj): Boto3 CFN object
        params (dict): Params to apply to the template

    Returns (bool):


    """

    #
    # Delay the creation of the stack for Bucket ACL permissions to be replicated
    # We need to wait for the s3 bucket specified in the return parameters to be available
    #
    try:
        stack_info = CFT.delete_stack(
            StackName=K8S_STACK_NAME,
        )
        if stack_info:
            return True
        else:
            return False
    except Exception as e:
        logger.info('Exception creating K8s role template')
        return False


def get_k8s_aws_account(account_id, k8s_client):
    """

    Args:
        account_id string: AWS Account ID
        k8s_client object: k8s API object

    Returns: Dictionary

    """
    response = k8s_client.get_aws_accounts(ids=account_id)
    if response['status_code'] == 200:
        return response
    elif response['status_code'] == 207:
        return
    else:
        raise AccountStatusException()


def register_k8s_aws_account(account_id, k8s_client, aws_region):
    """

    Args:
        account_id:
        k8s_client:

    Returns Dict:

    """
    response = k8s_client.create_aws_account(account_id=account_id, region=aws_region)
    if response['status_code'] != 201:
        raise AccountRegistrationException(response['body']['errors'][0])
    else:
        return response


def lambda_handler(event, context):
    """
    Registers the AWS account and then retrieves the account setup url.
    Extracts the template params from the url link in the API response
    Loads the CFT
    Args:
        event:
        context:

    Returns:

    """
    STATUS = 'FAILED'
    logger.info('Got event {}'.format(event))
    logger.info('Context {}'.format(context))

    accountId = context.invoked_function_arn.split(":")[4]

    cft_client = boto3.client('cloudformation')

    secret_str = get_secret(secret_store_name, secret_store_region)
    if secret_str:
        secrets_dict = json.loads(secret_str)
        FalconClientId = secrets_dict['client_id']
        FalconSecret = secrets_dict['client_secret']
    falcon = KubernetesProtection(client_id=FalconClientId,
                                  client_secret=FalconSecret,
                                  base_url=cs_cloud
                                  )
    if event['RequestType'] == 'Create':

        try:
            #
            # First check if account is already registered.
            # If it is we will proceed without registration
            #
            k8s_acct_details = get_k8s_aws_account(accountId, falcon)
            if not k8s_acct_details:
                response = register_k8s_aws_account(accountId, falcon, aws_region)
                # Now the account is registered we can get the details.
                k8s_acct_details = get_k8s_aws_account(accountId, falcon)
            url = k8s_acct_details['body']['resources'][0]['cloudformation_url']
            cft_params_dict = get_params(url)
            if load_cft(cft_client, cft_params_dict):
                STATUS = 'SUCCESS'
            else:
                STATUS = 'FAILED'
        except Exception as error:
            logger.info('Error {} registering k8s protection account'.format(error))
            STATUS = 'FAILED'

    elif event['RequestType'] == 'Delete':
        try:
            delete_cft(cft_client)
            response = falcon.delete_aws_accounts(ids=accountId)
            if response['status_code'] == 200:
                logger.info('Deleted account {}'.format(accountId))
            # Send CFN response Success anyway so that the stack deletion can continue
        except Exception as error:
            logger.info('Error {} deleting K8s protection account'.format(error))
        STATUS = 'SUCCESS'

    cfnresponse_send(event, context, STATUS, 'k8s_registration', "CustomResourcePhysicalID")

