import logging
from crhelper import CfnResource
from time import sleep
import json
import boto3
from semantic_version import Version
from random import choice

execution_trust_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Principal': {
                'Service': ['lambda.amazonaws.com']
            },
            'Action': 'sts:AssumeRole'
        }
    ]
}

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='DEBUG')
lmbd = boto3.client('lambda')
ssm = boto3.client('ssm')
iam = boto3.client("iam")
sts = boto3.client("sts")
account_id = sts.get_caller_identity()['Account']


def put_role(role_name, policy, trust_policy):
    retries = 5
    while True:
        try:
            try:
                response = iam.create_role(Path='/', RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
                role_arn = response['Role']['Arn']
            except iam.exceptions.EntityAlreadyExistsException:
                role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            try:
                response = iam.create_policy(Path='/', PolicyName=role_name, PolicyDocument=json.dumps(policy))
                arn = response['Policy']['Arn']
            except iam.exceptions.EntityAlreadyExistsException:

                arn = f"arn:aws:iam::{account_id}:policy/{role_name}"
                versions = iam.list_policy_versions(PolicyArn=arn)['Versions']
                if len(versions) >= 5:
                    oldest = [v for v in versions if not v['IsDefaultVersion']][-1]['VersionId']
                    iam.delete_policy_version(PolicyArn=arn, VersionId=oldest)
                iam.create_policy_version(PolicyArn=arn, PolicyDocument=json.dumps(policy), SetAsDefault=True)
            iam.attach_role_policy(RoleName=role_name, PolicyArn=arn)
            return role_arn
        except Exception as e:
            print(e)
            retries -= 1
            if retries < 1:
                raise
            sleep(choice(range(1, 10)))


def get_current_version(type_name):
    try:
        return Version(ssm.get_parameter(Name=f"/cfn-custom-resources/{type_name}/version")['Parameter']['Value'])
    except ssm.exceptions.ParameterNotFound:
        return Version('0.0.0')


def set_version(type_name, type_version):
    ssm.put_parameter(Name=f"/cfn-custom-resources/{type_name}/version", Value=type_version, Type='String', Overwrite=True)


@helper.create
@helper.update
def register(event, _):
    logger.error(f"event: {json.dumps(event)}")
    function_name = event['ResourceProperties']['Name']
    version = Version(event['ResourceProperties'].get('Version', '0.0.0'))
    if version != Version('0.0.0') and version <= get_current_version(function_name):
        print("version already registered is greater than this version, leaving as is.")
        try:
            arn = lmbd.get_function_configuration(FunctionName=function_name)['FunctionArn']
            return arn
        except lmbd.exceptions.ResourceNotFoundException:
            print("resource missing, re-registering...")
    execution_role_arn = put_role(function_name, event['ResourceProperties']['IamPolicy'], execution_trust_policy)
    arn = put_function(function_name, execution_role_arn, event['ResourceProperties']['S3Uri'])
    set_version(function_name, event['ResourceProperties'].get('Version', '0.0.0'))
    return arn


def put_function(function_name, execution_role, zip_uri):
    try:
        arn = lmbd.get_function_configuration(FunctionName=function_name)['FunctionArn']
        exists = True
    except lmbd.exceptions.ResourceNotFoundException:
        exists = False
    kwargs = {
        'FunctionName': function_name,
        'Role': execution_role,
        'Handler': 'lambda_function.lambda_handler',
        'Timeout': 900,
        'MemorySize': 1024,
        'Runtime': 'python3.8'
    }
    if not exists:
        kwargs['Code'] = {
            'S3Bucket': zip_uri.split('/')[2],
            'S3Key': '/'.join('s3://bucket/keyprefix/mid/filename.ext'.split('/')[3:])
        }
        return lmbd.create_function(**kwargs)['FunctionArn']
    else:
        lmbd.update_function_code(
            FunctionName=function_name,
            S3Bucket=zip_uri.split('/')[2],
            S3Key='/'.join('s3://bucket/keyprefix/mid/filename.ext'.split('/')[3:])
        )
        lmbd.update_function_configuration(**kwargs)


@helper.delete
def delete(event, _):
    # We don't know whether other stacks are using the custom resource, so we retain the resource after delete.
    return


def lambda_handler(event, context):
    helper(event, context)
