#!/bin/bash
echo 'Creating zip of s3 bucket files'

cd ../../code
zip -r code.zip *
mv ./code.zip ../S3_Bucket

cd ../S3_Bucket
zip s3bucket.zip *
mv ./s3bucket.zip ../cloudshare/staging/s3bucket.zip


cd ../cloudshare/staging
echo 'Creating zip bundle'
zip cwpdemopackage_v2.zip cwp-se-demo_v2.sh start.sh s3bucket.zip
mv ./cwpdemopackage_v2.zip ../cloudshare_bucket