#!/bin/bash
echo ${AWS_REGION}
yum install -y jq  && yum install -y openssl
curl -o kubectl https://amazon-eks.s3-us-west-2.amazonaws.com/1.21.2/2021-07-05/bin/linux/amd64/kubectl
chmod +x ./kubectl
mv ./kubectl /usr/bin/kubectl
kubectl apply -f https://amazon-eks.s3.us-west-2.amazonaws.com/manifests/${AWS_REGION}/vpc-resource-controller/latest/vpc-resource-controller.yaml
curl -o webhook-create-signed-cert.sh https://amazon-eks.s3.us-west-2.amazonaws.com/manifests/${AWS_REGION}/vpc-admission-webhook/latest/webhook-create-signed-cert.sh
curl -o webhook-patch-ca-bundle.sh https://amazon-eks.s3.us-west-2.amazonaws.com/manifests/${AWS_REGION}/vpc-admission-webhook/latest/webhook-patch-ca-bundle.sh
curl -o vpc-admission-webhook-deployment.yaml https://amazon-eks.s3.us-west-2.amazonaws.com/manifests/${AWS_REGION}/vpc-admission-webhook/latest/vpc-admission-webhook-deployment.yaml
chmod +x webhook-create-signed-cert.sh webhook-patch-ca-bundle.sh
./webhook-create-signed-cert.sh
mkdir -p ~/.kube;
cat > ~/.kube/config <<EOF
  apiVersion: v1
  clusters:
  - cluster:
      server: ${K8S_ENDPOINT}
      certificate-authority-data: ${K8S_CA_DATA}
    name: kubernetes
  contexts:
  - context:
      cluster: kubernetes
      user: aws
    name: aws
  current-context: aws
  kind: Config
  preferences: {}
  users:
  - name: aws
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1alpha1
        command: aws-iam-authenticator
        args:
          - "token"
          - "-i"
          - "${K8S_CLUSTER_NAME}"
EOF
cat ./vpc-admission-webhook-deployment.yaml | ./webhook-patch-ca-bundle.sh > vpc-admission-webhook.yaml
rm -rf ~/.kube/config
kubectl apply -f vpc-admission-webhook.yaml
