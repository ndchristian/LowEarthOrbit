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

| Variable      | Option        | Description  |
| :------------- |:-------------:| :-----:|
| profile       | --profile     | Profile in your credentials file to be used to communicate with AWS |
| region        | --region      | Which AWS region to execute in |

----------------------------
Commands:
----------------------------

###validate

####Description:

Validates all files with the file extensions: ".json", ".template", ".txt", "yaml", or "yml" for CloudFormation in the specified bucket.

###Options:

| Variable      | Option        | Description                                            | Required |
| :-------------|:-------------:| :-----:                                                | :-----: |
| bucket        | --bucket      | S3 bucket that has the CloudFormation templates.| true |
| prefix        | --prefix      | Prefix or bucket subdirectory where CloudFormation templates are located | false |

----------------------------