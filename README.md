# low-earth-orbit (leo)

------------
About
------------

Leo is a better, faster way to depoy AWS CloudFormation templates.

------------
Installation
------------

Recommended way to install leo is to use [`pip` in a `virtualenv`](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/):

`pip install lowearthorbit`

If you want to install globally:

`sudo pip install lowearthorbit`

Just for your user:

`sudo pip install --user lowearthorbit`

Updating to the latest version:

`sudo pip install --upgrade lowearthorbit`



---------------
Getting Started
---------------
Before getting started with leo, you need to set up AWS credentials. There are several different ways to do this:

* Environment variables
* Shared credentials file
* Config file
* IAM Role

However, the recommended way is to install [aws-cli](https://github.com/aws/aws-cli) and running the `aws configure` command.

More about [AWS Credentials](https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html).

----------------------------
Configurable Options
----------------------------

| Variable                 | Option                     | Description                                                                  | Required  | Type   |
| :-------------:          |:------------:              | :-----------------------------------------------------------------:          | :--------:| :-----:|
| aws-access-key-id        | --aws-access-key-id        | AWS access key ID                                                            | False     | String |
| aws-secret-access-key-id | --aws-secret-access-key-id | AWS secret access key                                                        | False     | String |
| aws_session_token        | --aws-session-token        | AWS temporary session token                                                  | False     | String |
| botocore-session         | --botocore-session         | AWS Use this Botocore session instead of creating a new default one          | False     | String |
| profile                  | --profile                  | The name of a profile to use. If not given, then the default profile is used | False     | String |
| region                   | --region                   | Region when creating new connections                                         | False     | String |
| debug                    | --debug                     | Shows information for debugging                                             | False     | Boolean|

----------------------------
Commands:
----------------------------

### delete

#### Description:

Uploads all files in the given local path with the file extensions: .json, .template, .txt, yaml, or yml into S3 for CloudFormation.

### Options:

| Variable          | Option           | Description                        | Required | Type   |
| :-----------------|:----------------:| :-------------------------------:  | :-----:  | :----: |
| job-identifier    | --job-identifier | Identifies which stacks to delete  | True     | String |


### deploy

#### Description:

Creates or updates CloudFormation stacks.


### Options:

| Variable      | Option          | Description                                                                                                               | Required | Type      |
| :-------------|:-------------:  | :---------------------------------------------------------------------:                                                   | :-----:  | :----:  |
| bucket           | --bucket           | S3 bucket that the CloudFormation templates will be deployed from                                                   | True     | String  |
| prefix           | --prefix           | Prefix or bucket subdirectory where CloudFormation templates will be deployed from                                  | False    | String  |
| gated            | --gated            | Checks with user before deploying an update                                                                         | False    | Boolean |
| job-identifier   | --job-identifier   | Prefix that is added on to the deployed stack names                                                                 | True     | String  |
| parameters       | --parameters       | All parameters that are needed to deploy with. Can either be from a JSON file or typed JSON that must be in quotes  | False    | String  |
| tags             | --tags             | Tags added to all deployed stacks. Must be JSON that's in quotes                                                    | False     | String  |

Parameters JSON syntax:

```[
  {
    "ParameterKey": "string",
    "ParameterValue": "string",
    "UsePreviousValue": true|false,
    "ResolvedValue": "string"
  }
  ...
] 
```
Tags JSON syntax:
```
[
  {
    "Key": "string",
    "Value": "string"
  }
  ...
]
```

----------------------------

### upload

#### Description:

Uploads all files in the given local path with the file extensions: .json, .template, .txt, yaml, or yml into S3 for CloudFormation.

### Options:

| Variable      | Option        | Description                                                                      | Required | Type   |
| :-------------|:-------------:| :---------------------------------------------------------------------:          | :-----:  | :----: |
| bucket        | --bucket      | S3 bucket that the CloudFormation templates will be uploaded to                  | True     | String |
| prefix        | --prefix      | Prefix or bucket subdirectory where CloudFormation templates will be uploaded to | False    | String |
| localpath     | --localpath   | Local path where CloudFormation templates are located                            | True     | String |
----------------------------

### validate

#### Description:

Validates all files with the file extensions: .json, .template, .txt, yaml, or yml for CloudFormation in the specified bucket.

### Options:

| Variable      | Option        | Description                                                              | Required | Type   |
| :-------------|:-------------:| :---------------------------------------------------------------------:  | :-----:  | :----: |
| bucket        | --bucket      | S3 bucket that has the CloudFormation templates                          | True     | String |
| prefix        | --prefix      | Prefix or bucket subdirectory where CloudFormation templates are located | False    | String |

----------------------------

Examples:
----------------------------

Checkout the examples folder for more information.

#### Delete:

```
#!/usr/bin/env bash

source config.conf

echo $PROFILE
echo $PRODBUCKET
echo $PREFIX

leo --profile $PROFILE plan --bucket $PRODBUCKET  --prefix $PREFIX

exit
```

#### Deploy:

```
#!/usr/bin/env bash

source config.conf

echo $PRODBUCKET
echo $JOB_IDENTIFIER
echo $PARAMETERS

leo deploy --bucket $PRODBUCKET --job-identifier $JOB_IDENTIFIER --gated True --parameters $PARAMETERS

exit
```

#### Upload:
```
#!/usr/bin/env bash

source config.conf

#echo $PRODBUCKET
#echo $PREFIX
#echo $LOCALPATH

leo upload --bucket $BUCKET --prefix $PREFIX --localpath $LOCALPATH

exit
```

#### Validate:
```
#!/usr/bin/env bash

source config.conf

echo $PROFILE
echo $PRODBUCKET
echo $PREFIX

leo --profile $PROFILE validate --bucket $PRODBUCKET  --prefix $PREFIX

exit
```
