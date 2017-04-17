# Sslify

## Purpose:

Automate the mid-TWU-term addition of SSL cert from LetsEncrypt to the nginx config on the server freewheelers.bike

## Setup & Usage:

```
pip install -r requirements.txt # install dependencies

cd aws_infrastructure/sslify

# USAGE: python sslify.py <term> <team> <env>
python sslify.py 54 5 qa

# Now everything should work; go to your environment and check!
 
# Note: this does NOT implement force auto-redirect to ssl
```

## Development:
```
pytest # run tests
pytest --cov=sslify.py test_sslify.py --cov-report html && open htmlcov/index.html # view test coverage
pytest test_sslify.py::TestSslify::test_matches_env_CI # run only one test 
```

    
## TODO

- This code base needs a lot of refactoring and unit testing.  
- Implement force auto-redirect to ssl