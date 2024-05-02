# Riget Zoo Adventures - Booking Webapp

## Setup
This app is built using **Python 3.11.4**
Other versions may work, but you have been warned!

1) `py -m pip install -r requirements.txt`
2) `py -m flask --app webapp run` (optional parameter: `--debug` for debugging)

The webapp will run under `http://127.0.0.1:5000` by default

### Do note:
> Having the webapp run under debug mode means that the secret key will be '`DEBUGGING_KEY`'.

> This is bad for security, hence it is highly recommended that the app isn't run under debug in a production environment

## Admin Login
There is a standard admin login; change the password before deploying to production.

* Email: `email@example.com`
* Password: `Password1!`
