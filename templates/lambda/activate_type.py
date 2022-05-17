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
                'Service': ['resources.cloudformation.amazonaws.com', 'lambda.amazonaws.com']
            },
            'Action': 'sts:AssumeRole'
        }
    ]
}
log_trust_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Principal': {
                'Service': ['cloudformation.amazonaws.com', 'resources.cloudformation.amazonaws.com']
            },
            'Action': 'sts:AssumeRole'
        }
    ]
}
log_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:DescribeLogGroups',
                       'logs:DescribeLogStreams', 'logs:PutLogEvents', 'cloudwatch:ListMetrics',
                       'cloudwatch:PutMetricData'],
            'Resource': '*'
        }
    ]
}

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='DEBUG')
cfn = boto3.client('cloudformation')
# ssm = boto3.client('ssm')
iam = boto3.client("iam")
sts = boto3.client("sts")
identity = sts.get_caller_identity()
account_id = identity['Account']
partition = identity['Arn'].split(':')[1]


def put_role(role_name, policy, trust_policy):
    retries = 5
    while True:
        try:
            try:
                response = iam.create_role(Path='/', RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
                role_arn = response['Role']['Arn']
            except iam.exceptions.EntityAlreadyExistsException:
                role_arn = f"arn:{partition}:iam::{account_id}:role/{role_name}"
            try:
                response = iam.create_policy(Path='/', PolicyName=role_name, PolicyDocument=json.dumps(policy))
                arn = response['Policy']['Arn']
            except iam.exceptions.EntityAlreadyExistsException:

                arn = f"arn:{partition}:iam::{account_id}:policy/{role_name}"
                versions = iam.list_policy_versions(PolicyArn=arn)['Versions']
                if len(versions) >= 5:
                    oldest = [v for v in versions if not v['IsDefaultVersion']][-1]['VersionId']
                    iam.delete_policy_version(PolicyArn=arn, VersionId=oldest)
                while True:
                    try:
                        iam.create_policy_version(PolicyArn=arn, PolicyDocument=json.dumps(policy), SetAsDefault=True)
                        break
                    except Exception as e:
                        if 'you must delete an existing version' in str(e):
                            versions = iam.list_policy_versions(PolicyArn=arn)['Versions']
                            oldest = [v for v in versions if not v['IsDefaultVersion']][-1]['VersionId']
                            iam.delete_policy_version(PolicyArn=arn, VersionId=oldest)
                            continue
                        raise
            iam.put_role_permissions_boundary(
                RoleName=role_name,
                PermissionsBoundary= f"arn:aws:iam::{account_id}:policy/BoundaryForAdministratorAccess"
            )
            iam.attach_role_policy(RoleName=role_name, PolicyArn=arn)
            return role_arn
        except Exception as e:
            print(e)
            retries -= 1
            if retries < 1:
                raise
            sleep(choice(range(1,10)))

# def get_current_version(type_name):
#     try:
#         return Version(ssm.get_parameter(Name=f"/cfn-registry/{type_name}/version")['Parameter']['Value'])
#     except ssm.exceptions.ParameterNotFound:
#         return Version('0.0.0')


# def set_version(type_name, type_version):
#     ssm.put_parameter(Name=f"/cfn-registry/{type_name}/version", Value=type_version, Type='String', Overwrite=True)


def stabilize(token):
    p = cfn.describe_type_registration(RegistrationToken=token)
    while p['ProgressStatus'] == "IN_PROGRESS":
        sleep(5)
        p = cfn.describe_type_registration(RegistrationToken=token)
    if p['ProgressStatus'] == 'FAILED':
        if 'to finish before submitting another deployment request for ' not in p['Description']:
            raise Exception(p['Description'])
        return None
    return p['TypeVersionArn']


@helper.create
@helper.update
def register(event, _):
    logger.error(f"event: {json.dumps(event)}")
    # type_name = event['ResourceProperties']['TypeName'].replace("::", "-").lower()
    # execution_role_arn = put_role(type_name, event['ResourceProperties']['IamPolicy'], execution_trust_policy)
    # log_role_arn = put_role('CloudFormationRegistryResourceLogRole', log_policy, log_trust_policy)
    # kwargs = {
    #     "Type": 'RESOURCE',
    #     "TypeName": event['ResourceProperties']['TypeName'],
    #
    #    # "SchemaHandlerPackage": event['ResourceProperties']['SchemaHandlerPackage'],
    #     "LoggingConfig": {
    #         "LogRoleArn": log_role_arn,
    #         "LogGroupName": f"/cloudformation/registry/{type_name}"
    #     },
    #     "ExecutionRoleArn": execution_role_arn
    # }
    type_name = event['ResourceProperties']['TypeName'].replace("::", "-").lower()
    execution_role_arn = put_role(type_name, event['ResourceProperties']['IamPolicy'], execution_trust_policy)
    log_role_arn = put_role('CloudFormationRegistryResourceLogRole', log_policy, log_trust_policy)
    kwargs = {
        "Type": 'RESOURCE',
        "PublicTypeArn": event['ResourceProperties']['PblicTypeArn'],
        "AutoUpdate": True,
        "LoggingConfig": {
            "LogRoleArn": log_role_arn,
            "LogGroupName": f"/cloudformation/registry/{type_name}"
        },
        "ExecutionRoleArn": execution_role_arn
    }
    retries = 3
    while True:
        try:
            try:
                response = cfn.activate_type(**kwargs)
            except cfn.exceptions.CFNRegistryException as e:
                if "Maximum number of versions exceeded" not in str(e):
                    raise
                continue
            version_arn = stabilize(response['RegistrationToken'])
            break
        except Exception as e:
            if not retries:
                raise
            retries -= 1
            logger.error(e, exc_info=True)
            sleep(60)
    return

#
# def delete_oldest(name):
#     versions = cfn.list_type_versions(Type='RESOURCE', TypeName=name)['TypeVersionSummaries']
#     if len(versions) < 2:
#         return
#     try:
#         try:
#             cfn.deregister_type(Arn=versions[0]['Arn'])
#         except cfn.exceptions.CFNRegistryException as e:
#             if "is the default version" not in str(e):
#                 raise
#             cfn.deregister_type(Arn=versions[1]['Arn'])
#     except cfn.exceptions.TypeNotFoundException:
#         print("version already deleted...")


@helper.delete
def delete(event, _):
    # We don't know whether other stacks are using the resource type, so we retain the resource after delete.
    return


def lambda_handler(event, context):
    helper(event, context)
