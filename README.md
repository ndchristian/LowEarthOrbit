# low-earth-orbit (leo)

------------
About
------------

A better, faster way to deploy AWS CloudFormation templates.

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

Leo creates a file called *.leo* at `~/.leo` on Linux, macOS, or Unix, or at `C:\Users\*USERNAME*\.leo` on Windows. This is for specifically Leo config commands.

In Leo, templates must be numbered in the order to be deployed in.

*Example:*

```
00-template.yml
01-template.yml
02-template.yml
```

## Synopsis

`leo [options] <command> [parameters]`

Use *leo --help* for all options and commands or *leo \<command\> --help* for specific command parameters.

## Options

*--aws-access-key-id (String)*

The AWS access key used to access AWS. This is optional, if not used the default credentials configured will be used. This should be used if you want to override the default credentials.

*--aws-secret-access-key-id (String)*

The secret AWS access key used to access AWS. This is optional, if not used the default credentials configured will be used. This should be used if you want to override the default credentials.

*--aws-session-token (String)*

The session token used to access AWS. This is optional, if not used the default credentials configured will be used. This should be used if you want to override the default credentials.

*--botocore-session (String)*

An already created botocore session. This is optional, use this if you want to use an already created botocore session instead of creating a new one.

*--profile (String)*

The name of a profile to use. If not used, then the default profile is used.

*--region (String)*

AWS Region to use. If not used, then the default region is used.

*--debug (Boolean)*

This is optional, use to show debugging information.

Commands:
----------------------------

### delete

#### Description:

Uploads all files in the given local path with the file extensions: .json, .template, .txt, yaml, or yml into S3 for CloudFormation.

#### Synopsis:

```
delete
--job-identifier <value>
--config-name <value>
```

#### Options:

*--job-identifier (String)*

Identifies which stack(s) to delete. This is required unless *--config-name* is used.

***Note:***

*Job identifiers must only be alphanumeric characters and hyphens. It must start with an alphabetic character due to stack name restraints.*

*--config-name (String)*

Name of the config to use. This is required unless *--job-identifier* is used.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To delete a stack or stacks:*

```
leo --region us-west-2 delete --job-identifier jobident
```

------



### deploy

#### Description:

Creates or updates CloudFormation stacks.

#### Synopsis:

```
deploy
--bucket <value>
--prefix <value>
--gated <value>
--job-identifier <value>
--parameters <value>
--notification-arns <value>
--rollback-configuration <value>
--tags <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Name of the S3 bucket used to deploy the CloudFormation templates from. This is required unless *--config-name* is used.

*--prefix (String)*

The location within the bucket where the CloudFormation templates are.

*--gated (Boolean)*

Default is 'False'. If set to 'True' a prompt asking to deploy will be displayed every time a stack is ready

*--job-identifier (String)*

Adds a prefix to the stack name to help identify a group of stacks. This is required unless *--config-name* is used.

***Note:***

*Job identifiers must only be alphanumeric characters and hyphens. It must start with an alphabetic character due to stack name restraints.*

*--parameters (JSON)*

Parameter keys and parameter values required by the CloudFormation templates to deploy. If a parameter key and parameter value is not given, a prompt will ask the user to give a parameter value.

JSON Syntax:

```
[
  {
    "ParameterKey": "string",
    "ParameterValue": "string",
    "UsePreviousValue": true|false,
    "ResolvedValue": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--notification-arns (JSON)*

The SNS (Simple Notification Service) topic ARNs to notify about stack related events.

JSON Syntax:

```
[
"string", 
"string", 
"string"
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--rollback-configuration (JSON)*

The rollback triggers that CloudFormation monitors for during deployment, and for the specified period afterwards.

```
{
"RollbackTriggers": [
{
"Arn": "string",
"Type": "string"
}
...
],
"MonitoringTimeInMinutes": integer
}
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--tags (JSON)*

The key-value pairs associated with each deployed stack. These tags will also be propagated to the resources created by deployment. There is a limit of 50 tags that can be specified.

JSON Syntax:

```
[
  {
    "Key": "string",
    "Value": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--config-name (String)*

Name of the config to be used. This is required unless *--bucket* and/or *--job-identifier* is used.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To deploy stack(s):*

```
leo deploy --bucket foobucket --parameters "[{'ParameterKey':'AccountNo','ParameterValue':'*********'},{'ParameterKey':'S3BucketCode','ParameterValue':'BUCKET'},{'ParameterKey':'S3KeyCode','ParameterValue':'KEY'},{'ParameterKey':'Endpoint','ParameterValue':'USER@EXAMPLE.COM'},{'ParameterKey':'Protocol','ParameterValue':'email'},{'ParameterKey':'TagEnvironment','ParameterValue':'NONPROD'},{'ParameterKey':'TagPoC','ParameterValue':'USER@EXAMPLE.COM'}]" --config-name fooconfig
```

----------------------------

### plan

#### Description:

Gathers information about an upcoming deployment. Displays what resources will be created/changed and the estimated cost URL.

#### Synopsis:

```
plan
--bucket <value>
--prefix <value>
--job-identifier <value>
--parameters <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Name of the S3 bucket used to gather CloudFormation templates from. This is required unless *--config-name* is used.

*--prefix (String)*

The location within the bucket where the CloudFormation templates are.

*--job-identifier (String)*

Prefix used to identify CloudFormation stacks. This is required unless *--config-name* is used.

*--parameters (JSON)*

Parameter keys and parameter values required by the CloudFormation templates to gather a plan. If a parameter key and parameter value is not given, a prompt will ask the user to give a parameter value.

JSON Syntax:

```
[
  {
    "ParameterKey": "string",
    "ParameterValue": "string",
    "UsePreviousValue": true|false,
    "ResolvedValue": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--config-name (String)*

Name of the config to be used. This is required unless *--bucket* and/or *--job-identifier* are used.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To plan for a deployment*

```
leo plan --config-name fooconfig
```

----------------------------

### upload

#### Description:

Uploads all files in the given local path with the file extensions: .json, .template, .txt, yaml, or yml into S3 for CloudFormation.

#### Synopsis:

```
upload
--bucket <value>
--prefix <value>
--local-path <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Bucket that the CloudFormation templates will be uploaded to. This is required unless *--config-name* is used.

*--prefix (String)*

Location within the bucket that the CloudFormation templates will be uploaded to.

*--local-path (String)*

Local path where the CloudFormations templates are located.

*--config-name (String)*

Name of the config to be used. This is required unless *--bucket* and/or *--local-path* are used.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

#### Examples:

##### *To upload CloudFormation templates:*

```
leo upload --bucket foobucket --localpath /path/to/templates/
```

----------------------------

### validate

#### Description:

Validates all files with the file extensions: .json, .template, .txt, yaml, or yml for CloudFormation in the specified bucket.

#### Synopsis:

```
validate
--bucket <value>
--prefix <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Bucket that the Cloudformation templates are in. This is required unless *--config-name* is used.

*--prefix*

The location within the bucket where the CloudFormation templates are located.

*--config-name*

Name of the config to be used. This is required unless *--bucket* is used.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To validate templates:*

```
leo validate --bucket foobucket
```

### create-config

#### Description:

Creates a configuration entry that stores all given values.

#### Synopsis:

```
create-config
--bucket <value>
--prefix <value>
--gated <value>
--local-path <value>
--job-identifier <value>
--parameters <value>
--notification-arns <value>
--rollback-configuration <value>
--tags <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Name of the S3 bucket used to deploy/upload/validate the CloudFormation templates from. 

*--prefix (String)*

The location within the bucket where the CloudFormation templates are.

*--gated (Boolean)*

If set to 'True' a prompt asking to deploy will be displayed every time a stack is ready

*--local-path (String)*

Local path where the CloudFormations templates are located.

*--job-identifier (String)*

Adds a prefix to the stack name to help identify a group of stacks.

***Note:***

*Job identifiers must only be alphanumeric characters and hyphens. It must start with an alphabetic character due to stack name restraints.*

*--parameters (JSON)*

Parameter keys and parameter values required by the CloudFormation templates to deploy. If a parameter key and parameter value is not given, a prompt will ask the user to give a parameter value.

JSON Syntax:

```
[
  {
    "ParameterKey": "string",
    "ParameterValue": "string",
    "UsePreviousValue": true|false,
    "ResolvedValue": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--notification-arns (JSON)*

The SNS (Simple Notification Service) topic ARNs to notify about stack related events.

JSON Syntax:

```
[
"string", 
"string", 
"string"
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--rollback-configuration (JSON)*

The rollback triggers that CloudFormation monitors for during deployment, and for the specified period afterwards.

```
{
"RollbackTriggers": [
{
"Arn": "string",
"Type": "string"
}
...
],
"MonitoringTimeInMinutes": integer
}
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--tags (JSON)*

The key-value pairs associated with each deployed stack. These tags will also be propagated to the resources created by deployment. There is a limit of 50 tags that can be specified.

JSON Syntax:

```
[
  {
    "Key": "string",
    "Value": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--config-name (String)*

Name of the config.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To create a config:*

```
leo create-config --bucket foobucket --parameters "[{'ParameterKey':'AccountNo','ParameterValue':'*********'},{'ParameterKey':'S3BucketCode','ParameterValue':'BUCKET'},{'ParameterKey':'S3KeyCode','ParameterValue':'KEY'},{'ParameterKey':'Endpoint','ParameterValue':'USER@EXAMPLE.COM'},{'ParameterKey':'Protocol','ParameterValue':'email'},{'ParameterKey':'TagEnvironment','ParameterValue':'NONPROD'},{'ParameterKey':'TagPoC','ParameterValue':'USER@EXAMPLE.COM'}]" --config-name fooconfig
```

### edit-config

#### Description:

Edits an already existing configuration. Any values specified will replace the values in the config.

#### Synopsis:

```
edit-config
--bucket <value>
--prefix <value>
--gated <value>
--local-path <value>
--job-identifier <value>
--parameters <value>
--notification-arns <value>
--rollback-configuration <value>
--tags <value>
--config-name <value>
```

#### Options:

*--bucket (String)*

Name of the S3 bucket used to deploy/upload/validate the CloudFormation templates from. 

*--prefix (String)*

The location within the bucket where the CloudFormation templates are.

*--gated (Boolean)*

If set to 'True' a prompt asking to deploy will be displayed every time a stack is ready

*--local-path (String)*

Local path where the CloudFormations templates are located.

*--job-identifier (String)*

Adds a prefix to the stack name to help identify a group of stacks.

***Note:***

*Job identifiers must only be alphanumeric characters and hyphens. It must start with an alphabetic character due to stack name restraints.*

*--parameters (JSON)*

Parameter keys and parameter values required by the CloudFormation templates to deploy. If a parameter key and parameter value is not given, a prompt will ask the user to give a parameter value.

JSON Syntax:

```
[
  {
    "ParameterKey": "string",
    "ParameterValue": "string",
    "UsePreviousValue": true|false,
    "ResolvedValue": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--notification-arns (JSON)*

The SNS (Simple Notification Service) topic ARNs to notify about stack related events.

JSON Syntax:

```
[
"string", 
"string", 
"string"
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--rollback-configuration (JSON)*

The rollback triggers that CloudFormation monitors for during deployment, and for the specified period afterwards.

```
{
"RollbackTriggers": [
{
"Arn": "string",
"Type": "string"
}
...
],
"MonitoringTimeInMinutes": integer
}
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--tags (JSON)*

The key-value pairs associated with each deployed stack. These tags will also be propagated to the resources created by deployment. There is a limit of 50 tags that can be specified.

JSON Syntax:

```
[
  {
    "Key": "string",
    "Value": "string"
  }
  ...
]
```

***Note:***

*JSON syntax must be wrapped in opposing quotations that are in the JSON syntax. For example, the example above would be wrapped in single quotations.* 

*--config-name (String)*

Name of the config.

***Note:***

*If values from other options are specified, then they will override the respective value in the configuration.*

#### Example:

##### *To edit a config:*

```
leo edit-config --bucket barbucket --parameters "[{'ParameterKey':'AccountNo','ParameterValue':'*********'},{'ParameterKey':'S3BucketCode','ParameterValue':'BUCKET'},{'ParameterKey':'S3KeyCode','ParameterValue':'KEY'},{'ParameterKey':'Endpoint','ParameterValue':'USER@EXAMPLE.COM'},{'ParameterKey':'Protocol','ParameterValue':'email'},{'ParameterKey':'TagEnvironment','ParameterValue':'NONPROD'},{'ParameterKey':'TagPoC','ParameterValue':'USER@EXAMPLE.COM'}]" --config-name fooconfig
```

------

### delete-config

#### Description:

Deletes a configuration.

#### Synopsis:

```
delete-config
--config-name <value>
```

#### Options:

*--config-name (String)*

Name of the config.

#### Example:

##### *To delete a config:*

```
leo delete-config --config-name fooconfig

```

------

### list-configs

#### Description:

List all configuration names. If *--config-name* is specified it will show the values of the specified configuration.

#### Synopsis:

```
list-configs
--config-name <value>
```

#### Options:

*--config-name (String)*

Name of the config.

#### Examples:

##### *To list all configs:*

```
leo list-configs
```

##### To show a specific config contents:

```
leo list-configs --config-name fooconfig
```

