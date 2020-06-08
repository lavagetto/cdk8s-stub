# cdk8s-stub
A simple stub example of how a cdk8s-based abstraction could work for wikimedia.

You will find a single chart here called "blubberoid". It's not complete or even 100% correct,
but it's used to show how a reasonable abstraction could look like to the user when building new services.

What's missing right now is the ability to read configuration values from files (like helmfile does), plus other 
things like networkpolicies etc.

To generate the kubernetes yaml, install cdk8s and run `cdk8s synth`.