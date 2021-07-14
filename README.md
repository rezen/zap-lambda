# zap-lambda
*Experimental*  
What if you could run ZAP in a lambda? That would be cool? This first POC spiders a site and spits out the URLs and alerts.

## Requirements
- bash
- docker
- AWS
  - `aws` cli

docker-compose up --abort-on-container-exit

## Try it out
- Create the package, run `./build.sh`
  - The artifact will be created in `_builds/zap-aws-*.zip`
- Deploy lambda
  - **Magically**
    - `./deploy.sh zap-bucket-name`
  - **Manually**
    - Upload the artifact to a new/existing s3 bucket
    - Create a lambda 
      - Author from scratch
      - Name `zap-lambda-poc`
      - Runtime `Python 2.7`
      - Create function
      - Set code entry type to the address of the s3 bucket the artifacts lives
      - For handler specify `zap_lambda.handler`
      - Save
- Navigate in AWS web console to lambda and *Test*
  - `{"target":"https://example.com"}`

## AWS
AWS limits total package size of 250mb, so I had to put ZAP on a diet to fit under that limit.

- https://github.com/p4tin/goaws
- https://github.com/vsouza/docker-SQS-local
- 
**Env Variables**  
- https://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html  

**Python Packages**    
- https://gist.github.com/gene1wood/4a052f39490fae00e0c3

### Slimming Down
The following zap plugins were removed to make things fit into a lambda

- accessControl
- diff
- gettingStarted
- help
- jxbrowsermacos
- jxbrowserwindows
- onlineMenu
- portscan
- quickstart
- reveal
- saverawmessage
- savexmlmessage
- sequence
- soap
- tips
- webdrivermacos
- webdriverwindows
- jxbrowser
- jxbrowserlinux64
- invoke

## Todo
- Move to using [serverless](https://serverless.com/) framework
- Have locks for targets to ensure not running concurrent scans
- Automate deployment to AWS
- Have a local test environment
- Use `zap_common.py` from main repo and replace changes with sed.
- Custom builds for baseline|browser|api focused scans
- Context handling
  - From s3 bucket or as event data
- Persist session in bucket or RDS?
- Option to have alerts sent to sns
- Option to dump results into bucket
- Emit events for stats
- Option for collecting http messages
- Stale job cleanup
- Break up active scans tests into separate handlers so a separate lambda is run for each active scan test
  - Event would trigger with target and test name
  - Event would also include additional authentication for setup
    - Cookie, custom headers, etc


## Scanning Persistence

### v1 - Storage via s3
```
/zap-scans/
  verified_domains # list of domains that have been verified
  verified_sites # list of sites that have been verified
  targets.json # list of target to scan, verified or not
  config.json # global configs of durations etc
  /_locks/
    https_example_com.lock
  /targets/
    ids.json # file that contains all uuids
    /https_example_com/
      schedule # text file for how often the site should be scanned
      config.json # for extra headers, alerts, duration, 
      is_verified # has verification method details
      /alerts/
        2019006345345558922206.json
        2019022117051550771586.json
    /http_site_com/
      config.json
      is_verified
  ...
```

### v2 - Storage via DynamoDB?


AmazonS3