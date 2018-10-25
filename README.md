# zap-lambda
*Experimental*  
What if you could run ZAP in a lambda? That would be cool? This first POC spiders a site and spits out the URLs and alerts.

## Requirements
- bash
- docker
- AWS
  - `aws` cli

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
- Automate deployment to AWS
- Have a local test environment
- Custom builds for baseline|browser|api focused scans
- Context handling
  - From s3 bucket or as event data
- Persist session in bucket or RDS?
- Option to have alerts sent to sns
- Option to dump results into bucket
- Break up active scans tests into separate handlers so a separate lambda is run for each active scan test
  - Event would trigger with target and test name
  - Event would also include additional authentication for setup
    - Cookie, custom headers, etc