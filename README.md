# Sslify

## Purpose:

Automate the mid-TWU-term addition of SSL cert from LetsEncrypt to the nginx config on the server freewheelers.bike

## Setup & Usage:

```
pip install -r requirements.txt # install dependencies

cd aws_infrastructure/sslify

# USAGE: python sslify.py <term> <team> <env>
# This requests a letsencrypt cert for a particular environment
python sslify.py 54 5 qa
# Now everything should work; go to your environment and check!
 
# USAGE: python sslify.py <term> <team> <env> redirect_only
# This adds forced redirect for http to https
# This should be run AFTER the previous command or you will see redirects that go nowhere or go to error pages
python sslify.py 54 5 qa redirect_only
```

## Development:
```
pytest # run tests
pytest --cov=sslify.py test_sslify.py --cov-report html && open htmlcov/index.html # view test coverage
pytest test_sslify.py::TestSslify::test_matches_env_CI # run only one test 
```

    
## TODO

- Rewrite in Java because that is what the rest of 