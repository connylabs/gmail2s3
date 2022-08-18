# Gmail2S3

Your main CLI program should be written `gmail2s3.cli:cli`
and will then be registered as the CLI command `gmail2s3` .


"Store all incoming emails of Google Mail account to S3, including attachments"

## Getting Started
### Google Oauth CLientID
The first step is to create GoogleAPI Oauth Client ID and store it as a `client_secret.json` file:
The process is described in the simplegmail documentation: [https://github.com/jeremyephron/simplegmail#getting-started](https://github.com/jeremyephron/simplegmail#getting-started)


### Google Account Token

The following step is to receive a token that grant access to a gmail account.
This command is starting an oauth2 flow, it opens the default browser to login and grant permission.
in this example the token is stored in the  "gtoken.json" file.

``` shell
./bin/gmail2s3 gmail-login -k client_secret.json -t gtoken.json
```

### Configure the application
Edit the `config.yaml` file with the S3 credentials and the paths to the two previous files:

``` yaml
gmail:
  client_secret: "client_secret.json"
  gmail_token: "gtoken.json"

s3:
  endpoint: null
  access_key: 'AK***************'
  secret_key: 'D7************3U'
  region: 'eu-central-1'
  prefix: 'emails/'
  bucket: 'my-emails'

```

## Email Sync
Email sync upload to S3 the selected emails

Most commands can filter email via labels and dates.
labels can also be excluded.
By default, gmail2s3 apply the label "s3" to all emails already processed.
To process email only once, the label s3 can be filtered out

This command upload all emails to s3 that has the label "new" and not the label "s3"
```
gmail2s3 gmail-sync -l='new' -e="s3" --output yaml
```

Dry-run: to first test the command, the `--info` option can be used. It only count the number of emails filtered but doesn't sync them
```
gmail2s3 gmail-sync -l='new' -e="s3" --output yaml
```


## Email Forward
Gmail forward can happen only at the reception, there's no possibility to forward multiple emails directly.
Gmail2S3 can perform this action. It works similarly than email-sync:

```shell
gmail2s3 gmail-forward -l=emails-to-forward --set-label=forwarded -e="forwarded"  --to=address-to-forward@example.com --raw
```
The option --raw will try to do the least number of modification to the email.
Without it, the subject can be modified with a prefix:

``` shell
gmail2s3 gmail-forward -l=emails-to-forward --set-label=forwarded -e="forwarded"  --to=address-to-forward@example.com --prefix="[FWD][G2S3]"
```
