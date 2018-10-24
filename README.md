# zap-lambda
*Experimental*  
What if you could run ZAP in a lambda? That would be cool? This first POC spiders a site and spits out the URLs and alerts.

## Requirements
- docker
- python
- AWS

## Try it out
- Create the package, run `./build.sh`
- Upload to a new/existing s3 bucket
- Create a lambda 
  - Author from scratch
  - Name `zap-lambda-poc`
  - Runtime `Python 2.7`
  - Create function
  - Set code entry type to the address of the s3 bucket the artifacts lives
  - For handler specify `zap_lambda.handler`
  - Save
  - Test
    - `{"target":"https://example.com"}`

## AWS
AWS limits total package size of 250mb, so I had to put ZAP on a diet to fit under that limit.

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