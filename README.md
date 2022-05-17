# Dev Days 2 Building Blocks

1) Build an EKS cluster using 
AWSQS::EKS::CLUSTER CFT extension
   
Upload files in S3 bucket and load cwp-lab-entrypoint.yaml

## Templates

We are using nested templates as driven primarily by the need to build the EKS cluster control plane before builing the nodes and the bastion server. 

### Initial Template
cwp-lab-entrypoint.yaml - Main template that loads the remaining templates.  We are still referencing the inital aws quickstart buckets as we are building the Bastion host from the original quickstart folders. 

### SetupStack

iam.template.yaml - The first template loaded that builds common resources needed by future templates (mainly IAM roles).


### VPCStack 

vpc.template.yaml - Template creates a VPC with user configurable CIDR range with public and private subnets.  Private subnets have outbound internet connectivity via NAT Gateways.   VPC is a 2 AZ deployment.  The template will pick the first two AZs available in the selected region. 

### EKSControlPlaneStack

eks-cluster.template.yaml - Template builds the EKS control plane

### EKSNodeGroup

eks-nodegroup.template.yaml - Template builds the EKS nodegroup

### BastionStack

linux-bastion.template - Quickstart template 

https://aws-quickstart.s3.us-east-1.amazonaws.com/quickstart-amazon-eks/submodules/quickstart-linux-bastion/templates/linux-bastion.template




